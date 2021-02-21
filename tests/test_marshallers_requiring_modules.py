# Copyright (c) 2016-2021, Freja Nordsiek
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
import sys
import tempfile

import numpy as np
import h5py

import hdf5storage
import hdf5storage.utilities
import hdf5storage.Marshallers


class Tmarshaller(hdf5storage.Marshallers.TypeMarshaller):
    def read(self, f, dsetgrp, attributes):
        return 'read'

    def read_approximate(self, f, dsetgrp, attributes):
        return 'read_approximate'


def test_missing_required_parent():
    m = hdf5storage.Marshallers.TypeMarshaller()
    m.required_parent_modules = ['ainivieanvueaq']
    m.python_type_strings = ['vi8vaeaniea']
    m.types = [s for s in m.python_type_strings]
    m.update_type_lookups()
    mc = hdf5storage.MarshallerCollection(marshallers=[m])
    assert mc._has_required_modules[-1] is False
    assert mc._imported_required_modules[-1] is False
    mback, has_modules = mc.get_marshaller_for_type_string( \
        m.python_type_strings[0])
    assert mback is not None
    assert has_modules is False
    assert mc._has_required_modules[-1] is False
    assert mc._imported_required_modules[-1] is False
    for name in m.required_parent_modules:
        assert name not in sys.modules


def test_missing_required_lazy():
    m = hdf5storage.Marshallers.TypeMarshaller()
    m.required_parent_modules = ['numpy']
    m.required_modules = ['ainivieanvueaq']
    m.python_type_strings = ['vi8vaeaniea']
    m.types = [s for s in m.python_type_strings]
    m.update_type_lookups()
    mc = hdf5storage.MarshallerCollection(lazy_loading=True,
                                          marshallers=[m])
    assert mc._has_required_modules[-1]
    assert mc._imported_required_modules[-1] is False
    mback, has_modules = mc.get_marshaller_for_type_string( \
        m.python_type_strings[0])
    assert mback is not None
    assert has_modules is False
    assert mc._has_required_modules[-1] is False
    assert mc._imported_required_modules[-1] is False
    for name in m.required_modules:
        assert name not in sys.modules


def test_missing_required_non_lazy():
    m = hdf5storage.Marshallers.TypeMarshaller()
    m.required_parent_modules = ['numpy']
    m.required_modules = ['ainivieanvueaq']
    m.python_type_strings = ['vi8vaeaniea']
    m.types = [s for s in m.python_type_strings]
    m.update_type_lookups()
    mc = hdf5storage.MarshallerCollection(lazy_loading=False,
                                          marshallers=[m])
    assert mc._has_required_modules[-1] is False
    assert mc._imported_required_modules[-1] is False
    mback, has_modules = mc.get_marshaller_for_type_string( \
        m.python_type_strings[0])
    assert mback is not None
    assert has_modules is False
    assert mc._has_required_modules[-1] is False
    assert mc._imported_required_modules[-1] is False
    for name in m.required_modules:
        assert name not in sys.modules


def test_has_required_lazy():
    m = hdf5storage.Marshallers.TypeMarshaller()
    m.required_parent_modules = ['tarfile']
    m.required_modules = ['tarfile']
    m.python_type_strings = ['ellipsis']
    m.types = ['builtins.ellipsis']
    m.update_type_lookups()
    for name in m.required_modules:
        assert name not in sys.modules
    mc = hdf5storage.MarshallerCollection(lazy_loading=True,
                                          marshallers=[m])
    for name in m.required_modules:
        assert name not in sys.modules
    assert mc._has_required_modules[-1]
    assert mc._imported_required_modules[-1] is False
    mback, has_modules = mc.get_marshaller_for_type_string( \
        m.python_type_strings[0])
    assert mback is not None
    assert has_modules
    assert mc._has_required_modules[-1]
    assert mc._imported_required_modules[-1]
    for name in m.required_modules:
        assert name in sys.modules

    # Do it again, but this time the modules are already loaded so that
    # flag should be set.
    mc = hdf5storage.MarshallerCollection(lazy_loading=True,
                                          marshallers=[m])
    assert mc._has_required_modules[-1]
    assert mc._imported_required_modules[-1]
    mback, has_modules = mc.get_marshaller_for_type_string( \
        m.python_type_strings[0])
    assert mback is not None
    assert has_modules
    assert mc._has_required_modules[-1]
    assert mc._imported_required_modules[-1]


