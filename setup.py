#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.md') as readme_file:
    readme = readme_file.read()

with open('CHANGELOG.md') as history_file:
    history = history_file.read()

requirements = [
    # py2/3 compat dependencies
    'six',
    'enum34',
    # all other modules
    'requests'
]

setup_requirements = [
    'pytest-runner',
]

test_requirements = [
    'pytest',
    'hypothesis',
    'requests-mock'
]

setup(
    name='signal_analog',
    version='0.4.0',
    description="Troposphere-like library for building and composing SignalFx SignalFlow programs.",
    long_description=readme + '\n\n' + history,
    author="Fernando Freire",
    author_email='***REMOVED***',
    url='https://bitbucket.nike.com/projects/NIK/repos/signal_analog',
    packages=find_packages(include=['signal_analog']),
    include_package_data=True,
    install_requires=requirements,
    zip_safe=False,
    keywords='signal_analog',
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    test_suite='tests',
    tests_require=test_requirements,
    setup_requires=setup_requirements,
)
