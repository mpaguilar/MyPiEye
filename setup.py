from setuptools import setup, find_packages
setup(
    name="PiEye",
    version="0.1",
    packages=find_packages(),
    scripts=['pieye.py'],
    package_data={
        '': ['pieye.ini']
    }
)
