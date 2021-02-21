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

import os.path
import random
import tempfile

import numpy as np

import h5py

import pytest

import hdf5storage
from hdf5storage.pathesc import escape_path


from make_randoms import random_name, random_dict, random_int, \
    random_str_ascii, random_str_some_unicode, max_dict_key_length

random.seed()



# Need a list of dict-like types, which will depend on Python
# version.
dict_like = ['dict', 'OrderedDict']

# Need a list of previously invalid characters.
invalid_characters = ('\x00', '/')

# Generate a bunch of random key_values_names.
keys_values_names = [('keys', 'values')]
for i in range(5):
    names = ('a', 'a')
    while names[0] == names[1]:
        names = [random_str_ascii(8) for i in range(2)]
    keys_values_names.append(names)

# Set the other key types.
other_key_types = ('bytes', 'numpy.bytes_', 'numpy.unicode_')


@pytest.mark.parametrize(
    'tp,option_keywords',
    [(tp, {'store_python_metadata': pyth_meta,
           'matlab_compatible': mat_meta,
           'dict_like_keys_name': names[0],
           'dict_like_values_name': names[1]})
     for tp in dict_like
     for pyth_meta in (True, False)
     for mat_meta in (True, False)
     for names in keys_values_names])
def test_all_valid_str_keys(tp, option_keywords):
    options = hdf5storage.Options(**option_keywords)
    key_value_names = (options.dict_like_keys_name,
                       options.dict_like_values_name)

    data = random_dict(tp)
    for k in key_value_names:
        if k in data:
            del data[k]

    # Make a random name.
    name = random_name()

    # Write the data to the file with the given name with the provided
    # options.
    with tempfile.TemporaryDirectory() as folder:
        filename = os.path.join(folder, 'data.h5')
        hdf5storage.write(data, path=name, filename=filename,
                          options=options)

        with h5py.File(filename, mode='r') as f:
            for k in key_value_names:
                assert escape_path(k) not in f[name]
            for k in data:
                assert escape_path(k) in f[name]


@pytest.mark.parametrize(
    'tp,ch,option_keywords',
    [(tp, ch, {'store_python_metadata': pyth_meta,
               'matlab_compatible': mat_meta,
               'dict_like_keys_name': names[0],
               'dict_like_values_name': names[1]})
     for tp in dict_like
     for pyth_meta in (True, False)
     for mat_meta in (True, False)
     for ch in invalid_characters
     for names in keys_values_names])
def test_str_key_previously_invalid_char(tp, ch, option_keywords):
    options = hdf5storage.Options(**option_keywords)
    key_value_names = (options.dict_like_keys_name,
                       options.dict_like_values_name)

    data = random_dict(tp)
    for k in key_value_names:
        if k in data:
            del data[k]

    # Add a random invalid str key using the provided character
    key = key_value_names[0]
    while key in key_value_names:
        key = ch.join([random_str_ascii(max_dict_key_length)
                      for i in range(2)])
    data[key] = random_int()

    # Make a random name.
    name = random_name()

    # Write the data to the file with the given name with the provided
    # options.
    with tempfile.TemporaryDirectory() as folder:
        filename = os.path.join(folder, 'data.h5')
        hdf5storage.write(data, path=name, filename=filename,
                          options=options)

        with h5py.File(filename, mode='r') as f:
            for k in key_value_names:
                assert escape_path(k) not in f[name]
            for k in data:
                assert escape_path(k) in f[name]


@pytest.mark.parametrize(
    'tp,other_tp,option_keywords',
    [(tp, otp, {'store_python_metadata': pyth_meta,
                'matlab_compatible': mat_meta,
                'dict_like_keys_name': names[0],
                'dict_like_values_name': names[1]})
     for tp in dict_like
     for pyth_meta in (True, False)
     for mat_meta in (True, False)
     for otp in other_key_types
     for names in keys_values_names])
def test_string_type_non_str_key(tp, other_tp, option_keywords):
    options = hdf5storage.Options(**option_keywords)
    key_value_names = (options.dict_like_keys_name,
                       options.dict_like_values_name)

    data = random_dict(tp)
    for k in key_value_names:
        if k in data:
            del data[k]
    keys = list(data.keys())

    key_gen = random_str_some_unicode(max_dict_key_length)
    if other_tp == 'numpy.bytes_':
        key = np.bytes_(key_gen.encode('UTF-8'))
    elif other_tp == 'numpy.unicode_':
        key = np.unicode_(key_gen)
    elif other_tp == 'bytes':
        key = key_gen.encode('UTF-8')
    data[key] = random_int()
    keys.append(key_gen)

    # Make a random name.
    name = random_name()

    # Write the data to the file with the given name with the provided
    # options.
    with tempfile.TemporaryDirectory() as folder:
        filename = os.path.join(folder, 'data.h5')
        hdf5storage.write(data, path=name, filename=filename,
                          options=options)

        with h5py.File(filename, mode='r') as f:
            assert set(keys) == set(f[name].keys())


@pytest.mark.parametrize(
    'tp,option_keywords',
    [(tp, {'store_python_metadata': pyth_meta,
           'matlab_compatible': mat_meta,
           'dict_like_keys_name': names[0],
           'dict_like_values_name': names[1]})
     for tp in dict_like
     for pyth_meta in (True, False)
     for mat_meta in (True, False)
     for names in keys_values_names])
def test_int_key(tp, option_keywords):
    options = hdf5storage.Options(**option_keywords)
    key_value_names = (options.dict_like_keys_name,
                       options.dict_like_values_name)

    data = random_dict(tp)
    for k in key_value_names:
        if k in data:
            del data[k]

    key = random_int()
    data[key] = random_int()

    # Make a random name.
    name = random_name()

    # Write the data to the file with the given name with the provided
    # options.
    with tempfile.TemporaryDirectory() as folder:
        filename = os.path.join(folder, 'data.h5')
        hdf5storage.write(data, path=name, filename=filename,
                          options=options)

        with h5py.File(filename, mode='r') as f:
            assert set(key_value_names) == set(f[name].keys())
