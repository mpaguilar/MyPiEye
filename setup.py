from setuptools import setup, find_packages

import MyPiEye

setup(
    name="MyPiEye",
    version="0.1",
    author="Michael P. Aguilar",
    packages=find_packages('MyPiEye'),
    entry_points={
        'console_scripts': [
            'mypieye = MyPiEye.__main__'
        ]
    },

    package_dir={
        '': 'MyPiEye'
    },

    package_data={
        '': ['*.ini']
    },

    install_requires=[
        'apiclient==1.0.3',
        'cachetools==2.1.0',
        'certifi==2018.8.24',
        'chardet==3.0.4',
        'Click==7.0',
        'colorama==0.3.9',
        'httplib2==0.11.3',
        'idna==2.7',
        'numpy==1.15.2',
        'pyasn1==0.4.4',
        'pyasn1-modules==0.2.2',
        'requests==2.19.1',
        'rsa==4.0',
        'six==1.11.0',
        'uritemplate==3.0.0',
        'urllib3==1.23',
        'opencv-python==3.4.3.18'
    ]
)
