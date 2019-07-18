import runpy
from os.path import splitext, basename, join, abspath, dirname

from setuptools import setup, find_packages, findall, find_namespace_packages
from setuptools.glob import glob

here = abspath(dirname(__file__))


def get_version():
    file_globals = runpy.run_path("pytw/version.py")
    return file_globals['__version__']


def read(*parts):
    with open(join(here, *parts), 'r') as f:
        return f.read()


LONG_DESCRIPTION = read('README.md')
REQUIREMENTS = read('requirements.txt')

setup(
    name='pytw',
    version=get_version(),
    description='A text-based space trading game',
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    author='Don Brown',
    author_email='mrdon@twdata.org',
    url='https://bitbucket.org/mrdon/pytw',
    license='aplv2',
    install_requires=REQUIREMENTS,
    packages=find_namespace_packages(include=['pytw.*']),
    include_package_data=True,
    entry_points="""
        [console_scripts]
        pytw-client = pytw.client_app:main
        pytw-server = pytw.server_app:main
    """,
    python_requires='>=3.7',
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3 :: Only",
    ],
)
