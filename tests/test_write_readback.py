#!/usr/bin/env python3

import sys
import os
import os.path
import posixpath
import string
import math
import random

import numpy as np
import numpy.testing as npt
import numpy.random

import hdf5storage


random.seed()


class TestPythonMatlabFormat(object):
    def __init__(self):
        self.filename = 'data.mat'
        self.options = hdf5storage.Options()

        # Need a list of the supported numeric dtypes to test.
        self.dtypes = ['bool', 'uint8', 'uint16', 'uint32', 'uint64',
                       'int8', 'int16', 'int32', 'int64', 'float16',
                       'float32', 'float64', 'complex64', 'complex128',
                       'bytes', 'str']

        # Now, there is an assert_equal_X where X is a type for every
        # type. Unless one is overridden in a subclass, they should all
        # the base one. Storing things in the dict self.__dict__ will do
        # this.

        types = ['None', 'bool', 'int', 'float', 'complex', 'str',
                 'bytes', 'bytearray']
        for tp in types:
            self.__dict__['assert_equal_' + tp] = self.assert_equal

    def random_str_ascii(self, length):
        ltrs = string.ascii_letters + string.digits
        return ''.join([random.choice(ltrs) for i in range(0, length)])

    def random_bytes(self, length):
        ltrs = bytes(range(1, 127))
        return bytes([random.choice(ltrs) for i in range(0, length)])

    def random_int(self):
        return random.randint(-(2**63 - 1), 2**63)

    def random_float(self):
        return random.uniform(-1.0, 1.0) \
            * 10.0**random.randint(-300, 300)

    def random_numpy(self, shape, dtype):
        if dtype in 'bytes':
            length = random.randint(1, 100)
            data = np.zeros(shape=shape, dtype='S' + str(length))
            for x in np.nditer(data, op_flags=['readwrite']):
                x[...] = np.bytes_(self.random_bytes(length))
            return data
        elif dtype == 'str':
            length = random.randint(1, 100)
            data = np.zeros(shape=shape, dtype='U' + str(length))
            for x in np.nditer(data, op_flags=['readwrite']):
                x[...] = np.str_(self.random_str_ascii(length))
            return data
        else:
            nbytes = np.ndarray(shape=(1,), dtype=dtype).nbytes
            bts = np.random.bytes(nbytes * np.prod(shape))
            if dtype == 'bool':
                bts = b''.join([{True: b'\x01', False: b'\x00'}[ \
                    ch > 127] for ch in bts])
            return np.ndarray(shape=shape, dtype=dtype, buffer=bts)

    def random_numpy_scalar(self, dtype):
        if dtype == 'bytes':
            return np.bytes_(self.random_bytes(random.randint(1, 100)))
        elif dtype == 'str':
            return np.str_(self.random_str_ascii(
                           random.randint(1, 100)))
        else:
            return self.random_numpy(tuple(), dtype)[()]

    def random_name(self):
        depth = random.randint(1, 5)
        path = '/'
        for i in range(0, depth):
            path = posixpath.join(path, self.random_str_ascii(
                                  random.randint(1, 17)))
        return path

    def write_readback(self, data, name, options):
        # Write the data to the proper file with the given name, read it
        # back, and return the result. The file needs to be deleted
        # before and after to keep junk from building up.
        if os.path.exists(self.filename):
            os.remove(self.filename)
        try:
            hdf5storage.write(data, name=name, filename=self.filename,
                              options=options)
            out = hdf5storage.read(name=name, filename=self.filename,
                                options=options)
        except:
            raise
        finally:
            if os.path.exists(self.filename):
                os.remove(self.filename)
        return out

    def assert_equal(self, a, b):
        assert a == b

    def assert_equal_numpy(self, a, b):
        assert type(a) == type(b)
        assert a.dtype == b.dtype
        npt.assert_equal(a, b)
    
    def test_None(self):
        data = None
        out = self.write_readback(data, self.random_name(),
                                  self.options)
        self.assert_equal_None(out, data)

    def test_bool_True(self):
        data = True
        out = self.write_readback(data, self.random_name(),
                                  self.options)
        self.assert_equal_bool(out, data)

    def test_bool_False(self):
        data = False
        out = self.write_readback(data, self.random_name(),
                                  self.options)
        self.assert_equal_bool(out, data)

    def test_int(self):
        data = self.random_int()
        out = self.write_readback(data, self.random_name(),
                                  self.options)
        self.assert_equal_int(out, data)

    def test_float(self):
        data = self.random_float()
        out = self.write_readback(data, self.random_name(),
                                  self.options)
        self.assert_equal_float(out, data)

    def test_float_inf(self):
        data = float(np.inf)
        out = self.write_readback(data, self.random_name(),
                                  self.options)
        self.assert_equal_float(out, data)

    def test_float_ninf(self):
        data = float(-np.inf)
        out = self.write_readback(data, self.random_name(),
                                  self.options)
        self.assert_equal_float(out, data)

    def test_float_nan(self):
        data = float(np.nan)
        out = self.write_readback(data, self.random_name(),
                                  self.options)
        assert math.isnan(out)

    def test_complex(self):
        data = self.random_float() + 1j*self.random_float()
        out = self.write_readback(data, self.random_name(),
                                  self.options)
        self.assert_equal_complex(out, data)

    def test_str(self):
        data = self.random_str_ascii(random.randint(1, 100))
        out = self.write_readback(data, self.random_name(),
                                  self.options)
        self.assert_equal_str(out, data)

    def test_str_empty(self):
        data = ''
        out = self.write_readback(data, self.random_name(),
                                  self.options)
        self.assert_equal_str(out, data)

    def test_bytes(self):
        data = self.random_bytes(random.randint(1, 100))
        out = self.write_readback(data, self.random_name(),
                                  self.options)
        self.assert_equal_bytes(out, data)

    def test_bytes_empty(self):
        data = b''
        out = self.write_readback(data, self.random_name(),
                                  self.options)
        self.assert_equal_bytes(out, data)

    def test_bytearray(self):
        data = bytearray(self.random_bytes(random.randint(1, 100)))
        out = self.write_readback(data, self.random_name(),
                                  self.options)
        self.assert_equal_bytearray(out, data)

    def test_bytearray_empty(self):
        data = bytearray(b'')
        out = self.write_readback(data, self.random_name(),
                                  self.options)
        self.assert_equal_bytearray(out, data)

    def check_numpy_scalar(self, dtype):
        data = self.random_numpy_scalar(dtype)
        out = self.write_readback(data, self.random_name(),
                                  self.options)
        self.assert_equal_numpy(out, data)

    def check_numpy_array(self, dtype):
        shape = (random.randint(1, 12), random.randint(1, 12))
        data = self.random_numpy(shape, dtype)
        out = self.write_readback(data, self.random_name(),
                                  self.options)
        self.assert_equal_numpy(out, data)

    def check_numpy_empty(self, dtype):
        data = np.array([], dtype)
        out = self.write_readback(data, self.random_name(),
                                  self.options)
        self.assert_equal_numpy(out, data)

    def test_numpy_scalar(self):
        for dt in self.dtypes:
            yield self.check_numpy_scalar, dt

    def test_numpy_array(self):
        for dt in self.dtypes:
            yield self.check_numpy_array, dt

    def test_numpy_empty(self):
        for dt in self.dtypes:
            yield self.check_numpy_empty, dt


class TestPythonFormat(TestPythonMatlabFormat):
    def __init__(self):
        # The parent does most of the setup. All that has to be changed
        # is turning MATLAB compatibility off and changing the file
        # name.
        TestPythonMatlabFormat.__init__(self)
        self.options = hdf5storage.Options(matlab_compatible=False)
        self.filename = 'data.h5'
