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
import tempfile

import numpy as np

import h5py

import hdf5storage
from hdf5storage.utilities import escape_path

from nose.tools import assert_equal as assert_equal_nose

from asserts import *
from make_randoms import *

random.seed()



# Need a list of dict-like types, which will depend on Python
# version. dict is in all of them, but OrderedDict is only in Python >=
# 2.7.
dict_like = ['dict']
if sys.hexversion >= 0x2070000:
    dict_like += ['OrderedDict']

# Need a list of previously invalid characters, which will depend on the
# Python version.
if sys.hexversion >= 0x3000000:
    invalid_characters = ('\x00', '/')
else:
    invalid_characters = (unicode('\x00'), unicode('/'))


def check_all_valid_str_keys(tp, option_keywords):
    options = hdf5storage.Options(**option_keywords)
    key_value_names = (options.dict_like_keys_name,
                       options.dict_like_values_name)

    data = random_dict(tp)
    for k in key_value_names:
        if k in data:
            del data[k]

    # Make a random name.
    name = random_name()

    # Write the data to the proper file with the given name with the
    # provided options. The file needs to be deleted after to keep junk
    # from building up.
    fld = None
    try:
        fld = tempfile.mkstemp()
        os.close(fld[0])
        filename = fld[1]
        hdf5storage.write(data, path=name, filename=filename,
                          options=options)

        with h5py.File(filename) as f:
            for k in key_value_names:
                assert escape_path(k) not in f[name]
            for k in data:
                assert escape_path(k) in f[name]
    except:
        raise
    finally:
        if fld is not None:
            os.remove(fld[1])


def check_str_key_previously_invalid_char(tp, ch, option_keywords):
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

    # Write the data to the proper file with the given name with the
    # provided options. The file needs to be deleted after to keep junk
    # from building up.
    fld = None
    try:
        fld = tempfile.mkstemp()
        os.close(fld[0])
        filename = fld[1]
        hdf5storage.write(data, path=name, filename=filename,
                          options=options)

        with h5py.File(filename) as f:
            for k in key_value_names:
                assert escape_path(k) not in f[name]
            for k in data:
                assert escape_path(k) in f[name]
    except:
        raise
    finally:
        if fld is not None:
            os.remove(fld[1])


def check_string_type_non_str_key(tp, other_tp, option_keywords):
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

    # Write the data to the proper file with the given name with the
    # provided options. The file needs to be deleted after to keep junk
    # from building up.
    fld = None
    try:
        fld = tempfile.mkstemp()
        os.close(fld[0])
        filename = fld[1]
        hdf5storage.write(data, path=name, filename=filename,
                          options=options)

        with h5py.File(filename) as f:
            assert_equal_nose(set(keys), set(f[name].keys()))

    except:
        raise
    finally:
        if fld is not None:
            os.remove(fld[1])


def check_int_key(tp, option_keywords):
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

    # Write the data to the proper file with the given name with the
    # provided options. The file needs to be deleted after to keep junk
    # from building up.
    fld = None
    try:
        fld = tempfile.mkstemp()
        os.close(fld[0])
        filename = fld[1]
        hdf5storage.write(data, path=name, filename=filename,
                          options=options)

        with h5py.File(filename) as f:
            assert_equal_nose(set(key_value_names), set(f[name].keys()))
    except:
        raise
    finally:
        if fld is not None:
            os.remove(fld[1])


def test_all_valid_str_keys():
    # generate some random keys_values_names
    keys_values_names = [('keys', 'values')]
    for i in range(3):
        names = ('a', 'a')
        while names[0] == names[1]:
            names = [random_str_ascii(8) for i in range(2)]
        keys_values_names.append(names)
    for pyth_meta in (True, False):
        for mat_meta in (True, False):
            for tp in dict_like:
                for names in keys_values_names:
                    options_keywords = { \
                        'store_python_metadata': pyth_meta, \
                        'matlab_compatible': mat_meta, \
                        'dict_like_keys_name': names[0], \
                        'dict_like_values_name': names[1]}
                    yield check_all_valid_str_keys, tp, options_keywords


def test_str_key_previously_invalid_char():
    # generate some random keys_values_names
    keys_values_names = [('keys', 'values')]
    for i in range(3):
        names = ('a', 'a')
        while names[0] == names[1]:
            names = [random_str_ascii(8) for i in range(2)]
        keys_values_names.append(names)
    for pyth_meta in (True, False):
        for mat_meta in (True, False):
            for tp in dict_like:
                for c in invalid_characters:
                    for names in keys_values_names:
                        options_keywords = { \
                            'store_python_metadata': pyth_meta, \
                            'matlab_compatible': mat_meta, \
                            'dict_like_keys_name': names[0], \
                            'dict_like_values_name': names[1]}
                        yield check_str_key_previously_invalid_char, tp, c, options_keywords


def test_string_type_non_str_key():
    # Set the other key types.
    other_tps = ['bytes', 'numpy.bytes_', 'numpy.unicode_']
    # generate some random keys_values_names
    keys_values_names = [('keys', 'values')]
    for i in range(1):
        names = ('a', 'a')
        while names[0] == names[1]:
            names = [random_str_ascii(8) for i in range(2)]
        keys_values_names.append(names)
    for pyth_meta in (True, False):
        for mat_meta in (True, False):
            for tp in dict_like:
                for other_tp in other_tps:
                    for names in keys_values_names:
                        options_keywords = { \
                            'store_python_metadata': pyth_meta, \
                            'matlab_compatible': mat_meta, \
                            'dict_like_keys_name': names[0], \
                            'dict_like_values_name': names[1]}
                    yield check_string_type_non_str_key, tp, other_tp, options_keywords


def test_int_key():
    # generate some random keys_values_names
    keys_values_names = [('keys', 'values')]
    for i in range(3):
        names = ('a', 'a')
        while names[0] == names[1]:
            names = [random_str_ascii(8) for i in range(2)]
        keys_values_names.append(names)
    for pyth_meta in (True, False):
        for mat_meta in (True, False):
            for tp in dict_like:
                for names in keys_values_names:
                    options_keywords = { \
                        'store_python_metadata': pyth_meta, \
                        'matlab_compatible': mat_meta, \
                        'dict_like_keys_name': names[0], \
                        'dict_like_values_name': names[1]}
                    yield check_int_key, tp, options_keywords
