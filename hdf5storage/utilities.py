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
""" Module of functions to set and delete HDF5 attributes.

"""

import numpy as np
import h5py


def set_attribute(target, name, value):
    """ Sets an attribute on a Dataset or Group.

    If the attribute `name` doesn't exist yet, it is created. If it
    already exists, it is overwritten if it differs from `value`.

    Parameters
    ----------
    target : Dataset or Group
        :py:class:`h5py.Dataset` or :py:class:`h5py.Group` to set the
        attribute of.
    name : str
        Name of the attribute to set.
    value : numpy type other than :py:class:`str_`
        Value to set the attribute to.

    """
    if name not in target.attrs:
        target.attrs.create(name, value)
    elif target.attrs[name].dtype != value.dtype \
            or target.attrs[name].shape != value.shape:
        target.attrs.create(name, value)
    elif np.any(target.attrs[name] != value):
        target.attrs.modify(name, value)


def set_attribute_string(target, name, value):
    """ Sets an attribute to a string on a Dataset or Group.

    If the attribute `name` doesn't exist yet, it is created. If it
    already exists, it is overwritten if it differs from `value`.

    Parameters
    ----------
    target : Dataset or Group
        :py:class:`h5py.Dataset` or :py:class:`h5py.Group` to set the
        attribute of.
    name : str
        Name of the attribute to set.
    value : string
        Value to set the attribute to. Can be any sort of string type
        that will convert to a :py:class:`numpy.string_`

    """
    set_attribute(target, name, np.string_(value))


def set_attribute_string_array(target, name, string_list):
    """ Sets an attribute to an array of string on a Dataset or Group.

    If the attribute `name` doesn't exist yet, it is created. If it
    already exists, it is overwritten with the list of string
    `string_list` (they will be vlen strings).

    Parameters
    ----------
    target : Dataset or Group
        :py:class:`h5py.Dataset` or :py:class:`h5py.Group` to set the
        attribute of.
    name : str
        Name of the attribute to set.
    string_list : list, tuple
        List of strings to set the attribute to. Can be any string type
        that will convert to a :py:class:`numpy.string_`

    """
    target.attrs.create(name, np.string_(string_list),
                        dtype=h5py.special_dtype(vlen=bytes))


def del_attribute(target, name):
    """ Deletes an attribute on a Dataset or Group.

    If the attribute `name` exists, it is deleted.

    Parameters
    ----------
    target : Dataset or Group
        :py:class:`h5py.Dataset` or :py:class:`h5py.Group` to set the
        attribute of.
    name : str
        Name of the attribute to delete.

    """
    if name in target.attrs:
        del target.attrs[name]
