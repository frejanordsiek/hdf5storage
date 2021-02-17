# Copyright (c) 2013-2021, Freja Nordsiek
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
# 1. Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import sys
from setuptools import setup

if sys.hexversion < 0x3050000:
    raise NotImplementedError('Python < 3.5 not supported.')

with open('README.rst') as file:
    long_description = file.read()

setup(name='hdf5storage',
      version='0.2',
      description='Utilities to read/write Python types to/from HDF5 files, including MATLAB v7.3 MAT files.',
      long_description=long_description,
      author='Freja Nordsiek',
      author_email='fnordsie@posteo.net',
      url='https://github.com/frejanordsiek/hdf5storage',
      packages=['hdf5storage'],
      install_requires=["setuptools", "numpy", "h5py>=2.3"],
      tests_require=['nose>=1.0'],
      test_suite='nose.collector',
      license='BSD',
      keywords='hdf5 matlab',
      zip_safe=True,
      classifiers=[
          "Programming Language :: Python :: 3 :: Only",
          "Development Status :: 3 - Alpha",
          "License :: OSI Approved :: BSD License",
          "Operating System :: OS Independent",
          "Intended Audience :: Developers",
          "Intended Audience :: Information Technology",
          "Intended Audience :: Science/Research",
          "Topic :: Scientific/Engineering",
          "Topic :: Database",
          "Topic :: Software Development :: Libraries :: Python Modules"
          ]
      )
