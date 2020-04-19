# -*- coding: utf-8 -*-

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

import sys
import os
import os.path
import tempfile

import numpy as np
import h5py

import hdf5storage

import nose.tools


# A test to make sure that the following are written as UTF-16
# (uint16) if they don't contain doublets and the
# convert_numpy_str_to_utf16 option is set.
#
# * str
# * numpy.unicode_ scalars

def check_conv_utf16(tp):
    name = '/a'
    data = tp('abcdefghijklmnopqrstuvwxyz')
    fld = None
    try:
        fld = tempfile.mkstemp()
        os.close(fld[0])
        filename = fld[1]
        hdf5storage.write(data, path=name, filename=filename,
                          matlab_compatible=False,
                          store_python_metadata=False,
                          convert_numpy_str_to_utf16=True)
        with h5py.File(filename, mode='r') as f:
            nose.tools.assert_equal(f[name].dtype.type, np.uint16)
    except:
        raise
    finally:
        if fld is not None:
            os.remove(fld[1])


def test_conv_utf16():
    if sys.hexversion < 0x3000000:
        tps = (unicode, np.unicode_)
    else:
        tps = (str, np.unicode_)
    for tp in tps:
        yield check_conv_utf16, tp
