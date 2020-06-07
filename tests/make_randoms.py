# -*- coding: utf-8 -*-

# Copyright (c) 2013-2020, Freja Nordsiek
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

import collections
import datetime
import fractions
import posixpath
import random
import string
import sys
import warnings

import numpy as np
import numpy.random


random.seed()


# The dtypes that can be made
dtypes = ['bool', 'uint8', 'uint16', 'uint32', 'uint64',
          'int8', 'int16', 'int32', 'int64',
          'float32', 'float64', 'complex64', 'complex128',
          'S', 'U']

# Define the sizes of random datasets to use.
max_string_length = 10
max_array_axis_length = 8
max_list_length = 6
max_posix_path_depth = 5
max_posix_path_lengths = 17
object_subarray_dimensions = 2
max_object_subarray_axis_length = 5
min_dict_keys = 4
max_dict_keys = 12
max_dict_key_length = 10
dict_value_subarray_dimensions = 2
max_dict_value_subarray_axis_length = 5
min_structured_ndarray_fields = 2
max_structured_ndarray_fields = 5
max_structured_ndarray_field_lengths = 10
max_structured_ndarray_axis_length = 2
structured_ndarray_subarray_dimensions = 2
max_structured_ndarray_subarray_axis_length = 4


def random_str_ascii_letters(length):
    # Makes a random ASCII str of the specified length.
    ltrs = string.ascii_letters
    return ''.join([random.choice(ltrs) for i in
                   range(0, length)])


def random_str_ascii(length):
    # Makes a random ASCII str of the specified length.
    ltrs = string.ascii_letters + string.digits
    return ''.join([random.choice(ltrs) for i in
                   range(0, length)])


def random_str_some_unicode(length):
    # Makes a random ASCII+limited unicode str of the specified
    # length.
    ltrs = random_str_ascii(10)
    ltrs += 'αβγδεζηθικλμνξοπρστυφχψωΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩς'
    c = ''
    return c.join([random.choice(ltrs) for i in range(0, length)])


def random_bytes(length):
    # Makes a random sequence of bytes of the specified length from
    # the ASCII set.
    ltrs = bytes(range(1, 127))
    return bytes([random.choice(ltrs) for i in range(0, length)])


def random_bytes_fullrange(length):
    # Makes a random sequence of bytes of the specified length from
    # the ASCII set.
    ltrs = bytes(range(1, 255))
    return bytes([random.choice(ltrs) for i in range(0, length)])

def random_int():
    return random.randint(-(2**31 - 1), 2**31)


def random_float():
    return random.uniform(-1.0, 1.0) \
        * 10.0**random.randint(-300, 300)


