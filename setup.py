from setuptools import setup, find_packages
setup(
    name="MyPiEye",
    version="0.1",
    packages=find_packages(),
    scripts=['mypieye.py'],
    package_data={
        '': ['mypieye.ini']
    }
)
