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
""" Module of Exceptions and low level read and write functions.

"""

import posixpath

import numpy as np
import h5py

from hdf5storage.utilities import *


class Hdf5storageError(IOError):
    """ Base class of hdf5storage package exceptions."""
    pass


class CantReadError(Hdf5storageError):
    """ Exception for a failure to read the desired data."""
    pass


class TypeNotMatlabCompatibleError(Hdf5storageError):
    """ Exception for trying to write non-MATLAB compatible data.

    In the event that MATLAB compatibility is being done
    (``Options.matlab_compatible``) and a Python type is not importable
    by MATLAB, the data is either not written or this exception is
    thrown depending on the value of
    ``Options.action_for_matlab_incompatible``.

    See Also
    --------
    hdf5storage.Options.matlab_compatible
    hdf5storage.Options.action_for_matlab_incompatible

    """
    pass


def write_data(f, grp, name, data, type_string, options):
    """ Writes a piece of data into an open HDF5 file.

    Low level function to store a Python type (`data`) into the
    specified Group.

    Parameters
    ----------
    f : h5py.File
        The open HDF5 file.
    grp : h5py.Group or h5py.File
        The Group to place the data in.
    name : str
        The name to write the data to.
    data : any
        The data to write.
    type_string : str or None
        The type string of the data, or ``None`` to deduce
        automatically.
    options : hdf5storage.core.Options
        The options to use when writing.

    Raises
    ------
    NotImplementedError
        If writing `data` is not supported.
    TypeNotMatlabCompatibleError
        If writing a type not compatible with MATLAB and
        `options.action_for_matlab_incompatible` is set to ``'error'``.

    See Also
    --------
    hdf5storage.core.write : Higher level version.
    read_data
    hdf5storage.core.Options

    """
    # Get the marshaller for type(data).

    tp = type(data)
    m = options.marshaller_collection.get_marshaller_for_type(tp)

    # If a marshaller was found, use it to write the data. Otherwise,
    # return an error. If we get something other than None back, then we
    # must recurse through the entries. Also, we must set the H5PATH
    # attribute to be the path to the containing group.

    if m is not None:
        m.write(f, grp, name, data, type_string, options)
    else:
        raise NotImplementedError('Can''t write data type: '+str(tp))


def read_data(f, grp, name, options):
    """ Writes a piece of data into an open HDF5 file.

    Low level function to read a Python type of the specified name from
    specified Group.

    Parameters
    ----------
    f : h5py.File
        The open HDF5 file.
    grp : h5py.Group or h5py.File
        The Group to read the data from.
    name : str
        The name of the data to read.
    options : hdf5storage.core.Options
        The options to use when reading.

    Returns
    -------
    data
        The data named `name` in Group `grp`.

    Raises
    ------
    CantReadError
        If the data cannot be read successfully.

    See Also
    --------
    hdf5storage.core.read : Higher level version.
    write_data
    hdf5storage.core.Options

    """
    # If name isn't found, return error.
    dsetgrp = grp.get(name)
    if dsetgrp is None:
        raise CantReadError('Could not find '
                            + posixpath.join(grp.name, name))

    # Get the different attributes that can be used to identify they
    # type, which are the type string and the MATLAB class.
    type_string = get_attribute_string(dsetgrp, 'Python.Type')
    matlab_class = get_attribute_string(dsetgrp, 'MATLAB_class')

    # If the type_string is present, get the marshaller for it. If it is
    # not, use the one for the matlab class if it is given. Otherwise,
    # use the fallback (NumpyScalarArrayMarshaller for both Datasets and
    # Groups). If calls to the marshaller collection to get the right
    # marshaller don't return one (return None), we also go to the
    # default).

    m = None
    mc = options.marshaller_collection
    if type_string is not None:
        m = mc.get_marshaller_for_type_string(type_string)
    elif matlab_class is not None:
        m = mc.get_marshaller_for_matlab_class(matlab_class)

    if m is None:
        m = mc.get_marshaller_for_type(np.uint8)

    # If a marshaller was found, use it to write the data. Otherwise,
    # return an error.

    if m is not None:
        return m.read(f, grp, name, options)
    else:
        raise CantReadError('Could not read ' + dsetgrp.name)