def random_numpy(shape, dtype, allow_nan=True,
                 allow_unicode=False,
                 object_element_dtypes=None):
    # Makes a random numpy array of the specified shape and dtype
    # string. The method is slightly different depending on the
    # type. For 'bytes', 'str', and 'object'; an array of the
    # specified size is made and then each element is set to either
    # a numpy.bytes_, numpy.str_, or some other object of any type
    # (here, it is a randomly typed random numpy array). If it is
    # any other type, then it is just a matter of constructing the
    # right sized ndarray from a random sequence of bytes (all must
    # be forced to 0 and 1 for bool). Optionally include unicode
    # characters. Optionally, for object dtypes, the allowed dtypes for
    # their elements can be given.
    if dtype == 'S':
        length = random.randint(1, max_string_length)
        data = np.zeros(shape=shape, dtype='S' + str(length))
        for index, x in np.ndenumerate(data):
            if allow_unicode:
                chars = random_bytes_fullrange(length)
            else:
                chars = random_bytes(length)
            data[index] = np.bytes_(chars)
        return data
    elif dtype == 'U':
        length = random.randint(1, max_string_length)
        data = np.zeros(shape=shape, dtype='U' + str(length))
        for index, x in np.ndenumerate(data):
            if allow_unicode:
                chars = random_str_some_unicode(length)
            else:
                chars = random_str_ascii(length)
            data[index] = np.unicode_(chars)
        return data
    elif dtype == 'object':
        if object_element_dtypes is None:
            object_element_dtypes = dtypes
        data = np.zeros(shape=shape, dtype='object')
        for index, x in np.ndenumerate(data):
            data[index] = random_numpy( \
                shape=random_numpy_shape( \
                object_subarray_dimensions, \
                max_object_subarray_axis_length), \
                dtype=random.choice(object_element_dtypes))
        return data
    else:
        nbytes = np.ndarray(shape=(1,), dtype=dtype).nbytes
        bts = np.random.bytes(nbytes * np.prod(shape))
        if dtype == 'bool':
            bts = b''.join([{True: b'\x01', False: b'\x00'}[ \
                ch > 127] for ch in bts])
        data = np.ndarray(shape=shape, dtype=dtype, buffer=bts)
        # If it is a floating point type and we are supposed to
        # remove NaN's, then turn them to zeros. Numpy will throw
        # RuntimeWarnings for some NaN values, so those warnings need to
        # be caught and ignored.
        if not allow_nan and data.dtype.kind in ('f', 'c'):
            data = data.copy()
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', RuntimeWarning)
                if data.dtype.kind == 'f':
                    data[np.isnan(data)] = 0.0
                else:
                    data.real[np.isnan(data.real)] = 0.0
                    data.imag[np.isnan(data.imag)] = 0.0
        return data


def random_numpy_scalar(dtype, object_element_dtypes=None):
    # How a random scalar is made depends on th type. For must, it
    # is just a single number. But for the string types, it is a
    # string of any length.
    if dtype == 'S':
        return np.bytes_(random_bytes(random.randint(1,
                         max_string_length)))
    elif dtype == 'U':
        return np.unicode_(random_str_ascii(
                           random.randint(1,
                           max_string_length)))
    else:
        return random_numpy(tuple(), dtype, \
            object_element_dtypes=object_element_dtypes)[()]


def random_numpy_shape(dimensions, max_length, min_length=1):
    # Makes a random shape tuple having the specified number of
    # dimensions. The maximum size along each axis is max_length.
    return tuple([random.randint(min_length, max_length)
                  for x in range(0, dimensions)])


def random_list(N, python_or_numpy='numpy'):
    # Makes a random list of the specified type. If instructed, it
    # will be composed entirely from random numpy arrays (make a
    # random object array and then convert that to a
    # list). Otherwise, it will be a list of random bytes.
    if python_or_numpy == 'numpy':
        return random_numpy((N,), dtype='object').tolist()
    else:
        data = []
        for i in range(0, N):
            data.append(random_bytes(random.randint(1,
                        max_string_length)))
        return data


def random_slice():
    # Make a random slice, whose parts could be None or int.
    parts = []
    for i in range(3):
        if random.choice((True, False)):
            parts.append(None)
        elif random.choice((True, False)):
            parts.append(random.randint(-2**30, 2**30))
        else:
            parts.append(random.randint(-2**128, 2**128))
    return slice(*parts)


def random_range():
    # Make a random range. The last element must not be zero.
    parts = []
    for i in range(3):
        if random.choice((True, False)):
            parts.append(random.randint(-2**30, 2**30))
        else:
            parts.append(random.randint(-2**128, 2**128))
    while parts[-1] == 0:
        if random.choice((True, False)):
            parts[-1] = random.randint(-2**30, 2**30)
        else:
            parts[-1] = random.randint(-2**128, 2**128)
    return range(*parts)


def random_fraction():
    return fractions.Fraction(numerator=random.randint(-2**65, 2**65),
                              denominator=random.randint(-2**65, 2**65))


