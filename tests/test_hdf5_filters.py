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

import os.path
import random
import tempfile

import h5py

import pytest

import hdf5storage

from asserts import assert_equal
from make_randoms import random_numpy, random_numpy_shape, \
    max_array_axis_length, dtypes, random_name

random.seed()


@pytest.mark.parametrize(
    'compression,shuffle,fletcher32,gzip_level',
    [(compression, shuffle, fletcher32, level)
     for compression in ('gzip', 'lzf')
     for shuffle in (True, False)
     for fletcher32 in (True, False)
     for level in range(10)])
def test_read_filtered_data(compression, shuffle, fletcher32,
                            gzip_level):
    # Make the filters dict.
    filts = {'compression': compression,
             'shuffle': shuffle,
             'fletcher32': fletcher32}
    if compression == 'gzip':
        filts['compression_opts'] = gzip_level

    # Make some random data.
    dims = random.randint(1, 4)
    data = random_numpy(shape=random_numpy_shape(dims,
                        max_array_axis_length),
                        dtype=random.choice(tuple(
                        set(dtypes) - set(['U']))))
    # Make a random name.
    name = random_name()

    # Write the data to the file with the given name with the provided
    # filters and read it back.
    with tempfile.TemporaryDirectory() as folder:
        filename = os.path.join(folder, 'data.h5')
        with h5py.File(filename, mode='w') as f:
            f.create_dataset(name, data=data, chunks=True, **filts)
        out = hdf5storage.read(path=name, filename=filename,
                               matlab_compatible=False)

    # Compare
    assert_equal(out, data)


@pytest.mark.parametrize(
    'compression,shuffle,fletcher32,gzip_level',
    [(compression, shuffle, fletcher32, level)
     for compression in ('gzip', 'lzf')
     for shuffle in (True, False)
     for fletcher32 in (True, False)
     for level in range(10)])
def test_write_filtered_data(compression, shuffle, fletcher32,
                             gzip_level):

    # Make some random data. The dtype must be restricted so that it can
    # be read back reliably.
    dims = random.randint(1, 4)
    dts = tuple(set(dtypes) - set(['U', 'S', 'bool', 'complex64', \
        'complex128']))

    data = random_numpy(shape=random_numpy_shape(dims,
                        max_array_axis_length),
                        dtype=random.choice(dts))
    # Make a random name.
    name = random_name()

    # Write the data to the file with the given name with the provided
    # filters and read it back.
    with tempfile.TemporaryDirectory() as folder:
        filename = os.path.join(folder, 'data.h5')
        hdf5storage.write(data, path=name, filename=filename,
                          store_python_metadata=False,
                          matlab_compatible=False,
                          compress=True, compress_size_threshold=0,
                          compression_algorithm=compression,
                          gzip_compression_level=gzip_level,
                          shuffle_filter=shuffle,
                          compressed_fletcher32_filter=fletcher32)

        with h5py.File(filename, mode='r') as f:
            d = f[name]
            filts = {'fletcher32': d.fletcher32,
                     'shuffle': d.shuffle,
                     'compression': d.compression,
                     'gzip_level': d.compression_opts}
            out = d[...]

    # Check the filters
    assert fletcher32 == filts['fletcher32']
    assert shuffle == filts['shuffle']
    assert compression == filts['compression']
    if compression == 'gzip':
        assert gzip_level == filts['gzip_level']

    # Compare
    assert_equal(out, data)


@pytest.mark.parametrize(
    'method,uncompressed_fletcher32_filter,compression,shuffle,'
    'fletcher32,gzip_level',
    [(method, uf, compression, shuffle, fletcher32, level)
     for method in ('compression_disabled', 'data_too_small')
     for uf in (True, False)
     for compression in ('gzip', 'lzf')
     for shuffle in (True, False)
     for fletcher32 in (True, False)
     for level in range(10)])
def test_uncompressed_write_filtered_data(
        method, uncompressed_fletcher32_filter, compression, shuffle,
        fletcher32, gzip_level):
    # Make the filters dict.
    filts = {'compression': compression,
             'shuffle': shuffle,
             'fletcher32': fletcher32,
             'gzip_level': gzip_level}

    # Make some random data. The dtype must be restricted so that it can
    # be read back reliably.
    dims = random.randint(1, 4)
    dts = tuple(set(dtypes) - set(['U', 'S', 'bool', 'complex64', \
        'complex128']))

    data = random_numpy(shape=random_numpy_shape(dims,
                        max_array_axis_length),
                        dtype=random.choice(dts))
    # Make a random name.
    name = random_name()

    # Make the options to disable compression by the method specified,
    # which is either that it is outright disabled or that the data is
    # smaller than the compression threshold.
    if method == 'compression_disabled':
        opts = {'compress': False, 'compress_size_threshold': 0}
    else:
        opts = {'compress': True,
                'compress_size_threshold': data.nbytes + 1}

    # Write the data to the file with the given name with the provided
    # filters and read it back.
    with tempfile.TemporaryDirectory() as folder:
        filename = os.path.join(folder, 'data.h5')
        hdf5storage.write(data, path=name, filename=filename, \
            store_python_metadata=False, matlab_compatible=False, \
            compression_algorithm=filts['compression'], \
            gzip_compression_level=filts['gzip_level'], \
            shuffle_filter=filts['shuffle'], \
            compressed_fletcher32_filter=filts['fletcher32'], \
            uncompressed_fletcher32_filter= \
            uncompressed_fletcher32_filter, \
            **opts)

        with h5py.File(filename, mode='r') as f:
            d = f[name]
            fletcher32 = d.fletcher32
            shuffle = d.shuffle
            compression = d.compression
            gzip_level = d.compression_opts
            out = d[...]

    # Check the filters
    assert compression is None
    assert shuffle is False
    assert fletcher32 == uncompressed_fletcher32_filter

    # Compare
    assert_equal(out, data)
