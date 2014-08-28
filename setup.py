#!/usr/bin/python
from setuptools import setup, find_packages
import os
import re
import sys

module_file = open("downburst/__init__.py").read()
metadata = dict(re.findall(r"__([a-z]+)__\s*=\s*['\"]([^'\"]*)['\"]", module_file))
long_description = open('README.rst').read()

install_requires=[
    'setuptools',
    'libvirt-python',
    ]

install_requires.extend(
    [ln.strip() for ln in open('requirements-dev.txt').readlines() if ln]
)

pyversion = sys.version_info[:2]
if pyversion < (2, 7) or (3, 0) <= pyversion <= (3, 1):
    install_requires.append('argparse')

tests_require = [
    'pytest >= 2.1.3',
    'tox >= 1.2'
]

setup(
    name='downburst',
    version=metadata['version'],
    packages=find_packages(),
    author='Inktank Storage, Inc.',
    author_email='ceph-qa@ceph.com',
    description='Run Cloud images on libvirt virtual machines',
    long_description=long_description,
    license='MIT',
    keywords='libvirt virtualization',
    url="https://github.com/ceph/downburst",
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 2.7",
    ],

    install_requires=install_requires,
    tests_require=tests_require,

    entry_points={

        'console_scripts': [
            'downburst = downburst.cli:main',
            ],

        'downburst.cli': [
            'create = downburst.create:make',
            'destroy = downburst.destroy:make',
            'list = downburst.discover:make',
            'gen-ssh-key = downburst.gen_ssh_key:make',
            'list-json = downburst.discover:make_json',
            ],

        },
    )
