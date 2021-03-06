import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
import json
import logging
from os.path import exists, basename, abspath, join
from time import sleep

import multiprocessing

log = multiprocessing.get_logger()

logging.getLogger('urllib3').setLevel(logging.WARN)

GOOGLE_DRIVE_SCOPE = 'https://www.googleapis.com/auth/drive.file'


class GDriveStorage(object):
    folder_lock = multiprocessing.Lock()

    def __init__(self, gauth, config):
        """
        Represents a folder on GDrive. Only folders off the root are supported.

        The app is restricted to only files and folders that it creates, so it is important that the same credentials
        be used to initialize the app.

        :param gauth: an initialized :class:`GDriveAuth` object.
        :param config: global config
        """

        self.config = config
        self.gconfig = config['gdrive']

        self.gauth = gauth

        self.headers = {
            'Authorization': 'Bearer {}'.format(self.gauth.access_token)
        }

        self.credentiall_folder = self.config.get('credential_folder')

        self.folder_name = self.gconfig.get('folder_name', None)
        self.client_id = self.gconfig.get('client_id', None)
        self.client_secret = self.gconfig.get('client_secret', None)

    @property
    def folder_id(self):
        return self.main_folder(create=False)

    def check(self):

        ret = True

        if self.credential_folder is None:
            log.error('credential_folder must be set.')
            ret = False

        if self.folder_name is None:
            log.error('folder_name must be set')
            ret = False

        if self.client_id is None:
            log.error('GDrive requires client_id')
            ret = False

        if self.client_secret is None:
            log.error('GDrive requires client_secret')
            ret = False

        log.info('Searching for main folder {} on GDrive'.format(folder_name))

        if self.main_folder(create=False) is None:
            log.error('Failed to find google folder.')
            ret = False

        return ret

    def configure(self):
        gconfig = self.config['gdrive']

        folder_name = gconfig['folder_name']

        log.info('Searching for main folder {} on GDrive'.format(folder_name))

        if self.main_folder(create=True) is None:
            log.error('Failed to create google folder.')
            return False

        return True

    def main_folder(self, create=False):
        """
        Sets `self.folder_id`

        :param create: Create the folder if it doesn't exist.
        :return: the id on success, None on fail.
        """
        # if we can't find it later, then it no longer exists.

        GDriveStorage.folder_lock.acquire()

        try:
            name = self.folder_name
            parent_id = 'root'

            retval = GDriveStorage.find_folders(self.gauth, parent_id, name)

            if retval is None:
                log.error('Cannot find main folder.')
                return None

            files = retval.get('files', [])

            assert len(files) <= 1, 'More than one folder named {}'.format(name)
            if len(files) > 1:
                log.error('More than one folder named {}'.format(name))
                return None

            elif len(files) < 1:
                if create:
                    log.warning('Main folder {} does not exist. Creating.'.format(name))

                    folder_id = GDriveStorage.create_folder(self.gauth, name, parent_id='root')
                    return folder_id
                else:
                    log.error('main folder not found')
                    return None

        finally:
            GDriveStorage.folder_lock.release()

    def subfolder(self, folder_name):
        """
        Finds or creates a subfolder off of the main folder.

        :param folder_name:
        :return: the ID of the folder
        """

        assert self.folder_id is not None, 'folder id is None'

        GDriveStorage.folder_lock.acquire()

        try:
            folders = GDriveStorage.find_folders(self.gauth, self.folder_id, folder_name)
            files = folders.get('files', [])

            fid = None

            if len(files) == 0:
                log.warning('Creating subfolder {}'.format(folder_name))
                fid = GDriveStorage.create_folder(self.gauth, folder_name, self.folder_id)
                sleep(.5)
            elif len(files) == 1:
                fid = files[0]['id']
            else:
                log.error('Found {} subfolders with name {}'.format(len(files), folder_name))

        finally:
            GDriveStorage.folder_lock.release()

        return fid

    @staticmethod
    def save(filename, metadata, headers):
        url = 'https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart'

        with open(filename, 'rb') as ifile:
            fdata = ifile.read()

            files = {
                'data': ('metadata', json.dumps(metadata), 'application/json; charset=UTF-8'),
                'file': (filename, fdata, 'image/jpeg')
            }

            menc = MultipartEncoder(
                fields=files)

            headers.update({'Content-Type': 'multipart/related; boundary={}'.format(menc.boundary_value)})

            upload_res = requests.post(url, data=menc, headers=headers)

            if upload_res.ok:
                log.debug('Upload responded ok: {}'.format(upload_res.status_code))
                return True
            else:
                log.error('Error ({})_uploading {}'.format(upload_res.status_code, filename))
                content = upload_res.json()
                log.error(content['error']['message'])
                return False

    def upload_file(self, img_capture):
        assert self.folder_id is not None, 'GDrive folder is not found'

        filename = img_capture.full_fname
        subdir = img_capture.subdir

        log.debug('Uploading {}'.format(filename))

        parent_id = None
        parent = GDriveStorage.find_folders(self.gauth, parent_id=self.folder_id, folder_name=subdir)

        if len(parent['files']) == 0:
            ret = self.subfolder(subdir)
            assert ret is not None
            parent_id = ret
        else:
            parent_id = parent['files'][0]['id']

        assert parent_id is not None, 'Parent id is None'

        metadata = {
            'name': basename(filename),
            'title': basename(filename),
            'parents': [parent_id]
        }

        retry = 0

        while retry < 1:

            if GDriveStorage.save(filename, metadata, dict(self.headers)):
                break
            retry += 1

        log.info('Upload {} complete'.format(filename))

        return True

    @staticmethod
    def find_folders(gauth, parent_id, folder_name):

        headers = {
            'Authorization': 'Bearer {}'.format(gauth.access_token),
            'Content-Type': 'application/json'
        }

        url = 'https://www.googleapis.com/drive/v3/files'
        qry = "mimeType = 'application/vnd.google-apps.folder' " \
              "and '{}' in parents and trashed = false and name = '{}'".format(parent_id, folder_name)

        folder_res = requests.get(url, headers=headers, params={'q': qry})

        if folder_res.ok:
            return folder_res.json()
        else:
            content = folder_res.json()
            log.error('Find folder returned: {} {}'.format(
                folder_res.status_code, content['error']['message']))

            return None

    @staticmethod
    def create_folder(gauth, folder_name, parent_id='root'):

        headers = {
            'Authorization': 'Bearer {}'.format(gauth.access_token),
            'Content-Type': 'application/json'
        }

        data = {
            'mimeType': 'application/vnd.google-apps.folder',
            'name': folder_name,
            'parents': [parent_id]
        }

        url = 'https://www.googleapis.com/drive/v3/files'

        create_res = requests.post(url, headers=headers, data=json.dumps(data))
        create_res.raise_for_status()

        retval = create_res.json()

        return retval['id']

    @staticmethod
    def delete_folder(gauth, folder_id):

        headers = {
            'Authorization': 'Bearer {}'.format(gauth.access_token)
        }

        url = 'https://www.googleapis.com/drive/v3/files/{}'.format(folder_id)
        delete_res = requests.delete(url, headers=headers)
        delete_res.raise_for_status()

        return True


