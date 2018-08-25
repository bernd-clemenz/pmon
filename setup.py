#
# Installation script for the simple http process monitor
# (c) ISC Clemenz & Weinbrecht GmbH 2018
#

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pmon",
    version="0.0.2",
    author="ISC Clemenz & Weinbrecht GmbH",
    author_email="info@isc-software.de",
    description="A very simple HTTP process monitor",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bernd-clemenz/pmon",
    packages=setuptools.find_packages(),
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
    install_requires=(
        "argparse",
        "requests",
        "paramiko"
    ),
)