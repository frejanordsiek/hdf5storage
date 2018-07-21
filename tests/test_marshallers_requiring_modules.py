# Copyright (c) 2016, Freja Nordsiek
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
import tempfile

import numpy as np
import h5py

import hdf5storage
import hdf5storage.utilities
import hdf5storage.Marshallers

from nose.tools import assert_is_not_none, assert_is_none, \
    assert_false, assert_equal, assert_not_in, assert_in


class Tmarshaller(hdf5storage.Marshallers.TypeMarshaller):
    def read(self, f, dsetgrp, attributes, options):
        return 'read'

    def read_approximate(self, f, dsetgrp, attributes, options):
        return 'read_approximate'


def test_missing_required_parent():
    m = hdf5storage.Marshallers.TypeMarshaller()
    m.required_parent_modules = ['ainivieanvueaq']
    m.python_type_strings = ['vi8vaeaniea']
    m.types = [s for s in m.python_type_strings]
    m.update_type_lookups()
    mc = hdf5storage.MarshallerCollection(marshallers=[m])
    assert_false(mc._has_required_modules[-1])
    assert_false(mc._imported_required_modules[-1])
    mback, has_modules = mc.get_marshaller_for_type_string( \
        m.python_type_strings[0])
    assert_is_not_none(mback)
    assert_false(has_modules)
    assert_false(mc._has_required_modules[-1])
    assert_false(mc._imported_required_modules[-1])
    for name in m.required_parent_modules:
        assert_not_in(name, sys.modules)


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
    assert_false(mc._imported_required_modules[-1])
    mback, has_modules = mc.get_marshaller_for_type_string( \
        m.python_type_strings[0])
    assert_is_not_none(mback)
    assert_false(has_modules)
    assert_false(mc._has_required_modules[-1])
    assert_false(mc._imported_required_modules[-1])
    for name in m.required_modules:
        assert_not_in(name, sys.modules)


def test_missing_required_non_lazy():
    m = hdf5storage.Marshallers.TypeMarshaller()
    m.required_parent_modules = ['numpy']
    m.required_modules = ['ainivieanvueaq']
    m.python_type_strings = ['vi8vaeaniea']
    m.types = [s for s in m.python_type_strings]
    m.update_type_lookups()
    mc = hdf5storage.MarshallerCollection(lazy_loading=False,
                                          marshallers=[m])
    assert_false(mc._has_required_modules[-1])
    assert_false(mc._imported_required_modules[-1])
    mback, has_modules = mc.get_marshaller_for_type_string( \
        m.python_type_strings[0])
    assert_is_not_none(mback)
    assert_false(has_modules)
    assert_false(mc._has_required_modules[-1])
    assert_false(mc._imported_required_modules[-1])
    for name in m.required_modules:
        assert_not_in(name, sys.modules)


def test_has_required_lazy():
    m = hdf5storage.Marshallers.TypeMarshaller()
    m.required_parent_modules = ['json']
    m.required_modules = ['json']
    m.python_type_strings = ['ellipsis']
    m.types = ['builtins.ellipsis']
    m.update_type_lookups()
    for name in m.required_modules:
        assert_not_in(name, sys.modules)
    mc = hdf5storage.MarshallerCollection(lazy_loading=True,
                                          marshallers=[m])
    for name in m.required_modules:
        assert_not_in(name, sys.modules)
    assert mc._has_required_modules[-1]
    assert_false(mc._imported_required_modules[-1])
    mback, has_modules = mc.get_marshaller_for_type_string( \
        m.python_type_strings[0])
    assert_is_not_none(mback)
    assert has_modules
    assert mc._has_required_modules[-1]
    assert mc._imported_required_modules[-1]
    for name in m.required_modules:
        assert_in(name, sys.modules)

    # Do it again, but this time the modules are already loaded so that
    # flag should be set.
    mc = hdf5storage.MarshallerCollection(lazy_loading=True,
                                          marshallers=[m])
    assert mc._has_required_modules[-1]
    assert mc._imported_required_modules[-1]
    mback, has_modules = mc.get_marshaller_for_type_string( \
        m.python_type_strings[0])
    assert_is_not_none(mback)
    assert has_modules
    assert mc._has_required_modules[-1]
    assert mc._imported_required_modules[-1]


def test_has_required_non_lazy():
    m = hdf5storage.Marshallers.TypeMarshaller()
    m.required_parent_modules = ['csv']
    m.required_modules = ['csv']
    m.python_type_strings = ['ellipsis']
    m.types = ['builtins.ellipsis']
    m.update_type_lookups()
    for name in m.required_modules:
        assert_not_in(name, sys.modules)
    mc = hdf5storage.MarshallerCollection(lazy_loading=False,
                                          marshallers=[m])
    for name in m.required_modules:
        assert_in(name, sys.modules)
    assert mc._has_required_modules[-1]
    assert mc._imported_required_modules[-1]
    mback, has_modules = mc.get_marshaller_for_type_string( \
        m.python_type_strings[0])
    assert_is_not_none(mback)
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

    fld = None
    name = '/the'
    try:
        fld = tempfile.mkstemp()
        os.close(fld[0])
        filename = fld[1]
        with h5py.File(filename) as f:
            f.create_dataset(name, data=np.int64([1]))
            f[name].attrs.create('Python.Type',
                                 b'ellipsis')
            out = hdf5storage.utilities.read_data(f, f, name, options)
    except:
        raise
    finally:
        if fld is not None:
            os.remove(fld[1])

    assert_equal(out, 'read')


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

    fld = None
    name = '/the'
    try:
        fld = tempfile.mkstemp()
        os.close(fld[0])
        filename = fld[1]
        with h5py.File(filename) as f:
            f.create_dataset(name, data=np.int64([1]))
            f[name].attrs.create('Python.Type',
                                 b'ellipsis')
            out = hdf5storage.utilities.read_data(f, f, name, options)
    except:
        raise
    finally:
        if fld is not None:
            os.remove(fld[1])

    assert_equal(out, 'read_approximate')


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

    fld = None
    name = '/the'
    try:
        fld = tempfile.mkstemp()
        os.close(fld[0])
        filename = fld[1]
        with h5py.File(filename) as f:
            f.create_dataset(name, data=np.int64([1]))
            f[name].attrs.create('Python.Type',
                                 b'ellipsis')
            out = hdf5storage.utilities.read_data(f, f, name, options)
    except:
        raise
    finally:
        if fld is not None:
            os.remove(fld[1])

    assert_equal(out, 'read_approximate')
