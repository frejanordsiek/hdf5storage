# Copyright (c) 2013-2016, Freja Nordsiek
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
import tempfile

import numpy as np
import h5py

import hdf5storage


# A series of tests to make sure that structured ndarrays with a field
# that has an object dtype are written like structs (are HDF5 Groups)
# but are written as an HDF5 COMPOUND Dataset otherwise (even in the
# case that a field's name is 'O').


def test_O_field_compound():
    name = '/a'
    data = np.empty(shape=(1, ), dtype=[('O', 'int8'), ('a', 'uint16')])
    with tempfile.TemporaryDirectory() as folder:
        filename = os.path.join(folder, 'data.h5')
        hdf5storage.write(data, path=name, filename=filename,
                          matlab_compatible=False,
                          structured_numpy_ndarray_as_struct=False)
        with h5py.File(filename, mode='r') as f:
            assert isinstance(f[name], h5py.Dataset)


def test_object_field_group():
    name = '/a'
    data = np.empty(shape=(1, ), dtype=[('a', 'O'), ('b', 'uint16')])
    data['a'][0] = [1, 2]
    with tempfile.TemporaryDirectory() as folder:
        filename = os.path.join(folder, 'data.h5')
        hdf5storage.write(data, path=name, filename=filename,
                          matlab_compatible=False,
                          structured_numpy_ndarray_as_struct=False)
        with h5py.File(filename, mode='r') as f:
            assert isinstance(f[name], h5py.Group)


def test_O_and_object_field_group():
    name = '/a'
    data = np.empty(shape=(1, ), dtype=[('a', 'O'), ('O', 'uint16')])
    data['a'][0] = [1, 2]
    with tempfile.TemporaryDirectory() as folder:
        filename = os.path.join(folder, 'data.h5')
        hdf5storage.write(data, path=name, filename=filename,
                          matlab_compatible=False,
                          structured_numpy_ndarray_as_struct=False)
        with h5py.File(filename, mode='r') as f:
            assert isinstance(f[name], h5py.Group)
