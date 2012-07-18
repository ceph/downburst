#!/usr/bin/python
from setuptools import setup, find_packages
import os
import sys

def read(fname):
    path = os.path.join(os.path.dirname(__file__), fname)
    f = open(path)
    return f.read()

install_requires = []
pyversion = sys.version_info[:2]
if pyversion < (2, 7) or (3, 0) <= pyversion <= (3, 1):
    install_requires.append('argparse')

setup(
    name='downburst',
    version='0.0.1',
    packages=find_packages(),

    author='Tommi Virtanen',
    author_email='tommi.virtanen@inktank.com',
    description='Run Ubuntu 12.04 Cloud images on libvirt virtual machines',
    long_description=read('README.rst'),
    license='MIT',
    keywords='libvirt virtualization',
    url="https://github.com/ceph/downburst",

    install_requires=[
        'setuptools',
        'requests',
        'lxml',
        'PyYaml',
        ] + install_requires,

    tests_require=[
        'pytest >=2.1.3',
        ],

    entry_points={

        'console_scripts': [
            'downburst = downburst.cli:main',
            ],

        'downburst.cli': [
            'create = downburst.create:make',
            'gen-ssh-key = downburst.gen_ssh_key:make',
            ],

        },
    )
