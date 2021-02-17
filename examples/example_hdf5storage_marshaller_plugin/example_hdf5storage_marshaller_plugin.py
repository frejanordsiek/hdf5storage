# Copyright (c) 2017-2021, Freja Nordsiek
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
"""
This is an example package for providing hdf5storage plugins.

"""

__version__ = '0.2'

import hdf5storage.Marshallers as hm


# Going to make a class that subclasses lists but doesn't really do
# anything else, but it will be enought to need a new marshaller.

class SubList(list):
    def __init__(self, *args, **keywords):
        list.__init__(self, *args, **keywords)


# The marshaller for this will be rather trivial. It inherits from
# PythonTupleSetDequeMarshaller which inherits from
# PythonListMarshaller. The only things that require any work is
# __init__ as PythonTupleSetDequeMarshaller's methods will otherwise
# work as is.
class SubListMarshaller(hm.PythonTupleSetDequeMarshaller):
    def __init__(self):
        hm.PythonTupleSetDequeMarshaller.__init__(self)
        self.types = ['example_hdf5storage_marshaller_plugin.SubList']
        self.python_type_strings = ['hdf5storage_marshallers_plugins_'
                                    'example.SubList']
        # As the parent class already has MATLAB strings handled, there
        # are no MATLAB classes that this marshaller should be used for.
        self.matlab_classes = []
        # Update the type lookups.
        self.update_type_lookups()

    def read(self, f, dsetgrp, attributes):
        # Use the grand-parent class version to read it and do most of
        # the work.
        data = hm.PythonListMarshaller.read(self, f, dsetgrp,
                                            attributes)
        return SubList(data)


# Return an instance of the one and only marshaller using the 1.0
# Marshaller API when given the hdf5storage version string. The version
# string is given so that plugin implementors can possibly select
# marshallers based on the version or initialize them in different ways,
# beyond just what the Marshaller API version information provides
# (perhaps some particular versions of hdf5storage require a work around
# on some issue or another).
def get_marshallers_1p0(hdf5storage_version):
    return (SubListMarshaller(), )

