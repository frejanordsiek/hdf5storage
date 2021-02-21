# Copyright (c) 2013-2021, Freja Nordsiek
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
import itertools
import math
import os.path
import pathlib
import posixpath
import random
import string
import warnings
import tempfile

import numpy as np

import pytest

import hdf5storage

from asserts import assert_equal, assert_equal_none_format, \
    assert_equal_matlab_format
from make_randoms import random_numpy_scalar, random_numpy_shape, \
    random_numpy, random_name, max_array_axis_length, \
    max_structured_ndarray_axis_length, random_structured_numpy_array, \
    random_str_ascii, max_dict_key_length, \
    random_list, max_list_length, random_dict, \
    random_str_some_unicode, random_int, random_float, \
    max_string_length, random_bytes, random_slice, random_range, \
    random_chainmap, random_fraction, random_datetime_timezone


random.seed()


# The formats.
fmts = ('PythonMatlab', 'Python', 'Matlab', 'None')

# Need a list of the supported numeric dtypes to test, excluding those
# not supported by MATLAB. 'S' and 'U' dtype chars have to be used for
# the bare byte and unicode string dtypes since the dtype strings (but
# not chars) are not the same in Python 2 and 3. Then make a list that
# is the same but also has those that are not supported by matlab.
dtypes_mat = ['bool', 'uint8', 'uint16', 'uint32', 'uint64',
              'int8', 'int16', 'int32', 'int64',
              'float32', 'float64', 'complex64', 'complex128',
              'S', 'U']
dtypes_non_mat = dtypes_mat + ['float16']

# Make a lookup for the dtypes and assertion function to use given the
# format.
dtypes_by_option = {'PythonMatlab': dtypes_mat,
                    'Python': dtypes_non_mat,
                    'Matlab': dtypes_mat,
                    'None': dtypes_non_mat}

assert_equal_by_option = {'PythonMatlab': assert_equal,
                          'Python': assert_equal,
                          'Matlab': assert_equal_matlab_format,
                          'None': assert_equal_none_format}

# Need a list of dict-like types.
dict_like = ('dict', 'OrderedDict', 'Counter')

# Need base dtypes of structured dtype tests.
base_dtypes = tuple((set(dtypes_non_mat) | {'U2', 'S3'}) - {'U', 'S'})


# A fixture of the Options to use depending on the format.
options_by_format = dict()

@pytest.fixture(scope="module", autouse=True)
def get_options():
    options_by_format.update(
        {
            'PythonMatlab': hdf5storage.Options(
                store_python_metadata=True, matlab_compatible=True),
            'Python': hdf5storage.Options(
                store_python_metadata=True, matlab_compatible=False),
            'Matlab': hdf5storage.Options(
                store_python_metadata=False, matlab_compatible=True),
            'None': hdf5storage.Options(
                store_python_metadata=False, matlab_compatible=False)})


# Function to write and then readback and optionall check everything
# with the appropriate assert_equal.
def write_readback(fmt, data, name=None, write_options=None,
                   read_options=None, check=True):
    # Use the default options for writing and reading if they are not
    # given.
    if write_options is None:
        write_options = options_by_format[fmt]
    if read_options is None:
        read_options = options_by_format[fmt]
    # Make a default name if one wasn't given.
    if name is None:
        name = random_name()
    # Randomly convert the name to other path types.
    path_choices = (str, bytes,
                    pathlib.PurePath,
                    pathlib.PurePosixPath,
                    pathlib.PureWindowsPath,
                    pathlib.Path)
    name_type_w = random.choice(path_choices)
    name_type_r = random.choice(path_choices)
    # Name to write with.
    if name_type_w == bytes:
        name_w = name.encode('utf-8')
    elif name_type_w in (pathlib.PurePath, pathlib.PurePosixPath,
                         pathlib.PosixPath):
        name_w = name_type_w(name)
    elif name_type_w != str:
        name_w = name_type_w(name[posixpath.isabs(name):])
    else:
        name_w = name
    # Name to read with.
    if name_type_r == bytes:
        name_r = name.encode('utf-8')
    elif name_type_r in (pathlib.PurePath, pathlib.PurePosixPath,
                         pathlib.PosixPath):
        name_r = name_type_r(name)
    elif name_type_r != str:
        name_r = name_type_r(name[posixpath.isabs(name):])
    else:
        name_r = name
    # Write the data to the file with the given name, read it back, and
    # return the result. The file needs to be deleted after to keep junk
    # from building up. Different options can be used for reading the
    # data back.
    with tempfile.TemporaryDirectory() as folder:
        filename = os.path.join(folder, 'data.h5')
        hdf5storage.write(data, path=name_w, filename=filename,
                          options=write_options)
        out = hdf5storage.read(path=name_r, filename=filename,
                               options=read_options)
    if check:
        assert_equal_by_option[fmt](out, data, options_by_format[fmt])
    return out