class GDriveAuth(object):
    """
    Provider for uploading to Google Drive.

    Auth info is kept in a caller-specified JSON file with the following fields:
     - refresh_token
     - access_token
     - expires_in

    The easiest way to use it is to call the class method `py:func:get_access_token`. Note that this will prompt
    the user at the command line if the app hasn't been authorized yet.

    Expected usage:
     - create object
     - call :func:`init_auth`. If the app hasn't been validated, it will return False. Otherwise, use object `access_token`.
     - call :func:`init_token`. This starts the authorization flow. Returns fields to be displayed to the user.
     - call :func:`validate_token` in a loop, until `True` is returned.
     - Every so often, call :func:`refresh_token`. Calling :func:`init_auth` will work, too.

    Access can be revoked at https://myaccount.google.com/permissions?pli=1

    """

    def __init__(self, config):

        """
        Google-provided items, and a filename to store the cookie.

        :param config: global config dictionary
        """
        self.config = config
        self.gconfig = config['gdrive']

        creds_folder = abspath(self.config['credential_folder'])
        credential_filename = abspath(join(creds_folder, 'google_auth.json'))

        self.client_id = self.gconfig.get('client_id', None)
        self.client_secret = self.gconfig['client_secret']
        self.credential_filename = credential_filename
        self.access_token = None
        self.refresh_token = None
        self.token_expires = None

    def check(self):
        ret = True

        if self.credential_filename is None:
            log.error('credential_folder must be set.')
            ret = False

        if self.client_id is None:
            log.error('GDriveAuth requires client_id')
            ret = False

        if self.client_secret is None:
            log.error('GDriveAuth requires client_secret')
            ret = False

        if not exists(self.credential_filename):
            log.error('Credential file does not exist: {}'.format(self.credential_filename))
            ret = False

        return ret

    def configure(self):

        if self.init_auth():
            return True

        log.warning('Auth failed, attempting initial validation')
        url, ucode, dcode = self.init_token()

        while True:
            print('please visit {} and input this code: {}'.format(url, ucode))
            input('Press Enter key when ready...')

            validate_ret = self.validate_token(dcode)

            if validate_ret is None:
                log.info('Validation incomplete. Retrying.')
                sleep(1)
                continue

            if validate_ret is False:
                log.critical('validation failed')
                return None

            if validate_ret is True:
                log.info('Application validated')
                return True

    def init_auth(self):
        """
        Loads auth from file, and tries to connect. If the initial attempt fails, then it will try to refresh the token.

        :return: True if we have a valid auth_token
        """
        if exists(self.credential_filename):
            self.load_auth()
        else:
            log.error('{} does not exist'.format(self.credential_filename))
            return False

        if self.try_auth():
            log.info('Authentication success')
            return True

        log.warning('access_token is invalid, attempting refresh')
        return self.refresh_auth_token()

    def load_auth(self):

        """
        Refreshes object properties with current token values.

        :return:
        """

        assert exists(self.credential_filename)

        with open(self.credential_filename, 'r') as f:
            creds = json.load(f)

            self.access_token = creds['access_token']
            self.refresh_token = creds['refresh_token']
            self.token_expires = creds['expires_in']

    def save_auth(self):
        """
        Saves token info.

        :return: None
        """
        log.debug('Saving auth parameters')
        with open(self.credential_filename, 'w') as f:
            json.dump({
                'access_token': self.access_token,
                'expires_in': self.token_expires,
                'refresh_token': self.refresh_token
            }, f)

        log.info('Auth parameters saved to {}'.format(self.credential_filename))

    def try_auth(self):
        """
        Tries to get a list of files from the root. It doesn't matter if there are any.

        :return: True if authenticated.
        """

        assert self.access_token is not None, 'Access token is not set'
        qry = '\'root\' in parents'

        url = 'https://www.googleapis.com/drive/v3/files'

        headers = {
            'Authorization': 'Bearer {}'.format(self.access_token)
        }
        chk_result = requests.get(url, headers=headers, params={'q': qry})
        if chk_result.status_code != 200:
            log.warning('Auth check failed with status {}'.format(chk_result.status_code))
            return False

        log.debug('Auth check passed')

        return True

    def refresh_auth_token(self):
        """
        Attempts to refresh existing token. If successful, updates the file.

        :return: True on success.
        """

        assert self.refresh_token is not None, 'refresh_token must be set'

        log.info('Attempting token refresh')

        url = 'https://www.googleapis.com/oauth2/v4/token'
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        postdata = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token
        }
        refresh_response = requests.post(url, headers=headers, data=postdata)

        if refresh_response.status_code == 200:
            resdata = refresh_response.json()
            self.access_token = resdata['access_token']
            self.token_expires = resdata['expires_in']

            self.save_auth()

            log.info('Token refreshed')
            return True

        log.warning('Token refresh failed')
        return False

    def init_token(self):
        """
        Begin the validation flow for user confirmation and permission. Used for "new" installations.
        The user should be prompted with the returned values so they can go to Google and allow this app
        to access their Google Drive files and folders.

        :return: tuple with `verification_url`, `user_code`, and `device_code`
        """

        log.debug('Getting validation code')

        auth_init = requests.post('https://accounts.google.com/o/oauth2/device/code',
                                  data={'client_id': self.client_id, 'scope': GOOGLE_DRIVE_SCOPE})

        # there's no reason this shouldn't come back 200 that we can deal with
        auth_init.raise_for_status()

        log.debug('Validation code received')
        verify_init = auth_init.json()

        log.debug('Verification url: {}'.format(verify_init['verification_url']))
        log.debug('User code: {}'.format(verify_init['user_code']))

        return verify_init['verification_url'], verify_init['user_code'], verify_init['device_code']

    def validate_token(self, device_code):
        """
        The second stage of the validation flow. Checks if the validation code has been entered by the user at Google.
        Saves to `self.credential_file` if it is. Retries should be handled by the caller.

        :param device_code: returned from :func:`init_token`.
        :return: True on success, None if waiting, and False on error.
        """

        log.debug('Trying token endpoint')

        # leave the URLs hardcoded. If they change, there will (likely) be a lot of changes.
        access_check = requests.post('https://www.googleapis.com/oauth2/v4/token', data={
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': device_code,
            'grant_type': 'http://oauth.net/grant_type/device/1.0'
        })

        if access_check.status_code == 200:
            log.info('Received token')
            validation_response = access_check.json()
            self.access_token = validation_response['access_token']
            self.token_expires = validation_response['expires_in']
            self.refresh_token = validation_response['refresh_token']
            self.save_auth()

            return True

        elif access_check.status_code == 400 or access_check.status_code == 428:
            log.debug('Waiting on authorization')
            return None

        elif access_check.status_code == 429:
            log.warning('Rate limit exceeded. Sleeping for 5 seconds.')
            sleep(5)

        else:
            log.warning('Unknown response')

        return False

    @classmethod
    def init_gauth(cls, client_id, client_secret, filename):
        """
        Helper for getting an initialized object. This will prompt the user at the command line with validation code
        if one has not been set.

        :param client_id:
        :param client_secret:
        :param filename: the filename for the saved tokens. Used by :func:__init__
        :return: None on failure, initialized :class:`GDriveAuth` object
        """

        gauth = cls(client_id, client_secret, filename)

        if gauth.init_auth():
            return gauth

        log.warning('Auth failed, attempting initial validation')
        url, ucode, dcode = gauth.init_token()

        while True:
            print('please visit {} and input this code: {}'.format(url, ucode))
            input('Press Enter key when ready...')

            validate_ret = gauth.validate_token(dcode)

            if validate_ret is None:
                log.info('Validation incomplete. Retrying.')
                sleep(1)
                continue

            if validate_ret is False:
                log.critical('validation failed')
                return None

            if validate_ret is True:
                log.info('Application validated')
                return gauth
