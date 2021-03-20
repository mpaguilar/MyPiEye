from setuptools import setup, find_packages

import MyPiEye

setup(
    name="MyPiEye",
    version="0.2.5",
    author="Michael P. Aguilar",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'mypieye = MyPiEye.cmdline:mypieye'
        ]
    },
    package_data={
        '': ['*.ini']
    },

    install_requires=[
        'aiohttp==3.4.4',
        'alabaster==0.7.12',
        'amqp==2.5.1',
        'apiclient==1.0.3',
        'asn1crypto==0.24.0',
        'async-timeout==3.0.1',
        'attrs==18.2.0',
        'azure-common==1.1.23',
        'azure-storage-blob==2.1.0',
        'azure-storage-common==2.1.0',
        'Babel==2.6.0',
        'billiard==3.6.1.0',
        'boto3==1.9.30',
        'botocore==1.12.50',
        'cachetools==2.1.0',
        'celery==4.3.0',
        'certifi==2018.8.24',
        'cffi==1.12.3',
        'chardet==3.0.4',
        'Click==7.0',
        'colorama==0.3.9',
        'cryptography==2.7',
        'dnspython==1.16.0',
        'docutils==0.14',
        'eventlet==0.25.1',
        'Flask==1.0.2',
        'gevent==1.4.0',
        'greenlet==0.4.15',
        'gunicorn==19.9.0',
        'httplib2==0.11.3',
        'idna==2.7',
        'imagesize==1.1.0',
        'importlib-metadata==0.20',
        'itsdangerous==1.1.0',
        'Jinja2==2.11.3',
        'jmespath==0.9.3',
        'kombu==4.6.4',
        'MarkupSafe==1.1.0',
        'minio==4.0.10',
        'monotonic==1.5',
        'more-itertools==7.2.0',
        'multidict==4.5.1',
        'numpy==1.15.2',
        'opencv-python==3.4.3.18',
        'opencv-python-headless==3.4.4.19',
        'packaging==18.0',
        'pyasn1==0.4.4',
        'pyasn1-modules==0.2.2',
        'pycparser==2.19',
        'Pygments==2.2.0',
        'pyparsing==2.3.0',
        'python-dateutil==2.7.5',
        'pytz==2018.7',
        'redis==3.3.8',
        'requests==2.20.0',
        'requests-toolbelt==0.8.0',
        'rsa==4.0',
        's3transfer==0.1.13',
        'six==1.11.0',
        'snowballstemmer==1.2.1',
        'Sphinx==1.8.1',
        'sphinx-rtd-theme==0.4.2',
        'sphinxcontrib-websupport==1.1.0',
        'uritemplate==3.0.0',
        'urllib3==1.23',
        'vine==1.3.0',
        'Werkzeug==0.14.1',
        'yarl==1.2.6',
        'zipp==0.6.0'
    ]
)