@pytest.mark.parametrize('fmt,dtype',
                         {(fmt, dt) for fmt in fmts
                          for dt in dtypes_by_option[fmt]})
def test_numpy_scalar(fmt, dtype):
    # Makes a random numpy scalar of the given type, writes it and
    # reads it back, and then compares it.
    data = random_numpy_scalar(dtype)
    write_readback(fmt, data)


@pytest.mark.parametrize('fmt,dtype,dimensions',
                         {(fmt, dt, dims) for fmt in fmts
                          for dt in dtypes_by_option[fmt]
                          for dims in range(1, 4)})
def test_numpy_array(fmt, dtype, dimensions):
    # Makes a random numpy array of the given type, writes it and
    # reads it back, and then compares it.
    shape = random_numpy_shape(dimensions,
                               max_array_axis_length)
    data = random_numpy(shape, dtype)
    write_readback(fmt, data)


@pytest.mark.parametrize('fmt,dtype',
                         {(fmt, dt) for fmt in fmts
                          for dt in dtypes_by_option[fmt]})
def test_numpy_empty(fmt, dtype):
    # Makes an empty numpy array of the given type, writes it and
    # reads it back, and then compares it.
    data = np.array([], dtype)
    write_readback(fmt, data)


@pytest.mark.parametrize('fmt,dtype,num_chars',
                         {(fmt, dt, n) for fmt in fmts
                          for dt in 'SU'
                          for n in range(1, 10)})
def test_numpy_stringlike_empty(fmt, dtype, num_chars):
    # Makes an empty stringlike numpy array of the given type and
    # size, writes it and reads it back, and then compares it.
    data = np.array([], dtype + str(num_chars))
    write_readback(fmt, data)


@pytest.mark.parametrize('fmt,dimensions',
                         {(fmt, dims) for fmt in fmts
                          for dims in range(1, 4)})
def test_numpy_structured_array(fmt, dimensions):
    # Makes a random structured ndarray of the given type, writes it
    # and reads it back, and then compares it.
    shape = random_numpy_shape(dimensions, \
        max_structured_ndarray_axis_length)
    data = random_structured_numpy_array(shape)
    write_readback(fmt, data)


@pytest.mark.parametrize('fmt,dimensions',
                         {(fmt, dims) for fmt in fmts
                          for dims in range(1, 4)})
def test_numpy_structured_array_empty(fmt, dimensions):
    # Makes a random structured ndarray of the given type, writes it
    # and reads it back, and then compares it.
    shape = random_numpy_shape(dimensions, \
        max_structured_ndarray_axis_length)
    data = random_structured_numpy_array(shape, (1, 0))
    write_readback(fmt, data)


@pytest.mark.parametrize('fmt', fmts)
def test_numpy_structured_array_unicode_fields(fmt):
    # Makes a random 1d structured ndarray with non-ascii characters
    # in its fields, writes it and reads it back, and then compares
    # it.
    shape = random_numpy_shape(1, \
        max_structured_ndarray_axis_length)
    data = random_structured_numpy_array(shape, \
        nonascii_fields=True).view(np.recarray).copy()
    write_readback(fmt, data)


@pytest.mark.parametrize('fmt,ch',
                         {(fmt, ch) for fmt in fmts
                          for ch in
                          ['\x00', '/', '\\']
                          + [i * '.' for i in range(1, 10)]})
def test_numpy_structured_array_field_special_char(fmt, ch):
    # Makes a random 1d structured ndarray with the character
    # in one field, writes it and reads it back, and then compares
    # it. It will be leading if it begins with a dot.
    field_names = [random_str_ascii(max_dict_key_length)
                   for i in range(2)]
    if ch[0] == '.':
        field_names[1] = ch + field_names[1]
    else:
        field_names[1] = field_names[1][0] + ch + field_names[1][1:]
    field_names[1] = field_names[1][0] + ch + field_names[1][1:]
    shape = random_numpy_shape(1, \
        max_structured_ndarray_axis_length)
    data = random_structured_numpy_array(shape, names=field_names)
    write_readback(fmt, data)


