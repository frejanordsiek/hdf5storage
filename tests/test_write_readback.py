# Copyright (c) 2013, Freja Nordsiek
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
import copy
import os
import os.path
import posixpath
import string
import math
import random
import collections

import numpy as np
import numpy.testing as npt
import numpy.random

import hdf5storage

from asserts import *


random.seed()


class TestPythonMatlabFormat(object):
    # Test for the ability to write python types to an HDF5 file that
    # type information and matlab information are stored in, and then
    # read it back and have it be the same.
    def __init__(self):
        self.filename = 'data.mat'
        self.options = hdf5storage.Options()

        # Need a list of the supported numeric dtypes to test, excluding
        # those not supported by MATLAB. 'S' and 'U' dtype chars have to
        # be used for the bare byte and unicode string dtypes since the
        # dtype strings (but not chars) are not the same in Python 2 and
        # 3.
        self.dtypes = ['bool', 'uint8', 'uint16', 'uint32', 'uint64',
                       'int8', 'int16', 'int32', 'int64',
                       'float32', 'float64', 'complex64', 'complex128',
                       'S', 'U']

        # Define the sizes of random datasets to use.
        self.max_string_length = 10
        self.max_array_axis_length = 8
        self.max_list_length = 6
        self.max_posix_path_depth = 5
        self.max_posix_path_lengths = 17
        self.object_subarray_dimensions = 2
        self.max_object_subarray_axis_length = 5
        self.min_dict_keys = 4
        self.max_dict_keys = 12
        self.max_dict_key_length = 10
        self.dict_value_subarray_dimensions = 2
        self.max_dict_value_subarray_axis_length = 5

    def random_str_ascii(self, length):
        # Makes a random ASCII str of the specified length.
        if sys.hexversion >= 0x03000000:
            ltrs = string.ascii_letters + string.digits
            return ''.join([random.choice(ltrs) for i in \
                range(0, length)])
        else:
            ltrs = unicode(string.ascii_letters + string.digits)
            return u''.join([random.choice(ltrs) for i in \
                range(0, length)])

    def random_str_some_unicode(self, length):
        # Makes a random ASCII+limited unicode str of the specified
        # length.
        if sys.hexversion >= 0x03000000:
            ltrs = '\u03c0\u03c9\xe9'
            return ''.join([random.choice(ltrs) for i in \
                range(0, length)])
        else:
            ltrs = u'\u03c0\u03c9\xe9'
            return u''.join([random.choice(ltrs) for i in \
                range(0, length)])

    def random_bytes(self, length):
        # Makes a random sequence of bytes of the specified length from
        # the ASCII set.
        ltrs = bytes(range(1, 127))
        return bytes([random.choice(ltrs) for i in range(0, length)])

    def random_int(self):
        return random.randint(-(2**63 - 1), 2**63)

    def random_float(self):
        return random.uniform(-1.0, 1.0) \
            * 10.0**random.randint(-300, 300)

    def random_numpy(self, shape, dtype):
        # Makes a random numpy array of the specified shape and dtype
        # string. The method is slightly different depending on the
        # type. For 'bytes', 'str', and 'object'; an array of the
        # specified size is made and then each element is set to either
        # a numpy.bytes_, numpy.str_, or some other object of any type
        # (here, it is a randomly typed random numpy array). If it is
        # any other type, then it is just a matter of constructing the
        # right sized ndarray from a random sequence of bytes (all must
        # be forced to 0 and 1 for bool).
        if dtype == 'S':
            length = random.randint(1, self.max_string_length)
            data = np.zeros(shape=shape, dtype='S' + str(length))
            for x in np.nditer(data, op_flags=['readwrite']):
                x[...] = np.bytes_(self.random_bytes(length))
            return data
        elif dtype == 'U':
            length = random.randint(1, self.max_string_length)
            data = np.zeros(shape=shape, dtype='U' + str(length))
            for x in np.nditer(data, op_flags=['readwrite']):
                x[...] = np.unicode_(self.random_str_ascii(length))
            return data
        elif dtype == 'object':
            data = np.zeros(shape=shape, dtype='object')
            for index, x in np.ndenumerate(data):
                data[index] = self.random_numpy( \
                    shape=self.random_numpy_shape( \
                    self.object_subarray_dimensions, \
                    self.max_object_subarray_axis_length), \
                    dtype=random.choice(self.dtypes))
            return data
        else:
            nbytes = np.ndarray(shape=(1,), dtype=dtype).nbytes
            bts = np.random.bytes(nbytes * np.prod(shape))
            if dtype == 'bool':
                bts = b''.join([{True: b'\x01', False: b'\x00'}[ \
                    ch > 127] for ch in bts])
            return np.ndarray(shape=shape, dtype=dtype, buffer=bts)

    def random_numpy_scalar(self, dtype):
        # How a random scalar is made depends on th type. For must, it
        # is just a single number. But for the string types, it is a
        # string of any length.
        if dtype == 'S':
            return np.bytes_(self.random_bytes(random.randint(1,
                             self.max_string_length)))
        elif dtype == 'U':
            return np.unicode_(self.random_str_ascii(
                               random.randint(1,
                               self.max_string_length)))
        else:
            return self.random_numpy(tuple(), dtype)[()]

    def random_numpy_shape(self, dimensions, max_length):
        # Makes a random shape tuple having the specified number of
        # dimensions. The maximum size along each axis is max_length.
        return tuple([random.randint(1, max_length) for x in range(0,
                     dimensions)])

    def random_list(self, N, python_or_numpy='numpy'):
        # Makes a random list of the specified type. If instructed, it
        # will be composed entirely from random numpy arrays (make a
        # random object array and then convert that to a
        # list). Otherwise, it will be a list of random bytes.
        if python_or_numpy == 'numpy':
            return self.random_numpy((N,), dtype='object').tolist()
        else:
            data = []
            for i in range(0, N):
                data.append(self.random_bytes(random.randint(1,
                            self.max_string_length)))
            return data

    def random_dict(self):
        # Makes a random dict (random number of randomized keys with
        # random numpy arrays as values).
        data = dict()
        for i in range(0, random.randint(self.min_dict_keys, \
                self.max_dict_keys)):
            name = self.random_str_ascii(self.max_dict_key_length)
            data[name] = \
                self.random_numpy(self.random_numpy_shape( \
                self.dict_value_subarray_dimensions, \
                self.max_dict_value_subarray_axis_length), \
                dtype=random.choice(self.dtypes))
        return data

    def random_name(self):
        # Makes a random POSIX path of a random depth.
        depth = random.randint(1, self.max_posix_path_depth)
        path = '/'
        for i in range(0, depth):
            path = posixpath.join(path, self.random_str_ascii(
                                  random.randint(1,
                                  self.max_posix_path_lengths)))
        return path

    def write_readback(self, data, name, options):
        # Write the data to the proper file with the given name, read it
        # back, and return the result. The file needs to be deleted
        # before and after to keep junk from building up.
        if os.path.exists(self.filename):
            os.remove(self.filename)
        try:
            hdf5storage.write(data, path=name, filename=self.filename,
                              options=options)
            out = hdf5storage.read(path=name, filename=self.filename,
                                   options=options)
        except:
            raise
        finally:
            if os.path.exists(self.filename):
                os.remove(self.filename)
        return out

    def assert_equal(self, a, b):
        assert_equal(a, b)

    def check_numpy_scalar(self, dtype):
        # Makes a random numpy scalar of the given type, writes it and
        # reads it back, and then compares it.
        data = self.random_numpy_scalar(dtype)
        out = self.write_readback(data, self.random_name(),
                                  self.options)
        self.assert_equal(out, data)

    def check_numpy_array(self, dtype, dimensions):
        # Makes a random numpy array of the given type, writes it and
        # reads it back, and then compares it.
        shape = self.random_numpy_shape(dimensions,
                                        self.max_array_axis_length)
        data = self.random_numpy(shape, dtype)
        out = self.write_readback(data, self.random_name(),
                                  self.options)
        self.assert_equal(out, data)

    def check_numpy_empty(self, dtype):
        # Makes an empty numpy array of the given type, writes it and
        # reads it back, and then compares it.
        data = np.array([], dtype)
        out = self.write_readback(data, self.random_name(),
                                  self.options)
        self.assert_equal(out, data)

    def check_python_collection(self, tp):
        # Makes a random collection of the specified type, writes it and
        # reads it back, and then compares it.
        if tp in (set, frozenset):
            data = tp(self.random_list(self.max_list_length,
                      python_or_numpy='python'))
        else:
            data = tp(self.random_list(self.max_list_length,
                      python_or_numpy='numpy'))
        out = self.write_readback(data, self.random_name(),
                                  self.options)
        self.assert_equal(out, data)

    def test_None(self):
        data = None
        out = self.write_readback(data, self.random_name(),
                                  self.options)
        self.assert_equal(out, data)

    def test_bool_True(self):
        data = True
        out = self.write_readback(data, self.random_name(),
                                  self.options)
        self.assert_equal(out, data)

    def test_bool_False(self):
        data = False
        out = self.write_readback(data, self.random_name(),
                                  self.options)
        self.assert_equal(out, data)

    def test_int(self):
        data = self.random_int()
        out = self.write_readback(data, self.random_name(),
                                  self.options)
        self.assert_equal(out, data)

    def test_float(self):
        data = self.random_float()
        out = self.write_readback(data, self.random_name(),
                                  self.options)
        self.assert_equal(out, data)

    def test_float_inf(self):
        data = float(np.inf)
        out = self.write_readback(data, self.random_name(),
                                  self.options)
        self.assert_equal(out, data)

    def test_float_ninf(self):
        data = float(-np.inf)
        out = self.write_readback(data, self.random_name(),
                                  self.options)
        self.assert_equal(out, data)

    def test_float_nan(self):
        data = float(np.nan)
        out = self.write_readback(data, self.random_name(),
                                  self.options)
        assert math.isnan(out)

    def test_complex(self):
        data = self.random_float() + 1j*self.random_float()
        out = self.write_readback(data, self.random_name(),
                                  self.options)
        self.assert_equal(out, data)

    def test_complex_real_nan(self):
        data = complex(np.nan, self.random_float())
        out = self.write_readback(data, self.random_name(),
                                  self.options)
        self.assert_equal(out, data)

    def test_complex_imaginary_nan(self):
        data = complex(self.random_float(), np.nan)
        out = self.write_readback(data, self.random_name(),
                                  self.options)
        self.assert_equal(out, data)

    def test_str_ascii(self):
        data = self.random_str_ascii(random.randint(1,
                                     self.max_string_length))
        out = self.write_readback(data, self.random_name(),
                                  self.options)
        self.assert_equal(out, data)

    def test_str_unicode(self):
        data = self.random_str_some_unicode(random.randint(1,
                                            self.max_string_length))
        out = self.write_readback(data, self.random_name(),
                                  self.options)
        self.assert_equal(out, data)

    def test_str_empty(self):
        data = ''
        out = self.write_readback(data, self.random_name(),
                                  self.options)
        self.assert_equal(out, data)

    def test_bytes(self):
        data = self.random_bytes(random.randint(1,
                                 self.max_string_length))
        out = self.write_readback(data, self.random_name(),
                                  self.options)
        self.assert_equal(out, data)

    def test_bytes_empty(self):
        data = b''
        out = self.write_readback(data, self.random_name(),
                                  self.options)
        self.assert_equal(out, data)

    def test_bytearray(self):
        data = bytearray(self.random_bytes(random.randint(1,
                         self.max_string_length)))
        out = self.write_readback(data, self.random_name(),
                                  self.options)
        self.assert_equal(out, data)

    def test_bytearray_empty(self):
        data = bytearray(b'')
        out = self.write_readback(data, self.random_name(),
                                  self.options)
        self.assert_equal(out, data)

    def test_numpy_scalar(self):
        for dt in self.dtypes:
            yield self.check_numpy_scalar, dt

    def test_numpy_array_1d(self):
        dtypes = copy.deepcopy(self.dtypes)
        dtypes.append('object')
        for dt in dtypes:
            yield self.check_numpy_array, dt, 1

    def test_numpy_array_2d(self):
        dtypes = copy.deepcopy(self.dtypes)
        dtypes.append('object')
        for dt in dtypes:
            yield self.check_numpy_array, dt, 2

    def test_numpy_array_3d(self):
        dtypes = copy.deepcopy(self.dtypes)
        dtypes.append('object')
        for dt in dtypes:
            yield self.check_numpy_array, dt, 3

    def test_numpy_empty(self):
        for dt in self.dtypes:
            yield self.check_numpy_empty, dt

    def test_python_collection(self):
        for tp in (list, tuple, set, frozenset, collections.deque):
            yield self.check_python_collection, tp

    def test_dict(self):
        data = self.random_dict()
        out = self.write_readback(data, self.random_name(),
                                  self.options)
        self.assert_equal(out, data)


