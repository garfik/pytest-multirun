# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

setup(
    name='pytest_multirun',
    description='pytest plugin to run your tests in parallel mode',
    version=0.11,
    author='Dmitrii Kulikov',
    author_email='garf.freeman@gmail.com',
    url='https://github.com/garfik/pytest-multirun',
    platforms=['linux', 'osx', 'win32'],
    packages=['pytest_multirun'],
    entry_points={
        'pytest11': [
            'multirun = pytest_multirun.plugin'
        ]
    },
    install_requires=['pytest==2.7.3', 'pytest-pycharm'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: MacOS :: MacOS X',
        'Topic :: Software Development :: Testing',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: Utilities',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: Implementation :: PyPy',
    ]
)