def random_dict(tp='dict'):
    # Makes a random dict or dict-like object tp (random number of
    # randomized keys with random numpy arrays as values). The only
    # supported values of tp are 'dict', 'OrderedDict', and 'Counter'.
    data = dict()
    for i in range(0, random.randint(min_dict_keys, \
            max_dict_keys)):
        name = random_str_ascii(max_dict_key_length)
        if tp == 'Counter':
            data[name] = random.randint(-2**65, 2**65)
        else:
            data[name] = \
                random_numpy(random_numpy_shape( \
                dict_value_subarray_dimensions, \
                max_dict_value_subarray_axis_length), \
                dtype=random.choice(dtypes))

    # If tp is 'dict', return as is. If it is a Counter, we need to
    # convert it. If it is an OrderedDict, we need to randomize the order.
    if tp == 'dict':
        return data
    elif tp == 'Counter':
        return collections.Counter(data)
    elif tp == 'OrderedDict':
        # An ordered dict is made by randomizing the field order.
        itms = list(data.items())
        random.shuffle(itms)
        return collections.OrderedDict(itms)
    else:
        return data


def random_chainmap():
    # Make list of random dicts and pass them.
    return collections.ChainMap(
        *[random_dict(random.choice(('dict', 'OrderedDict', 'Counter')))
          for i in range(random.randint(3, 8))])


def random_structured_numpy_array(shape, field_shapes=None,
                                  nonascii_fields=False,
                                  nondigits_fields=False,
                                  names=None):
    # Make random field names (if not provided with field names),
    # dtypes, and sizes. Though, if field_shapes is explicitly given,
    # the sizes should be random. The field names must all be of type
    # str, not unicode in Python 2. Optionally include non-ascii
    # characters in the field names (will have to be encoded in Python
    # 2.x). String types will not be used due to the difficulty in
    # assigning the length.
    if names is None:
        if nonascii_fields:
            name_func = random_str_some_unicode
        elif nondigits_fields:
            name_func = random_str_ascii_letters
        else:
            name_func = random_str_ascii
        names = [name_func(
                 max_structured_ndarray_field_lengths)
                 for i in range(0, random.randint(
                 min_structured_ndarray_fields,
                 max_structured_ndarray_fields))]
    dts = [random.choice(list(set(dtypes)
           - set(('S', 'U'))))
           for i in range(len(names))]
    if field_shapes is None:
        shapes = [random_numpy_shape(
                  structured_ndarray_subarray_dimensions,
                  max_structured_ndarray_subarray_axis_length)
                  for i in range(len(names))]
    else:
        shapes = [field_shapes] * len(names)
    # Construct the type of the whole thing.
    dt = np.dtype([(names[i], dts[i], shapes[i])
                  for i in range(len(names))])
    # Make the array. If dt.itemsize is 0, then we need to make an
    # array of int8's the size in shape and convert it to work
    # around a numpy bug. Otherwise, we will just create an empty
    # array and then proceed by assigning each field.
    if dt.itemsize == 0:
        return np.zeros(shape=shape, dtype='int8').astype(dt)
    else:
        data = np.empty(shape=shape, dtype=dt)
        for index, x in np.ndenumerate(data):
            for i, name in enumerate(names):
                data[name][index] = random_numpy(shapes[i], \
                    dts[i], allow_nan=False)
        return data


def random_datetime_timezone():
    # Timezones must be a round number of minutes before python 3.7.
    if sys.hexversion < 0x3070000:
        mult = 60
        bound = 24 * 60
    else:
        mult = 1
        bound = 24 * 60**2
    if random.choice((True, False)):
        return datetime.timezone(
            datetime.timedelta(
                seconds=mult * random.randint(-bound, bound)),
            name=random_str_some_unicode(10))
    else:
        return datetime.timezone(
            datetime.timedelta(
                seconds=mult * random.randint(-bound, bound)))


def random_name():
    # Makes a random POSIX path of a random depth.
    depth = random.randint(1, max_posix_path_depth)
    path = '/'
    for i in range(0, depth):
        path = posixpath.join(path, random_str_ascii(
                              random.randint(1,
                              max_posix_path_lengths)))
    return path
