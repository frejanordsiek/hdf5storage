# Copyright (c) 2021, Freja Nordsiek
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

import os.path
import random
import tempfile

import numpy
import h5py

import hdf5storage

import make_randoms


# A series of tests to make sure that empty arrays are stored properly
# in matlab compatible mode. Specifically, the shape must be stored in
# the Dataset in the same order as it is in or is to be in Python.

def test_write_empty():
    for _ in range(10):
        name = make_randoms.random_name()
        shape = list(make_randoms.random_numpy_shape(
            random.randrange(2, 10), 20))
        shape[random.randrange(len(shape))] = 0
        shape = tuple(shape)
        dtype = random.choice(make_randoms.dtypes)
        while dtype in ('S', 'U'):
            dtype = random.choice(make_randoms.dtypes)
        data = make_randoms.random_numpy(shape, dtype)
        with tempfile.TemporaryDirectory() as folder:
            filename = os.path.join(folder, 'data.h5')
            # Write
            hdf5storage.write(data, path=name, filename=filename,
                              matlab_compatible=True,
                              store_python_metadata=False)
            # Read to check.
            with h5py.File(filename, mode='r') as f:
                dset = f[name]
                assert isinstance(dset, h5py.Dataset)
                assert dset.dtype == numpy.dtype('uint64')
                assert tuple(dset[:]) == shape
                assert 'MATLAB_empty' in dset.attrs
                assert dset.attrs['MATLAB_empty'] == 1


def test_read_empty():
    for _ in range(10):
        name = make_randoms.random_name()
        shape = list(make_randoms.random_numpy_shape(
            random.randrange(2, 10), 20))
        shape[random.randrange(len(shape))] = 0
        shape = tuple(shape)
        dtype = random.choice(
            [prefix + 'int' + suffix
             for prefix in ('u', '')
             for suffix in ('8', '16', '32', '64')]
            + ['single', 'double'])
        with tempfile.TemporaryDirectory() as folder:
            filename = os.path.join(folder, 'data.h5')
            # Make the file and the data.
            with h5py.File(filename, mode='w') as f:
                dset = f.create_dataset(name,
                                        data=numpy.uint64(shape))
                dset.attrs.create('MATLAB_class', numpy.bytes_(dtype))
                dset.attrs.create('MATLAB_empty', numpy.uint8(1))
            # Read the data.
            data = hdf5storage.read(path=name, filename=filename)
            assert data.shape == shape
            assert data.dtype == numpy.dtype(dtype)
