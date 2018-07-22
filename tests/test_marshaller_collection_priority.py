# Copyright (c) 2014-2016, Freja Nordsiek
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

import random

from nose.tools import raises
from nose.tools import assert_equal as assert_equal_nose

import hdf5storage
import hdf5storage.Marshallers

random.seed()

# Check if the example package is installed because some tests will
# depend on it.
try:
    from example_hdf5storage_marshaller_plugin import SubListMarshaller
    has_example_hdf5storage_marshaller_plugin = True
except:
    has_example_hdf5storage_marshaller_plugin = False


# Need a new marshaller that does nothing.
class JunkMarshaller(hdf5storage.Marshallers.TypeMarshaller):
    pass


@raises(TypeError)
def check_error_non_tuplelist(obj):
    hdf5storage.MarshallerCollection(priority=obj)


def test_error_non_tuplelist():
    for v in (None, True, 1, 2.3, '39va', b'391', set(), dict()):
        yield check_error_non_tuplelist, v


@raises(ValueError)
def test_error_missing_element():
    need = ('builtin', 'user', 'plugin')
    hdf5storage.MarshallerCollection(priority=[random.choice(need)
                                               for i in range(2)])


@raises(ValueError)
def test_error_extra_element():
    hdf5storage.MarshallerCollection(priority=('builtin', 'user',
                                               'plugin', 'extra'))


def test_builtin_plugin_user():
    m = JunkMarshaller()
    mc = hdf5storage.MarshallerCollection(load_plugins=True,
                                          priority=('builtin', 'plugin',
                                                    'user'),
                                          marshallers=(m, ))
    assert_equal_nose(m, mc._marshallers[-1])
    if has_example_hdf5storage_marshaller_plugin:
        assert isinstance(mc._marshallers[-2],
                          SubListMarshaller)


def test_builtin_user_plugin():
    m = JunkMarshaller()
    mc = hdf5storage.MarshallerCollection(load_plugins=True,
                                          priority=('builtin', 'user',
                                                    'plugin'),
                                          marshallers=(m, ))
    if has_example_hdf5storage_marshaller_plugin:
        assert isinstance(mc._marshallers[-1],
                          SubListMarshaller)
        assert_equal_nose(m, mc._marshallers[-2])
    else:
        assert_equal_nose(m, mc._marshallers[-1])


def test_plugin_builtin_user():
    m = JunkMarshaller()
    mc = hdf5storage.MarshallerCollection(load_plugins=True,
                                          priority=('plugin', 'builtin',
                                                    'user'),
                                          marshallers=(m, ))
    assert_equal_nose(m, mc._marshallers[-1])
    if has_example_hdf5storage_marshaller_plugin:
        assert isinstance(mc._marshallers[0],
                          SubListMarshaller)


def test_plugin_user_builtin():
    m = JunkMarshaller()
    mc = hdf5storage.MarshallerCollection(load_plugins=True,
                                          priority=('plugin', 'user',
                                                    'builtin'),
                                          marshallers=(m, ))
    if has_example_hdf5storage_marshaller_plugin:
        assert isinstance(mc._marshallers[0],
                          SubListMarshaller)
        assert_equal_nose(m, mc._marshallers[1])
    else:
        assert_equal_nose(m, mc._marshallers[0])


def test_user_builtin_plugin():
    m = JunkMarshaller()
    mc = hdf5storage.MarshallerCollection(load_plugins=True,
                                          priority=('user', 'builtin',
                                                    'plugin'),
                                          marshallers=(m, ))
    assert_equal_nose(m, mc._marshallers[0])
    if has_example_hdf5storage_marshaller_plugin:
        assert isinstance(mc._marshallers[-1],
                          SubListMarshaller)


def test_user_plugin_builtin():
    m = JunkMarshaller()
    mc = hdf5storage.MarshallerCollection(load_plugins=True,
                                          priority=('user', 'plugin',
                                                    'builtin'),
                                          marshallers=(m, ))
    assert_equal_nose(m, mc._marshallers[0])
    if has_example_hdf5storage_marshaller_plugin:
        assert isinstance(mc._marshallers[1],
                          SubListMarshaller)
