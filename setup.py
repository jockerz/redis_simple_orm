#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re

from setuptools import find_packages, setup


def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    with open(os.path.join(package, "__init__.py")) as f:
        return re.search("__version__ = ['\"]([^'\"]+)['\"]", f.read()).group(1)


def get_long_description():
    """
    Return the README.
    """
    with open("README.md", encoding="utf8") as f:
        return f.read()


def get_packages(package):
    """
    Return root package and all sub-packages.
    """
    return [
        dirpath
        for dirpath, dirnames, filenames in os.walk(package)
        if os.path.exists(os.path.join(dirpath, "__init__.py"))
    ]


setup(
    name="redis_simple_orm",
    version=get_version("RSO"),
    python_requires='>=3.6',
    url="https://github.com/jockerz/redis_simple_orm",
    license="MIT",
    description="Simple Redis ORM (Sync and Async).",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="Jockerz",
    author_email="jockerz@protonmail.com",
    packages=find_packages(
        exclude=['tests', "*.tests", "*.tests.*", "tests.*"]
    ),
    include_package_data=True,
    data_files=[("", ["LICENSE"])],
    install_requires=[
        'aiocontextvars;python_version<"3.7"',
    ],
    extras_require={
        "redis-py": ["redis"],
        "aioredis": ["aioredis"],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
)
