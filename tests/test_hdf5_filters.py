# Copyright (c) 2013-2015, Freja Nordsiek
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
        with h5py.File(filename) as f:
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
