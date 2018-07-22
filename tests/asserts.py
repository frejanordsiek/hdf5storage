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
import collections
import warnings

import numpy as np
import numpy.testing as npt


def assert_dtypes_equal(a, b):
    # Check that two dtypes are equal, but ignorning itemsize for dtypes
    # whose shape is 0.
    assert isinstance(a, np.dtype)
    assert a.shape == b.shape
    if b.names is None:
        assert a == b
    else:
        assert a.names == b.names
        for n in b.names:
            assert_dtypes_equal(a[n], b[n])


def assert_equal(a, b):
    # Compares a and b for equality. If they are dictionaries, they must
    # have the same set of keys, after which they values must all be
    # compared. If they are a collection type (list, tuple, set,
    # frozenset, or deque), they must have the same length and their
    # elements must be compared. If they are not numpy types (aren't
    # or don't inherit from np.generic or np.ndarray), then it is a
    # matter of just comparing them. Otherwise, their dtypes and shapes
    # have to be compared. Then, if they are not an object array,
    # numpy.testing.assert_equal will compare them elementwise. For
    # object arrays, each element must be iterated over to be compared.
    assert type(a) == type(b)
    if type(b) == dict:
        assert set(a.keys()) == set(b.keys())
        for k in b:
            assert_equal(a[k], b[k])
    elif type(b) in (list, tuple, set, frozenset, collections.deque):
        assert len(a) == len(b)
        if type(b) in (set, frozenset):
            assert a == b
        else:
            for index in range(0, len(a)):
                assert_equal(a[index], b[index])
    elif not isinstance(b, (np.generic, np.ndarray)):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', RuntimeWarning)
            if isinstance(b, complex):
                assert a.real == b.real \
                    or np.all(np.isnan([a.real, b.real]))
                assert a.imag == b.imag \
                    or np.all(np.isnan([a.imag, b.imag]))
            else:
                assert a == b or np.all(np.isnan([a, b]))
    else:
        assert_dtypes_equal(a.dtype, b.dtype)
        assert a.shape == b.shape
        if b.dtype.name != 'object':
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', RuntimeWarning)
                npt.assert_equal(a, b)
        else:
            for index, x in np.ndenumerate(a):
                assert_equal(a[index], b[index])


def assert_equal_none_format(a, b):
    # Compares a and b for equality. b is always the original. If they
    # are dictionaries, a must be a structured ndarray and they must
    # have the same set of keys, after which they values must all be
    # compared. If they are a collection type (list, tuple, set,
    # frozenset, or deque), then the compairison must be made with b
    # converted to an object array. If the original is not a numpy type
    # (isn't or doesn't inherit from np.generic or np.ndarray), then it
    # is a matter of converting it to the appropriate numpy
    # type. Otherwise, both are supposed to be numpy types. For object
    # arrays, each element must be iterated over to be compared. Then,
    # if it isn't a string type, then they must have the same dtype,
    # shape, and all elements. If it is an empty string, then it would
    # have been stored as just a null byte (recurse to do that
    # comparison). If it is a bytes_ type, the dtype, shape, and
    # elements must all be the same. If it is string_ type, we must
    # convert to uint32 and then everything can be compared.
    if type(b) == dict:
        assert type(a) == np.ndarray
        assert a.dtype.names is not None
        assert set(a.dtype.names) == set(b.keys())
        for k in b:
            assert_equal_none_format(a[k][0], b[k])
    elif type(b) in (list, tuple, set, frozenset, collections.deque):
        b_conv = np.zeros(dtype='object', shape=(len(b), ))
        for i, v in enumerate(b):
            b_conv[i] = v
        assert_equal_none_format(a, b_conv)
    elif not isinstance(b, (np.generic, np.ndarray)):
        if b is None:
            # It should be np.float64([])
            assert type(a) == np.ndarray
            assert a.dtype == np.float64([]).dtype
            assert a.shape == (0, )
        elif (sys.hexversion >= 0x03000000 \
                and isinstance(b, (bytes, bytearray))) \
                or (sys.hexversion < 0x03000000 \
                and isinstance(b, (bytes, bytearray))):
            assert a == np.bytes_(b)
        elif (sys.hexversion >= 0x03000000 \
                and isinstance(b, str)) \
                or (sys.hexversion < 0x03000000 \
                and isinstance(b, unicode)):
            assert_equal_none_format(a, np.unicode_(b))
        elif (sys.hexversion >= 0x03000000 \
                and type(b) == int) \
                or (sys.hexversion < 0x03000000 \
                and type(b) == long):
            assert_equal_none_format(a, np.int64(b))
        else:
            assert_equal_none_format(a, np.array(b)[()])
    elif isinstance(b, np.recarray):
        assert_equal_none_format(a, b.view(np.ndarray))
    else:
        if b.dtype.name != 'object':
            if b.dtype.char in ('U', 'S'):
                if b.dtype.char == 'S' and b.shape == tuple() \
                        and len(b) == 0:
                    assert_equal(a, \
                        np.zeros(shape=tuple(), dtype=b.dtype.char))
                elif b.dtype.char == 'U':
                    if b.shape == tuple() and len(b) == 0:
                        c = np.uint32(())
                    else:
                        c = np.atleast_1d(b).view(np.uint32)
                    assert a.dtype == c.dtype
                    assert a.shape == c.shape
                    npt.assert_equal(a, c)
                else:
                    assert a.dtype == b.dtype
                    assert a.shape == b.shape
                    npt.assert_equal(a, b)
            else:
                # Check that the dtype's shape matches.
                assert a.dtype.shape == b.dtype.shape
                # Now, if b.shape is just all ones, then a.shape will
                # just be (1,). Otherwise, we need to compare the shapes
                # directly. Also, dimensions need to be squeezed before
                # comparison in this case.
                assert np.prod(a.shape) == np.prod(b.shape)
                if a.shape != b.shape:
                    assert np.prod(b.shape) == 1
                    assert a.shape == (1, )
                if np.prod(a.shape) == 1:
                    a = np.squeeze(a)
                    b = np.squeeze(b)

                # If there was a null in the dtype or the dtype of one
                # of its fields (or subfields) has a 0 in its shape,
                # then it was written as a Group so the field order
                # could have changed.
                has_zero_shape = False
                if b.dtype.names is not None:
                    parts = [b.dtype]
                    while 0 != len(parts):
                        part = parts.pop()
                        if 0 in part.shape:
                            has_zero_shape = True
                        if part.names is not None:
                            parts.extend([v[0] for v
                                          in part.fields.values()])
                        if part.base != part:
                            parts.append(part.base)
                if b.dtype.names is not None \
                        and ('\\x00' in str(b.dtype) \
                        or has_zero_shape):
                    assert a.shape == b.shape
                    assert set(a.dtype.names) == set(b.dtype.names)
                    for n in b.dtype.names:
                        assert_equal_none_format(a[n], b[n])
                else:
                    assert a.dtype == b.dtype
                    with warnings.catch_warnings():
                        warnings.simplefilter('ignore', RuntimeWarning)
                        npt.assert_equal(a, b)
        else:
            # If the original is structued, it is possible that the
            # fields got out of order, in which case the dtype won't
            # quite match. It will need to be checked just to make sure
            # all pieces are there. Otherwise, the dtypes can be
            # directly compared.
            if b.dtype.fields is None:
                assert a.dtype == b.dtype
            else:
                assert dict(a.dtype.fields) == dict(b.dtype.fields)
            assert a.shape == b.shape
            for index, x in np.ndenumerate(a):
                assert_equal_none_format(a[index], b[index])