@pytest.mark.skipif(not hasattr(np, 'matrix'),
                    reason='numpy.matrix class has been removed.')
@pytest.mark.parametrize('fmt,dtype',
                         {(fmt, dt) for fmt in fmts
                          for dt in dtypes_by_option[fmt]})
def test_numpy_matrix(fmt, dtype):
    # Makes a random numpy array of the given type, converts it to
    # a matrix, writes it and reads it back, and then compares it.
    shape = random_numpy_shape(2, max_array_axis_length)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', (PendingDeprecationWarning,
                                         DeprecationWarning))
        data = np.matrix(random_numpy(shape, dtype))
    write_readback(fmt, data)


@pytest.mark.parametrize('fmt,dimensions',
                         {(fmt, dims) for fmt in fmts
                          for dims in range(1, 4)})
def test_numpy_recarray(fmt, dimensions):
    # Makes a random structured ndarray of the given type, converts
    # it to a recarray, writes it and reads it back, and then
    # compares it.
    shape = random_numpy_shape(dimensions, \
        max_structured_ndarray_axis_length)
    data = random_structured_numpy_array(shape).view(np.recarray).copy()
    write_readback(fmt, data)


@pytest.mark.parametrize('fmt,dimensions',
                         {(fmt, dims) for fmt in fmts
                          for dims in range(1, 4)})
def test_numpy_recarray_empty(fmt, dimensions):
    # Makes a random structured ndarray of the given type, converts
    # it to a recarray, writes it and reads it back, and then
    # compares it.
    shape = random_numpy_shape(dimensions, \
        max_structured_ndarray_axis_length)
    data = random_structured_numpy_array(shape, (1, 0)).view(np.recarray).copy()
    write_readback(fmt, data)


@pytest.mark.parametrize('fmt', fmts)
def test_numpy_recarray_unicode_fields(fmt):
    # Makes a random 1d structured ndarray with non-ascii characters
    # in its fields, converts it to a recarray, writes it and reads
    # it back, and then compares it.
    shape = random_numpy_shape(1, \
        max_structured_ndarray_axis_length)
    data = random_structured_numpy_array(shape,
                                         nonascii_fields=True)
    write_readback(fmt, data)


@pytest.mark.parametrize('fmt,ch',
                         {(fmt, ch) for fmt in fmts
                          for ch in
                          ['\x00', '/', '\\']
                          + [i * '.' for i in range(1, 10)]})
def test_numpy_recarray_field_special_char(fmt, ch):
    # Makes a random 1d structured ndarray with the character
    # in one field, converts it to a recarray, writes it and reads
    # it back, and then compares it. It will be leading if it starts
    # with a period.
    field_names = [random_str_ascii(max_dict_key_length)
                   for i in range(2)]
    if ch[0] == '.':
        field_names[1] = ch + field_names[1]
    else:
        field_names[1] = field_names[1][0] + ch + field_names[1][1:]
    shape = random_numpy_shape(1, \
        max_structured_ndarray_axis_length)
    data = random_structured_numpy_array(shape, names=field_names).view(np.recarray).copy()
    write_readback(fmt, data)


@pytest.mark.parametrize('fmt,dimensions',
                         {(fmt, dims) for fmt in fmts
                          for dims in range(1, 4)})
def test_numpy_chararray(fmt, dimensions):
    # Makes a random numpy array of bytes, converts it to a
    # chararray, writes it and reads it back, and then compares it.
    shape = random_numpy_shape(dimensions,
                               max_array_axis_length)
    data = random_numpy(shape, 'S').view(np.chararray).copy()
    write_readback(fmt, data)


@pytest.mark.parametrize('fmt,num_chars',
                         {(fmt, dims) for fmt in fmts
                          for dims in range(1, 10)})
def test_numpy_chararray_empty(fmt, num_chars):
    # Makes an empty numpy array of bytes of the given number of
    # characters, converts it to a chararray, writes it and reads it
    # back, and then compares it.
    data = np.array([], 'S' + str(num_chars)).view(np.chararray).copy()
    write_readback(fmt, data)


