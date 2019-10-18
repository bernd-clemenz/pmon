#
# -*- coding: utf-8-*-
# Installation script for the simple http process monitor
# (c) ISC Clemenz & Weinbrecht GmbH 2018
#

import os

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

here = os.path.abspath(os.path.dirname(__file__))
about = {}
with open(os.path.join(here, 'pmon', '__version__.py'), 'r') as f:
    exec(f.read(), about)

setuptools.setup(
    name=about['__title__'],
    version=about['__version__'],
    author=about['__author__'],
    author_email=about['__author_email__'],
    description=about['__description__'],
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=about['__url__'],
    packages=setuptools.find_packages(),
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
    install_requires=(
        "argparse",
        "keyring",
        "requests",
        "paramiko",
        "cherrypy",
        "pyzmq"
    )
)