def assert_equal_matlab_format(a, b):
    # Compares a and b for equality. b is always the original. If they
    # are dictionaries, a must be a structured ndarray and they must
    # have the same set of keys, after which they values must all be
    # compared. If they are a collection type (list, tuple, set,
    # frozenset, or deque), then the compairison must be made with b
    # converted to an object array. If the original is not a numpy type
    # (isn't or doesn't inherit from np.generic or np.ndarray), then it
    # is a matter of converting it to the appropriate numpy
    # type. Otherwise, both are supposed to be numpy types. For object
    # arrays, each element must be iterated over to be compared. Then,
    # if it isn't a string type, then they must have the same dtype,
    # shape, and all elements. All strings are converted to numpy.str_
    # on read. If it is empty, it has shape (1, 0). A numpy.str_ has all
    # of its strings per row compacted together. A numpy.bytes_ string
    # has to have the same thing done, but then it needs to be converted
    # up to UTF-32 and to numpy.str_ through uint32.
    #
    # In all cases, we expect things to be at least two dimensional
    # arrays.
    if type(b) == dict:
        assert type(a) == np.ndarray
        assert a.dtype.names is not None
        assert set(a.dtype.names) == set(b.keys())
        for k in b:
            assert_equal_matlab_format(a[k][0], b[k])
    elif type(b) in (list, tuple, set, frozenset, collections.deque):
        b_conv = np.zeros(dtype='object', shape=(len(b), ))
        for i, v in enumerate(b):
            b_conv[i] = v
        assert_equal_matlab_format(a, b_conv)
    elif not isinstance(b, (np.generic, np.ndarray)):
        if b is None:
            # It should be np.zeros(shape=(0, 1), dtype='float64'))
            assert type(a) == np.ndarray
            assert a.dtype == np.dtype('float64')
            assert a.shape == (1, 0)
        elif (sys.hexversion >= 0x03000000 \
                and isinstance(b, (bytes, str, bytearray))) \
                or (sys.hexversion < 0x03000000 \
                and isinstance(b, (bytes, unicode, bytearray))):
            if len(b) == 0:
                assert_equal(a, np.zeros(shape=(1, 0), dtype='U'))
            elif isinstance(b, (bytes, bytearray)):
                assert_equal(a, np.atleast_2d(np.unicode_( \
                    b.decode('UTF-8'))))
            else:
                assert_equal(a, np.atleast_2d(np.unicode_(b)))
        elif (sys.hexversion >= 0x03000000 \
                and type(b) == int) \
                or (sys.hexversion < 0x03000000 \
                and type(b) == long):
            assert_equal(a, np.atleast_2d(np.int64(b)))
        else:
            assert_equal(a, np.atleast_2d(np.array(b)))
    else:
        if b.dtype.name != 'object':
            if b.dtype.char in ('U', 'S'):
                if len(b) == 0 and (b.shape == tuple() \
                        or b.shape == (0, )):
                    assert_equal(a, np.zeros(shape=(1, 0),
                                 dtype='U'))
                elif b.dtype.char == 'U':
                    c = np.atleast_1d(b)
                    c = np.atleast_2d(c.view(np.dtype('U' \
                        + str(c.shape[-1]*c.dtype.itemsize//4))))
                    assert a.dtype == c.dtype
                    assert a.shape == c.shape
                    npt.assert_equal(a, c)
                elif b.dtype.char == 'S':
                    c = np.atleast_1d(b)
                    c = c.view(np.dtype('S' \
                        + str(c.shape[-1]*c.dtype.itemsize)))
                    c = np.uint32(c.view(np.ndarray).view(np.dtype('uint8')))
                    c = c.view(np.dtype('U' + str(c.shape[-1])))
                    c = np.atleast_2d(c)
                    assert a.dtype == c.dtype
                    assert a.shape == c.shape
                    npt.assert_equal(a, c)
                    pass
                else:
                    c = np.atleast_2d(b)
                    assert a.dtype == c.dtype
                    assert a.shape == c.shape
                    with warnings.catch_warnings():
                        warnings.simplefilter('ignore', RuntimeWarning)
                        npt.assert_equal(a, c)
            else:
                c = np.atleast_2d(b)
                # An empty complex number gets turned into a real
                # number when it is stored.
                if np.prod(c.shape) == 0 \
                        and b.dtype.name.startswith('complex'):
                    c = np.real(c)
                # If it is structured, check that the field names are
                # the same, in the same order, and then go through them
                # one by one. Otherwise, make sure the dtypes and shapes
                # are the same before comparing all values.
                if b.dtype.names is None and a.dtype.names is None:
                    assert a.dtype == c.dtype
                    assert a.shape == c.shape
                    with warnings.catch_warnings():
                        warnings.simplefilter('ignore', RuntimeWarning)
                        npt.assert_equal(a, c)
                else:
                    assert a.dtype.names is not None
                    assert b.dtype.names is not None
                    assert set(a.dtype.names) == set(b.dtype.names)
                    # The ordering of fields must be preserved if the
                    # MATLAB_fields attribute could be used, which can
                    # only be done if there are no non-ascii characters
                    # in any of the field names.
                    if sys.hexversion >= 0x03000000:
                        allfields = ''.join(b.dtype.names)
                    else:
                        allfields = unicode('').join( \
                            [nm.decode('UTF-8') \
                            for nm in b.dtype.names])
                    if np.all(np.array([ord(ch) < 128 \
                            for ch in allfields])):
                        assert a.dtype.names == b.dtype.names
                    a = a.flatten()
                    b = b.flatten()
                    for k in b.dtype.names:
                        for index, x in np.ndenumerate(a):
                            assert_equal_from_matlab(a[k][index],
                                                     b[k][index])
        else:
            c = np.atleast_2d(b)
            assert a.dtype == c.dtype
            assert a.shape == c.shape
            for index, x in np.ndenumerate(a):
                assert_equal_matlab_format(a[index], c[index])


def assert_equal_from_matlab(a, b):
    # Compares a and b for equality. They are all going to be numpy
    # types. hdf5storage and scipy behave differently when importing
    # arrays as to whether they are 2D or not, so we will make them all
    # at least 2D regardless. For strings, the two packages produce
    # transposed results of each other, so one just needs to be
    # transposed. For object arrays, each element must be iterated over
    # to be compared. For structured ndarrays, their fields need to be
    # compared and then they can be compared element and field
    # wise. Otherwise, they can be directly compared. Note, the type is
    # often converted by scipy (or on route to the file before scipy
    # gets it), so comparisons are done by value, which is not perfect.
    a = np.atleast_2d(a)
    b = np.atleast_2d(b)
    if a.dtype.char == 'U':
        a = a.T
    if b.dtype.name == 'object':
        a = a.flatten()
        b = b.flatten()
        for index, x in np.ndenumerate(a):
            assert_equal_from_matlab(a[index], b[index])
    elif b.dtype.names is not None or a.dtype.names is not None:
        assert a.dtype.names is not None
        assert b.dtype.names is not None
        assert set(a.dtype.names) == set(b.dtype.names)
        a = a.flatten()
        b = b.flatten()
        for k in b.dtype.names:
            for index, x in np.ndenumerate(a):
                assert_equal_from_matlab(a[k][index], b[k][index])
    else:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', RuntimeWarning)
            npt.assert_equal(a, b)
