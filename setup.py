from setuptools import setup, find_packages
setup(
    name="MyPiEye",
    version="0.1",
    packages=find_packages(),
    scripts=['MyPiEye/mypieye.py'],
    package_data={
        '': ['mypieye.ini']
    },
    entry_points={
        'console_scripts': [
            'mypieye = MyPiEye.mypieye:__main__'
        ]
    }
)
