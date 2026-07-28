#!/usr/bin/env python3
"""Setup configuration for Martian."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="martian",
    version="1.0.0",
    author="David",
    description="RGB controller for Mars Gaming MK-Revo Pro keyboard on Linux",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/elarreglador/martian",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: POSIX :: Linux",
        "Environment :: X11 Applications",
        "Topic :: System :: Hardware",
        "Intended Audience :: End Users/Desktop",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pillow>=10.0.0",
        "pystray>=0.19.0",
    ],
    entry_points={
        "console_scripts": [
            "martian=martian.ui.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "martian": ["modes/*.txt"],
    },
)
