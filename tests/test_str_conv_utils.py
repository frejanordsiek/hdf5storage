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

import numpy as np
import numpy.random

import hdf5storage.utilities as utils

from asserts import *
from make_randoms import *

random.seed()


def test_numpy_str_ascii_to_uint16_back():
    for i in range(10):
        data = random_numpy(shape=(1, ), dtype='U',
                            allow_unicode=False)[()]
        intermed = utils.convert_numpy_str_to_uint16(data)
        out = utils.convert_to_numpy_str(intermed)
        assert_equal(out, data)


def test_numpy_str_someunicode_to_uint16_back():
    for i in range(10):
        data = random_numpy(shape=(1, ), dtype='U',
                            allow_unicode=True)[()]
        intermed = utils.convert_numpy_str_to_uint16(data)
        out = utils.convert_to_numpy_str(intermed)
        assert_equal(out, data)


def test_numpy_str_ascii_to_uint32_back():
    for i in range(10):
        data = random_numpy(shape=(1, ), dtype='U',
                            allow_unicode=False)[()]
        intermed = utils.convert_numpy_str_to_uint32(data)
        out = utils.convert_to_numpy_str(intermed)
        assert intermed.tobytes() == data.tobytes()
        assert_equal(out, data)


def test_numpy_str_someunicode_to_uint32_back():
    for i in range(10):
        data = random_numpy(shape=(1, ), dtype='U',
                            allow_unicode=True)[()]
        intermed = utils.convert_numpy_str_to_uint32(data)
        out = utils.convert_to_numpy_str(intermed)
        assert intermed.tobytes() == data.tobytes()
        assert_equal(out, data)