@pytest.mark.parametrize('fmt,zero_shaped',
                         {(fmt, z) for fmt in fmts
                          for z in (True, False)})
def test_numpy_sized_dtype_nested_0(fmt, zero_shaped):
    dtypes = ('uint8', 'uint16', 'uint32', 'uint64',
              'int8', 'int16', 'int32', 'int64',
              'float32', 'float64',
              'complex64', 'complex128')
    for i in range(10):
        dt = (random.choice(dtypes), (2, 2 * zero_shaped))
        data = np.zeros((2, ), dtype=dt)
        write_readback(fmt, data)


@pytest.mark.parametrize('fmt,zero_shaped',
                         {(fmt, z) for fmt in fmts
                          for z in (True, False)})
def test_numpy_sized_dtype_nested_1(fmt, zero_shaped):
    dtypes = ('uint8', 'uint16', 'uint32', 'uint64',
              'int8', 'int16', 'int32', 'int64',
              'float32', 'float64',
              'complex64', 'complex128')
    for i in range(10):
        dt = [('a', random.choice(dtypes), (1, 2)),
              ('b', random.choice(dtypes), (1, 1, 4 * zero_shaped)),
              ('c',
               [('a', random.choice(dtypes)),
                ('b', random.choice(dtypes), (1, 2))])]
        data = np.zeros((random.randrange(1, 4), ), dtype=dt)
        write_readback(fmt, data)


@pytest.mark.parametrize('fmt,zero_shaped',
                         {(fmt, z) for fmt in fmts
                          for z in (True, False)})
def test_numpy_sized_dtype_nested_2(fmt, zero_shaped):
    dtypes = ('uint8', 'uint16', 'uint32', 'uint64',
              'int8', 'int16', 'int32', 'int64',
              'float32', 'float64',
              'complex64', 'complex128')
    for i in range(10):
        dt = [('a', random.choice(dtypes), (1, 3)),
              ('b',
               [('a', random.choice(dtypes), (2, )),
                ('b', random.choice(dtypes), (1, 2, 1))]),
              ('c',
               [('a', random.choice(dtypes),
                 (3 * zero_shaped, 1)),
                ('b', random.choice(dtypes), (2, ))], (2, 1))]
        data = np.zeros((2, ), dtype=dt)
        write_readback(fmt, data)


@pytest.mark.parametrize('fmt,zero_shaped',
                         {(fmt, z) for fmt in fmts
                          for z in (True, False)})
def test_numpy_sized_dtype_nested_3(fmt, zero_shaped):
    dtypes = ('uint8', 'uint16', 'uint32', 'uint64',
              'int8', 'int16', 'int32', 'int64',
              'float32', 'float64',
              'complex64', 'complex128')
    for i in range(10):
        dt = [('a', random.choice(dtypes), (3, 2)),
              ('b',
               [('a',
                 [('a', random.choice(dtypes))],
                 (2, 2)),
                ('b', random.choice(dtypes), (1, 2))]),
              ('c',
               [('a',
                 [('a', random.choice(dtypes),
                   (2, 1, zero_shaped * 2))]),
                ('b', random.choice(dtypes))])]
        data = np.zeros((1, ), dtype=dt)
        write_readback(fmt, data)


@pytest.mark.parametrize('fmt,tp,same_dims',
                         {(fmt, tp, s) for fmt in fmts
                          for tp in (list, tuple, set, frozenset,
                                     collections.deque)
                          for s in ('same-dims', 'diff-dims')})
def test_python_collection(fmt, tp, same_dims):
    # Makes a random collection of the specified type, writes it and
    # reads it back, and then compares it.
    if tp in (set, frozenset):
        data = tp(random_list(max_list_length,
                  python_or_numpy='python'))
    else:
        if same_dims == 'same-dims':
            shape = random_numpy_shape(random.randrange(2, 4),
                                       random.randrange(1, 4))
            dtypes = ('uint8', 'uint16', 'uint32', 'uint64',
                      'int8', 'int16', 'int32', 'int64',
                      'float32', 'float64',
                      'complex64', 'complex128')
            data = tp([random_numpy(shape, random.choice(dtypes),
                                    allow_nan=True)
                       for i in range(random.randrange(2, 7))])

        elif same_dims == 'diff-dims':
            data = tp(random_list(max_list_length,
                                  python_or_numpy='numpy'))
        else:
            raise ValueError('invalid value of same_dims')
    write_readback(fmt, data)


