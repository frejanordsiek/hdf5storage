#!/usr/bin/env python3

import sys
import os
import os.path
import posixpath
import string
import math
import random
import unittest

import numpy as np

import hdf5storage


random.seed()


class TestWriteReadbackCpythonMatlab(unittest.TestCase):
    def setUp(self):
        self.filename = 'data.h5'

        # Use the default options.
        self.options = hdf5storage.Options()

        # Now, there is a write_readback_X and assert_equal_X where X is
        # a type for every type. Unless one is overridden in a subclass,
        # they should all point to write_readback. Storing things in the
        # dict self.__dict__ will do this.

        types = ['None', 'bool', 'int', 'float', 'complex', 'str',
                 'bytes', 'bytearray']
        for tp in types:
            self.__dict__['write_readback_' + tp] = self.write_readback
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
        self.assertEqual(a, b)

    def test_None(self):
        data = None
        out = self.write_readback_None(data, self.random_name(),
                                       self.options)
        self.assert_equal_None(data, out)

    def test_bool_True(self):
        data = True
        out = self.write_readback_bool(data, self.random_name(),
                                       self.options)
        self.assert_equal_bool(data, out)

    def test_bool_False(self):
        data = False
        out = self.write_readback_bool(data, self.random_name(),
                                       self.options)
        self.assert_equal_bool(data, out)

    def test_int(self):
        data = self.random_int()
        out = self.write_readback_int(data, self.random_name(),
                                      self.options)
        self.assert_equal_int(data, out)

    def test_float(self):
        data = self.random_float()
        out = self.write_readback_float(data, self.random_name(),
                                        self.options)
        self.assert_equal_float(data, out)

    def test_float_inf(self):
        data = float(np.inf)
        out = self.write_readback_float(data, self.random_name(),
                                        self.options)
        self.assert_equal_float(data, out)

    def test_float_ninf(self):
        data = float(-np.inf)
        out = self.write_readback_float(data, self.random_name(),
                                        self.options)
        self.assert_equal_float(data, out)

    def test_float_nan(self):
        data = float(np.nan)
        out = self.write_readback_float(data, self.random_name(),
                                        self.options)
        self.assertTrue(math.isnan(out))

    def test_complex(self):
        data = self.random_float() + 1j*self.random_float()
        out = self.write_readback_float(data, self.random_name(),
                                        self.options)
        self.assert_equal_float(data, out)

    def test_str(self):
        data = self.random_str_ascii(random.randint(1, 100))
        out = self.write_readback_str(data, self.random_name(),
                                      self.options)
        self.assert_equal_str(data, out)

    @unittest.expectedFailure
    def test_str_empty(self):
        data = ''
        out = self.write_readback_str(data, self.random_name(),
                                      self.options)
        self.assert_equal_str(data, out)

    def test_bytes(self):
        data = self.random_bytes(random.randint(1, 100))
        out = self.write_readback_bytes(data, self.random_name(),
                                        self.options)
        self.assert_equal_bytes(data, out)

    @unittest.expectedFailure
    def test_bytes_empty(self):
        data = b''
        out = self.write_readback_bytes(data, self.random_name(),
                                        self.options)
        self.assert_equal_bytes(data, out)

    def test_bytearray(self):
        data = bytearray(self.random_bytes(random.randint(1, 100)))
        out = self.write_readback_bytearray(data, self.random_name(),
                                            self.options)
        self.assert_equal_bytearray(data, out)

    @unittest.expectedFailure
    def test_bytearray_empty(self):
        data = bytearray(b'')
        out = self.write_readback_bytearray(data, self.random_name(),
                                            self.options)
        self.assert_equal_bytearray(data, out)

if __name__ == '__main__':
    unittest.main()
