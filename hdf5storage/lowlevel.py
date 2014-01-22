# Copyright (c) 2013, Freja Nordsiek
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

import posixpath

import numpy as np
import h5py

from hdf5storage.utilities import *


class Hdf5storageError(IOError):
    """ Base class of hdf5storage package exceptions."""
    pass


class CantReadError(Hdf5storageError):
    """ Exception for a failure to read the desired data."""


def write_data(f, grp, name, data, type_string, options):
    # Get the marshaller for type(data).

    tp = type(data)
    m = options.marshaller_collection.get_marshaller_for_type(tp)

    # If a marshaller was found, use it to write the data. Otherwise,
    # return an error. If we get something other than None back, then we
    # must recurse through the entries. Also, we must set the H5PATH
    # attribute to be the path to the containing group.

    if m is not None:
        outputs = m.write(f, grp, name, data, type_string, options)
        if outputs is not None:
            if len(outputs) > 2:
                _MATLAB_fields_pairs.extend(outputs[2])
            for i, v in enumerate(outputs[1]):
                if len(outputs[0]) == 1:
                    write_data(f, outputs[0][0], v[0], v[1], None,
                               options)
                    if options.MATLAB_compatible:
                        set_attribute_string(outputs[0][0][v[0]],
                                             'H5PATH',
                                             outputs[0][0].name)
                    else:
                        del_attribute(outputs[0][0][v[0]], 'H5PATH')
                else:
                    write_data(f, outputs[0][i], v[0], v[1], None,
                               options)
                    if options.MATLAB_compatible:
                        set_attribute_string(outputs[0][i][v[0]],
                                             'H5PATH',
                                             outputs[0][i].name)
                    else:
                        del_attribute(outputs[0][i][v[0]], 'H5PATH')
    else:
        raise NotImplementedError('Can''t write data type: '+str(tp))


def read_data(f, grp, name, options):
    # If name isn't found, return error.
    if name not in grp:
        raise CantReadError('Could not find '
                            + posixpath.join(grp.name, name))

    # Get the different attributes that can be used to identify they
    # type, which are the type string and the MATLAB class.
    type_string = get_attribute_string(grp[name], 'CPython.Type')
    matlab_class = get_attribute_string(grp[name], 'MATLAB_class')

    # If the type_string is present, get the marshaller for it. If it is
    # not, use the one for the matlab class if it is given. Otherwise,
    # use the fallback (NumpyScalarArrayMarshaller for Datasets and
    # PythonDictMarshaller for Groups). If calls to the marshaller
    # collection to get the right marshaller don't return one (return
    # None, we also go to the default).

    m = None
    mc = options.marshaller_collection
    if type_string is not None:
        m = mc.get_marshaller_for_type_string(type_string)
    elif matlab_class is not None:
        m = mc.get_marshaller_for_matlab_class(matlab_class)

    if m is None:
        if isinstance(grp[name], h5py.Dataset):
            m = mc.get_marshaller_for_type(np.uint8)
        else:
            m = mc.get_marshaller_for_type(dict)

    # If a marshaller was found, use it to write the data. Otherwise,
    # return an error.

    if m is not None:
        return m.read(f, grp, name, options)
    else:
        raise CantReadError('Could not read ' + grp[name].name)
