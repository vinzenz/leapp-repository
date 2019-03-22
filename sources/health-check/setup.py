from setuptools import find_packages, setup
from distutils.util import convert_path

main_ns = {}
ver_path = convert_path('healthcheck/__init__.py')
with open(ver_path) as ver_file:
    exec(ver_file.read(), main_ns)

EXCLUSION = []

setup(
    name='healthcheck',
    version=main_ns['VERSION'],
    packages=find_packages(exclude=EXCLUSION),
    install_requires=['six'],
    entry_points='''
        [console_scripts]
        healthcheck=healthcheck:main
    '''
)
