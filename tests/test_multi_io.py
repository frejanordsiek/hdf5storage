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

import hdf5storage

from asserts import *
from make_randoms import *


random.seed()


filename = 'data.mat'


# A series of tests to make sure that more than one data item can be
# written or read at a time using the writes and reads functions.

def test_multi_write():
    # Makes a random dict of random paths and variables (random number
    # of randomized paths with random numpy arrays as values).
    data = dict()
    for i in range(0, random.randint(min_dict_keys, \
            max_dict_keys)):
        name = random_name()
        data[name] = \
            random_numpy(random_numpy_shape( \
            dict_value_subarray_dimensions, \
            max_dict_value_subarray_axis_length), \
            dtype=random.choice(dtypes))

    # Write it and then read it back item by item.
    if os.path.exists(filename):
        os.remove(filename)
    try:
        hdf5storage.writes(mdict=data, filename=filename)
        out = dict()
        for p in data:
            out[p] = hdf5storage.read(path=p, filename=filename)
    except:
        raise
    finally:
        if os.path.exists(filename):
            os.remove(filename)

    # Compare data and out.
    assert_equal(out, data)


def test_multi_read():
    # Makes a random dict of random paths and variables (random number
    # of randomized paths with random numpy arrays as values).
    data = dict()
    for i in range(0, random.randint(min_dict_keys, \
            max_dict_keys)):
        name = random_name()
        data[name] = \
            random_numpy(random_numpy_shape( \
            dict_value_subarray_dimensions, \
            max_dict_value_subarray_axis_length), \
            dtype=random.choice(dtypes))

    paths = data.keys()
    # Write it item by item  and then read it back in one unit.
    if os.path.exists(filename):
        os.remove(filename)
    try:
        for p in paths:
            hdf5storage.write(data=data[p], path=p, filename=filename)
        out = hdf5storage.reads(paths=list(data.keys()),
                                filename=filename)
    except:
        raise
    finally:
        if os.path.exists(filename):
            os.remove(filename)

    # Compare data and out.
    for i, p in enumerate(paths):
        assert_equal(out[i], data[p])
