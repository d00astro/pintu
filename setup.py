#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Setup of Pintu package

Todo:
    * Use config as much as possible

"""
__author__ = "Anders Åström"
__contact__ = "anders@astrom.sg"
__copyright__ = "2022, Anders Åström"
__licence__ = """The MIT License
Copyright © 2022 Anders Åström

Permission is hereby granted, free of charge, to any person obtaining a copy of this
 software and associated documentation files (the “Software”), to deal in the Software
 without restriction, including without limitation the rights to use, copy, modify,
 merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
 permit persons to whom the Software is furnished to do so, subject to the following
 conditions:

The above copyright notice and this permission notice shall be included in all copies
 or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
 INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
 PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
 HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
 CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
 OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import pathlib
from typing import List

import setuptools

here = pathlib.Path(__file__).parent.resolve()


def text(*names, encoding="utf8"):
    return here.joinpath(*names).read_text(encoding=encoding)


pi_model_file = pathlib.Path("/sys/firmware/devicetree/base/model")
pi_model = pi_model_file.read_text() if pi_model_file.is_file() else None

dependencies = [
    "ConfigArgParse",
    "fastapi",
    "gunicorn",
    "numpy",
    "packaging",
    "python-ulid",
    "redis",
    "requests",
    "uvicorn",
    "opencv-python",
    "ncnn",
]

# if pi_model:
#    dependencies.append("RPi.GPIO")


all_extras: List[str] = []

setuptools.setup(
    name="pintu",
    license="MIT License",
    description="Smart doorbell",
    long_description=text("README.md"),
    long_description_content_type="text/markdown",
    author="Anders Åström",
    author_email="anders@astrom.sg",
    url="https://github.com/d00astro/pintu",
    packages=setuptools.find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[  # https://pypi.org/classifiers/
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Development Status :: 3 - Alpha",
        "Topic :: Home Automation",
        "Topic :: Multimedia :: Video",
    ],
    install_requires=dependencies,
    extras_require={
        "all": all_extras,
    },
    entry_points={
        "console_scripts": ["redgrease=redgrease.cli:main [cli]"],
    },
    setup_requires=[],
    python_requires=">=3.6",
    keywords="home automation, raspberry pi, iot, video analytics",
)
