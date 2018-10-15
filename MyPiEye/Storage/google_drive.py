import requests
import json
import logging
from time import sleep
from os.path import exists

log = logging.getLogger(__name__)

GOOGLE_DRIVE_SCOPE = 'https://www.googleapis.com/auth/drive.file'


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
     - call `py.func:init_auth`. If the app hasn't been validated, it will return False. Otherwise, use object `access_token`.
     - call `py:func:init_token`. This starts the authorization flow. Returns fields to be displayed to the user.
     - call `py:func:validate_token` in a loop, until `True` is returned.
     - Every so often, call `py:func:refresh_token`. Calling `init_auth` will work, too.

    Access can be revoked at https://myaccount.google.com/permissions?pli=1

    """

    def __init__(self, client_id, client_secret, credential_filename):

        assert isinstance(client_id, str)
        assert isinstance(client_secret, str)
        assert isinstance(credential_filename, str)

        self.client_id = client_id
        self.client_secret = client_secret
        self.credential_filename = credential_filename
        self.access_token = None
        self.refresh_token = None
        self.token_expires = None

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

        assert exists(self.credential_filename)

        with open(self.credential_filename, 'r') as f:
            creds = json.load(f)

            self.access_token = creds['access_token']
            self.refresh_token = creds['refresh_token']
            self.token_expires = creds['expires_in']

    def save_auth(self):
        """
        Saves token info
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

        :param device_code: returned from `py:func:init_token`.
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
    def get_access_token(cls, client_id, client_secret, filename):
        """
        Helper for getting a token. This will prompt the user at the command line with validation code
        if one has not been set.
        :param client_id:
        :param client_secret:
        :param filename:
        :return:
        """

        gauth = cls(client_id, client_secret, filename)

        if gauth.init_auth():
            return gauth.access_token

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
                return gauth.access_token