@pytest.mark.parametrize('fmt,tp', {(fmt, tp) for fmt in fmts
                                    for tp in dict_like})
def test_dict_like(fmt, tp):
    data = random_dict(tp)
    write_readback(fmt, data)


@pytest.mark.parametrize('fmt,tp,other_tp',
                         {(fmt, tp, otp) for fmt in fmts
                          for tp in dict_like
                          for otp in ('bytes', 'numpy.bytes_',
                                      'numpy.unicode_',
                                      'int', 'float')})
def test_dict_like_other_type_key(fmt, tp, other_tp):
    data = random_dict(tp)

    key_gen = random_str_some_unicode(max_dict_key_length)
    if other_tp == 'numpy.bytes_':
        key = np.bytes_(key_gen.encode('UTF-8'))
    elif other_tp == 'numpy.unicode_':
        key = np.unicode_(key_gen)
    elif other_tp == 'bytes':
        key = key_gen.encode('UTF-8')
    elif other_tp == 'int':
        key = random_int()
    elif other_tp == 'float':
        key = random_float()

    data[key] = random_int()
    write_readback(fmt, data)


@pytest.mark.parametrize('fmt,tp', {(fmt, tp) for fmt in fmts
                                    for tp in dict_like})
def test_dict_like_key_null_character(fmt, tp):
    data = random_dict(tp)
    ch = '\x00'
    key = ch.join([random_str_ascii(max_dict_key_length)
                  for i in range(2)])
    data[key] = random_int()
    write_readback(fmt, data)


@pytest.mark.parametrize('fmt,tp', {(fmt, tp) for fmt in fmts
                                    for tp in dict_like})
def test_dict_like_key_forward_slash(fmt, tp):
    data = random_dict(tp)
    ch = '/'
    key = ch.join([random_str_ascii(max_dict_key_length)
                  for i in range(2)])
    data[key] = random_int()
    write_readback(fmt, data)


@pytest.mark.parametrize('fmt,tp', {(fmt, tp) for fmt in fmts
                                    for tp in dict_like})
def test_dict_like_key_back_slash(fmt, tp):
    data = random_dict(tp)
    ch = '\\'
    key = ch.join([random_str_ascii(max_dict_key_length)
                  for i in range(2)])
    data[key] = random_int()
    write_readback(fmt, data)


@pytest.mark.parametrize('fmt,tp', {(fmt, tp) for fmt in fmts
                                    for tp in dict_like})
def test_dict_like_key_leading_periods(fmt, tp):
    data = random_dict(tp)
    prefix = '.' * random.randint(1, 10)
    key = prefix + random_str_ascii(max_dict_key_length)
    data[key] = random_int()
    write_readback(fmt, data)


@pytest.mark.parametrize('fmt', fmts)
def test_None(fmt):
    data = None
    write_readback(fmt, data, random_name())


@pytest.mark.parametrize('fmt', fmts)
def test_Ellipsis(fmt):
    data = Ellipsis
    write_readback(fmt, data)


@pytest.mark.parametrize('fmt', fmts)
def test_NotImplemented(fmt):
    data = NotImplemented
    write_readback(fmt, data)


@pytest.mark.parametrize('fmt', fmts)
def test_bool_True(fmt):
    data = True
    write_readback(fmt, data)


@pytest.mark.parametrize('fmt', fmts)
def test_bool_False(fmt):
    data = False
    write_readback(fmt, data)


@pytest.mark.parametrize('fmt', fmts)
def test_int_needs_32_bits(fmt):
    data = random_int()
    write_readback(fmt, data)


@pytest.mark.parametrize('fmt', fmts)
def test_int_needs_64_bits(fmt):
    data = (2**32) * random_int()
    write_readback(fmt, data)


@pytest.mark.parametrize('fmt', fmts)
def test_int_or_long_too_big(fmt):
    data = 2**64 * random_int()
    write_readback(fmt, data)


@pytest.mark.parametrize('fmt', fmts)
def test_float(fmt):
    data = random_float()
    write_readback(fmt, data)


@pytest.mark.parametrize('fmt', fmts)
def test_float_inf(fmt):
    data = float(np.inf)
    write_readback(fmt, data)


@pytest.mark.parametrize('fmt', fmts)
def test_float_ninf(fmt):
    data = float(-np.inf)
    write_readback(fmt, data)