class TestPythonFormat(TestPythonMatlabFormat):
    def __init__(self):
        # The parent does most of the setup. All that has to be changed
        # is turning MATLAB compatibility off and changing the file
        # name.
        TestPythonMatlabFormat.__init__(self)
        self.options = hdf5storage.Options(matlab_compatible=False)
        self.filename = 'data.h5'


class TestNoneFormat(TestPythonMatlabFormat):
    def __init__(self):
        # The parent does most of the setup. All that has to be changed
        # is turning off the storage of type information as well as
        # MATLAB compatibility.
        TestPythonMatlabFormat.__init__(self)
        self.options = hdf5storage.Options(store_python_metadata=False,
                                           matlab_compatible=False)

        # Add in float16 to the set of types tested.
        self.dtypes.append('float16')

    def assert_equal(self, a, b):
        assert_equal_none_format(a, b)


class TestMatlabFormat(TestPythonMatlabFormat):
    def __init__(self):
        # The parent does most of the setup. All that has to be changed
        # is turning on the matlab compatibility, and changing the
        # filename.
        TestPythonMatlabFormat.__init__(self)
        self.options = hdf5storage.Options(store_python_metadata=False,
                                           matlab_compatible=True)
        self.filename = 'data.mat'

    def assert_equal(self, a, b):
        assert_equal_matlab_format(a, b)
