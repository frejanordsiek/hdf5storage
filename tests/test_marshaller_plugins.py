# Copyright (c) 2014-2021, Freja Nordsiek
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
import tempfile

import pkg_resources

import pytest

import hdf5storage
import hdf5storage.plugins

# Check if the example package is installed because some tests will
# depend on it.
try:
    import example_hdf5storage_marshaller_plugin
    has_example_hdf5storage_marshaller_plugin = True
except:
    has_example_hdf5storage_marshaller_plugin = False


def test_marshaller_api_versions():
    assert ('1.0', ) == \
        hdf5storage.plugins.supported_marshaller_api_versions()


def test_find_thirdparty_marshaller_plugins():
    found_example = False
    apivs = hdf5storage.plugins.supported_marshaller_api_versions()
    plugins = hdf5storage.plugins.find_thirdparty_marshaller_plugins()
    assert isinstance(plugins, dict)
    assert set(apivs) == set(plugins)
    for k, v in plugins.items():
        assert isinstance(k, str)
        assert isinstance(v, dict)
        for k2, v2 in v.items():
            assert isinstance(k2, str)
            assert isinstance(v2, pkg_resources.EntryPoint)
            if k2 == 'example_hdf5storage_marshaller_plugin':
                found_example = True
    assert has_example_hdf5storage_marshaller_plugin == found_example


@pytest.mark.skipif(has_example_hdf5storage_marshaller_plugin,
                    reason='requires example_hdf5storage_marshaller_'
                    'plugin')
def test_plugin_marshaller_SubList():
    mc = hdf5storage.MarshallerCollection(load_plugins=True,
                                          lazy_loading=True)
    options = hdf5storage.Options(store_python_metadata=True,
                                  matlab_compatible=False,
                                  marshaller_collection=mc)
    ell = [1, 2, 'b1', b'3991', True, None]
    data = example_hdf5storage_marshaller_plugin.SubList(ell)
    name = '/a'
    with tempfile.TemporaryDirectory() as folder:
        filename = os.path.join(folder, 'data.h5')
        hdf5storage.write(data, path=name, filename=filename,
                          options=options)
        out = hdf5storage.read(path=name, filename=filename,
                               options=options)
    assert ell == list(out)
    assert type(out) == example_hdf5storage_marshaller_plugin.SubList