@pytest.mark.parametrize('fmt', fmts)
def test_float_nan(fmt):
    data = float(np.nan)
    out = write_readback(fmt, data, check=False)
    assert math.isnan(out)


@pytest.mark.parametrize('fmt', fmts)
def test_complex(fmt):
    data = random_float() + 1j*random_float()
    write_readback(fmt, data)


@pytest.mark.parametrize('fmt', fmts)
def test_complex_real_nan(fmt):
    data = complex(np.nan, random_float())
    write_readback(fmt, data)


@pytest.mark.parametrize('fmt', fmts)
def test_complex_imaginary_nan(fmt):
    data = complex(random_float(), np.nan)
    write_readback(fmt, data)


@pytest.mark.parametrize('fmt', fmts)
def test_str_ascii(fmt):
    data = random_str_ascii(random.randint(1,
                            max_string_length))
    write_readback(fmt, data)


@pytest.mark.parametrize('fmt', fmts)
def test_str_ascii_encoded_utf8(fmt):
    ltrs = string.ascii_letters + string.digits
    data = 'a'
    while all([(c in ltrs) for c in data]):
        data = random_str_some_unicode(random.randint(1, \
            max_string_length))
    data = data.encode('utf-8')
    write_readback(fmt, data)


@pytest.mark.parametrize('fmt', fmts)
def test_str_with_null(fmt):
    strs = [random_str_ascii(
            random.randint(1, max_string_length))
            for i in range(2)]
    data = '\x00'.join(strs)
    write_readback(fmt, data)


@pytest.mark.parametrize('fmt', fmts)
def test_str_unicode(fmt):
    data = random_str_some_unicode(random.randint(1,
                                   max_string_length))
    write_readback(fmt, data)


@pytest.mark.parametrize('fmt', fmts)
def test_str_empty(fmt):
    data = ''
    write_readback(fmt, data)


@pytest.mark.parametrize('fmt', fmts)
def test_bytes(fmt):
    data = random_bytes(random.randint(1,
                        max_string_length))
    write_readback(fmt, data)


@pytest.mark.parametrize('fmt', fmts)
def test_bytes_empty(fmt):
    data = b''
    write_readback(fmt, data)


@pytest.mark.parametrize('fmt', fmts)
def test_bytes_with_null(fmt):
    strs = [random_bytes(
            random.randint(1, max_string_length))
            for i in range(2)]
    data = b'\x00'.join(strs)
    write_readback(fmt, data)


@pytest.mark.parametrize('fmt', fmts)
def test_bytearray(fmt):
    data = bytearray(random_bytes(random.randint(1,
                     max_string_length)))
    write_readback(fmt, data)


@pytest.mark.parametrize('fmt', fmts)
def test_bytearray_empty(fmt):
    data = bytearray(b'')
    write_readback(fmt, data)


@pytest.mark.parametrize('fmt', fmts)
def test_slice(fmt):
    for _ in range(10):
        data = random_slice()
        write_readback(fmt, data)


@pytest.mark.parametrize('fmt', fmts)
def test_range(fmt):
    for _ in range(10):
        data = random_range()
        write_readback(fmt, data)


@pytest.mark.parametrize('fmt', fmts)
def test_chainmap(fmt):
    data = random_chainmap()
    write_readback(fmt, data)


@pytest.mark.parametrize('fmt', fmts)
def test_fraction(fmt):
    data = random_fraction()
    write_readback(fmt, data)


@pytest.mark.parametrize(
    'fmt,base_dtype',
    {(fmt, dt) for fmt in fmts
     for dt in {
             v for v
             in itertools.chain(np.sctypeDict,
                                np.sctypeDict.values())
             if not isinstance(v, int)
             and v not in ('V', 'void', 'void0', 'Void0', np.void)}})
def test_dtype(fmt, base_dtype):
    # Suppress deprecation warnings for numeric style codes.
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', (PendingDeprecationWarning,
                                         DeprecationWarning))
        dtype = np.dtype(base_dtype)
    # Do the test for all endiannesses.
    if dtype.byteorder == '|':
        write_readback(fmt, dtype)
    else:
        for byteorder in '<>':
            write_readback(fmt, dtype.newbyteorder(byteorder))