def test_has_required_non_lazy():
    m = hdf5storage.Marshallers.TypeMarshaller()
    m.required_parent_modules = ['getopt']
    m.required_modules = ['getopt']
    m.python_type_strings = ['ellipsis']
    m.types = ['builtins.ellipsis']
    m.update_type_lookups()
    for name in m.required_modules:
        assert name not in sys.modules
    mc = hdf5storage.MarshallerCollection(lazy_loading=False,
                                          marshallers=[m])
    for name in m.required_modules:
        assert name in sys.modules
    assert mc._has_required_modules[-1]
    assert mc._imported_required_modules[-1]
    mback, has_modules = mc.get_marshaller_for_type_string( \
        m.python_type_strings[0])
    assert mback is not None
    assert has_modules
    assert mc._has_required_modules[-1]
    assert mc._imported_required_modules[-1]


def test_marshaller_read():
    m = Tmarshaller()
    m.required_parent_modules = ['json']
    m.required_modules = ['json']
    m.python_type_strings = ['ellipsis']
    m.types = ['builtins.ellipsis']
    m.update_type_lookups()
    mc = hdf5storage.MarshallerCollection(lazy_loading=True,
                                          marshallers=[m])
    options = hdf5storage.Options(marshaller_collection=mc)

    name = '/the'
    with tempfile.TemporaryDirectory() as folder:
        filename = os.path.join(folder, 'data.h5')
        with h5py.File(filename, mode='w') as f:
            f.create_dataset(name, data=np.int64([1]))
            f[name].attrs.create('Python.Type',
                                 b'ellipsis')
            out = hdf5storage.utilities.LowLevelFile(
                f, options).read_data(f, name)

    assert out == 'read'


def test_marshaller_read_approximate_missing_parent():
    m = Tmarshaller()
    m.required_parent_modules = ['aiveneiavie']
    m.required_modules = ['json']
    m.python_type_strings = ['ellipsis']
    m.types = ['builtins.ellipsis']
    m.update_type_lookups()
    mc = hdf5storage.MarshallerCollection(lazy_loading=True,
                                          marshallers=[m])
    options = hdf5storage.Options(marshaller_collection=mc)

    name = '/the'
    with tempfile.TemporaryDirectory() as folder:
        filename = os.path.join(folder, 'data.h5')
        with h5py.File(filename, mode='w') as f:
            f.create_dataset(name, data=np.int64([1]))
            f[name].attrs.create('Python.Type',
                                 b'ellipsis')
            out = hdf5storage.utilities.LowLevelFile(
                f, options).read_data(f, name)

    assert out == 'read_approximate'


def test_marshaller_read_approximate_missing_import():
    m = Tmarshaller()
    m.required_parent_modules = ['json']
    m.required_modules = ['aiveneiavie']
    m.python_type_strings = ['ellipsis']
    m.types = ['builtins.ellipsis']
    m.update_type_lookups()
    mc = hdf5storage.MarshallerCollection(lazy_loading=True,
                                          marshallers=[m])
    options = hdf5storage.Options(marshaller_collection=mc)

    name = '/the'
    with tempfile.TemporaryDirectory() as folder:
        filename = os.path.join(folder, 'data.h5')
        with h5py.File(filename, mode='w') as f:
            f.create_dataset(name, data=np.int64([1]))
            f[name].attrs.create('Python.Type',
                                 b'ellipsis')
            out = hdf5storage.utilities.LowLevelFile(
                f, options).read_data(f, name)

    assert out == 'read_approximate'
