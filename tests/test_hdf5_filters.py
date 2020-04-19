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

import os
import os.path
import random

import h5py

import hdf5storage

from nose.tools import raises

from asserts import *
from make_randoms import *

random.seed()


filename = 'data.mat'


def check_read_filters(filters):
    # Read out the filter arguments.
    filts = {'compression': 'gzip',
             'shuffle': True,
             'fletcher32': True,
             'gzip_level': 7}
    for k, v in filters.items():
        filts[k] = v
    if filts['compression'] == 'gzip':
        filts['compression_opts'] = filts['gzip_level']
    del filts['gzip_level']
    
    # Make some random data.
    dims = random.randint(1, 4)
    data = random_numpy(shape=random_numpy_shape(dims,
                        max_array_axis_length),
                        dtype=random.choice(tuple(
                        set(dtypes) - set(['U']))))
    # Make a random name.
    name = random_name()

    # Write the data to the proper file with the given name with the
    # provided filters and read it backt. The file needs to be deleted
    # before and after to keep junk from building up.
    if os.path.exists(filename):
        os.remove(filename)
    try:
        with h5py.File(filename, mode='w') as f:
            f.create_dataset(name, data=data, chunks=True, **filts)
        out = hdf5storage.read(path=name, filename=filename,
                               matlab_compatible=False)
    except:
        raise
    finally:
        if os.path.exists(filename):
            os.remove(filename)

    # Compare
    assert_equal(out, data)


def check_write_filters(filters):
    # Read out the filter arguments.
    filts = {'compression': 'gzip',
             'shuffle': True,
             'fletcher32': True,
             'gzip_level': 7}
    for k, v in filters.items():
        filts[k] = v

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

    # Write the data to the proper file with the given name with the
    # provided filters and read it backt. The file needs to be deleted
    # before and after to keep junk from building up.
    if os.path.exists(filename):
        os.remove(filename)
    try:
        hdf5storage.write(data, path=name, filename=filename, \
            store_python_metadata=False, matlab_compatible=False, \
            compress=True, compress_size_threshold=0, \
            compression_algorithm=filts['compression'], \
            gzip_compression_level=filts['gzip_level'], \
            shuffle_filter=filts['shuffle'], \
            compressed_fletcher32_filter=filts['fletcher32'])

        with h5py.File(filename, mode='r') as f:
            d = f[name]
            fletcher32 = d.fletcher32
            shuffle = d.shuffle
            compression = d.compression
            gzip_level = d.compression_opts
            out = d[...]
    except:
        raise
    finally:
        if os.path.exists(filename):
            os.remove(filename)

    # Check the filters
    assert fletcher32 == filts['fletcher32']
    assert shuffle == filts['shuffle']
    assert compression == filts['compression']
    if filts['compression'] == 'gzip':
        assert gzip_level == filts['gzip_level']

    # Compare
    assert_equal(out, data)


def check_uncompressed_write_filters(method,
                                     uncompressed_fletcher32_filter,
                                     filters):
    # Read out the filter arguments.
    filts = {'compression': 'gzip',
             'shuffle': True,
             'fletcher32': True,
             'gzip_level': 7}
    for k, v in filters.items():
        filts[k] = v

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

    # Write the data to the proper file with the given name with the
    # provided filters and read it backt. The file needs to be deleted
    # before and after to keep junk from building up.
    if os.path.exists(filename):
        os.remove(filename)
    try:
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
    except:
        raise
    finally:
        if os.path.exists(filename):
            os.remove(filename)

    # Check the filters
    assert compression == None
    assert shuffle == False
    assert fletcher32 == uncompressed_fletcher32_filter

    # Compare
    assert_equal(out, data)


def test_read_filtered_data():
    for compression in ('gzip', 'lzf'):
        for shuffle in (True, False):
            for fletcher32 in (True, False):
                if compression != 'gzip':
                    filters = {'compression': compression,
                               'shuffle': shuffle,
                               'fletcher32': fletcher32}
                    yield check_read_filters, filters
                else:
                    for level in range(10):
                        filters = {'compression': compression,
                                   'shuffle': shuffle,
                                   'fletcher32': fletcher32,
                                   'gzip_level': level}
                        yield check_read_filters, filters


def test_write_filtered_data():
    for compression in ('gzip', 'lzf'):
        for shuffle in (True, False):
            for fletcher32 in (True, False):
                if compression != 'gzip':
                    filters = {'compression': compression,
                               'shuffle': shuffle,
                               'fletcher32': fletcher32}
                    yield check_read_filters, filters
                else:
                    for level in range(10):
                        filters = {'compression': compression,
                                   'shuffle': shuffle,
                                   'fletcher32': fletcher32,
                                   'gzip_level': level}
                        yield check_write_filters, filters


def test_uncompressed_write_filtered_data():
    for method in ('compression_disabled', 'data_too_small'):
        for uncompressed_fletcher32_filter in (True, False):
            for compression in ('gzip', 'lzf'):
                for shuffle in (True, False):
                    for fletcher32 in (True, False):
                        if compression != 'gzip':
                            filters = {'compression': compression,
                                       'shuffle': shuffle,
                                       'fletcher32': fletcher32}
                            yield check_read_filters, filters
                        else:
                            for level in range(10):
                                filters = {'compression': compression,
                                           'shuffle': shuffle,
                                           'fletcher32': fletcher32,
                                           'gzip_level': level}
                                yield check_uncompressed_write_filters,\
                                    method, uncompressed_fletcher32_filter,\
                                    filters