@pytest.mark.parametrize('fmt', fmts)
def test_dtype_flexible(fmt):
    for c in 'SVU':
        for i in range(10):
            if c == 'V' and i == 0:
                continue
            s = c + str(i)
            write_readback(fmt, np.dtype('<' + s))
            write_readback(fmt, np.dtype('>' + s))


@pytest.mark.parametrize('fmt,base_dtype',
                         {(fmt, dt) for fmt in fmts
                          for dt in base_dtypes})
def test_dtype_shaped(fmt, base_dtype):
    for i in range(10):
        desc = (base_dtype,
                random_numpy_shape(random.randint(1, 4), 10))
        write_readback(fmt, np.dtype(desc))


@pytest.mark.parametrize('fmt', fmts)
def test_dtype_structured(fmt):
    for i in range(10):
        names = []
        for _ in range(random.randint(1, 5)):
            s = random_str_ascii(random.randint(1, 10))
            while s in names or s[0].isdigit():
                s = random_str_ascii(random.randint(1, 10))
            names.append(s)
        desc = [(v, random.choice(base_dtypes),
                 random_numpy_shape(random.randint(1, 4), 10))
                for v in names]
        write_readback(fmt, np.dtype(desc))
        write_readback(fmt, np.dtype(desc, align=True))


@pytest.mark.parametrize('fmt', fmts)
def test_dtype_structured_with_offsets_titles(fmt):
    for i in range(10):
        names = []
        for _ in range(random.randint(1, 5)):
            s = random_str_ascii(random.randint(1, 10))
            while s in names or s[0].isdigit():
                s = random_str_ascii(random.randint(1, 10))
            names.append(s)
        titles = []
        for _ in range(len(names)):
            s = random_str_some_unicode(random.randint(1, 10))
            while s in titles or s in names:
                s = random_str_some_unicode(random.randint(1, 10))
            titles.append(s)
        formats = [(random.choice(base_dtypes),
                    random_numpy_shape(random.randint(1, 4), 10))
                   for _ in range(len(names))]
        offsets = [random.randint(0, 100)
                   for _ in range(len(names))]
        desc = {'names': names,
                'formats': formats,
                'titles': titles,
                'offsets': offsets}
        desc_with_itemsize = desc.copy()
        desc_with_itemsize['itemsize'] = \
            np.dtype(desc).itemsize + random.randint(1, 100)
        # Make the dtypes in all combinations of the description and
        # align. Note that if the type isn't valid at all, it is not
        # tested.
        dts = []
        for d in (desc, desc_with_itemsize):
            for align in (False, True):
                try:
                    dts.append(np.dtype(d, align=align))
                except:
                    pass
        for dt in dts:
            write_readback(fmt, dt)


@pytest.mark.parametrize('fmt', fmts)
def test_datetime_timedelta(fmt):
    for _ in range(10):
        data = datetime.timedelta(days=random.randint(-20, 20),
                                  seconds=random.randint(-1000,
                                                         1000),
                                  microseconds=random.randint(
                                      -1000**3, 1000**3))
        write_readback(fmt, data)


@pytest.mark.parametrize('fmt', fmts)
def test_datetime_timezone(fmt):
    for _ in range(10):
        data = random_datetime_timezone()
        write_readback(fmt, data)


@pytest.mark.parametrize('fmt', fmts)
def test_datetime_date(fmt):
    for _ in range(10):
        data = datetime.date(year=random.randint(datetime.MINYEAR,
                                                 datetime.MAXYEAR),
                             month=random.randint(1, 12),
                             day=random.randint(1, 28))
        write_readback(fmt, data)


@pytest.mark.parametrize('fmt', fmts)
def test_datetime_time(fmt):
    for _ in range(10):
        data = datetime.time(hour=random.randint(0, 23),
                             minute=random.randint(0, 59),
                             second=random.randint(0, 59),
                             microsecond=random.randint(0, 999999),
                             tzinfo=random_datetime_timezone())
        write_readback(fmt, data)


@pytest.mark.parametrize('fmt', fmts)
def test_datetime_datetime(fmt):
    for _ in range(10):
        data = datetime.datetime(
            year=random.randint(datetime.MINYEAR, datetime.MAXYEAR),
            month=random.randint(1, 12),
            day=random.randint(1, 28),
            hour=random.randint(0, 23),
            minute=random.randint(0, 59),
            second=random.randint(0, 59),
            microsecond=random.randint(0, 999999),
            tzinfo=random_datetime_timezone())
        write_readback(fmt, data)
