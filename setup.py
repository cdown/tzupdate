#!/usr/bin/env python

from setuptools import setup


with open('README.rst') as readme_f:
    README = readme_f.read()

with open('requirements.txt') as requirements_f:
    REQUIREMENTS = requirements_f.readlines()

with open('tests/requirements.txt') as test_requirements_f:
    TEST_REQUIREMENTS = test_requirements_f.readlines()

setup(
    name='tzupdate',
    version='0.5.0',
    description='Set the system timezone based on IP geolocation',
    long_description=README,
    url='https://github.com/cdown/tzupdate',
    license='ISC',

    author='Chris Down',
    author_email='chris@chrisdown.name',

    py_modules=['tzupdate'],
    install_requires=REQUIREMENTS,

    entry_points={
        'console_scripts': ['tzupdate=tzupdate:main'],
    },

    keywords='timezone localtime tz',

    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: ISC License (ISCL)",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Topic :: System",
        "Topic :: System :: Networking :: Time Synchronization",
        "Topic :: Utilities",
    ],

    test_suite='nose.collector',
    tests_require=TEST_REQUIREMENTS,
)
