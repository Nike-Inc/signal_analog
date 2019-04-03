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
    'enum34',
    'six',
    # all other modules
    'requests',
    'click',
    'email_validator',
    'pyyaml',
    'markdown',
    'deprecation'
]

setup_requirements = [
    'bumpversion',
    'pytest-runner'
]

test_requirements = [
    'betamax',
    'betamax_serializers',
    'coverage',
    'hypothesis',
    'pytest',
    'pytest-html',
    'pytest-xdist',
    'requests-mock',
    'tox'
]

setup(
    name='signal_analog',
    version='2.7.0',
    description='A troposphere-like library for managing SignalFx'
                + 'Charts, Dashboards, and Detectors.',
    long_description=readme + '\n\n' + history,
    long_description_content_type="text/markdown",
    author="Fernando Freire",
    author_email='fernando.freire@nike.com',
    url='https://github.com/Nike-inc/signal_analog',
    packages=find_packages(include=['signal_analog']),
    include_package_data=True,
    install_requires=requirements,
    zip_safe=False,
    keywords='signal_analog signalfx dashboards charts detectors monitoring '
             + 'signalflow',
    license='BSD 3-Clause License',
    classifiers=[
        "Programming Language :: Python :: 2",
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Libraries',
        'Topic :: Utilities'
    ],
    test_suite='tests',
    tests_require=test_requirements,
    setup_requires=setup_requirements,
)
