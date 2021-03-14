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

""" Module for various utility functions.

There are utility functions for low level reading and writing, setting
and delete HDF5 attributes, encoding and decoding strings and complex
arrays, etc.

"""

import collections
import collections.abc
import copy
import posixpath
import random
import sys

import pkg_resources
import numpy as np
import h5py

import hdf5storage.exceptions


# We need to determine if h5py is one of the versions that cannot read
# the MATLAB_fields Attribute in the normal fashion so that we can
# handle it specially in LowLevelFile.read.
_handle_matlab_fields_specially = (
    pkg_resources.parse_version(h5py.__version__)
    in (pkg_resources.parse_version('3.0'),
        pkg_resources.parse_version('3.1')))

if _handle_matlab_fields_specially:
    import ctypes
    import h5py._objects


def does_dtype_have_a_zero_shape(dt):
    """ Determine whether a dtype (or its fields) have zero shape.

    Determines whether the given ``numpy.dtype`` has a shape with a zero
    element or if one of its fields does, or if one of its fields'
    fields does, and so on recursively. The following dtypes do not have
    zero shape.

    * ``'uint8'``
    * ``[('a', 'int32'), ('blah', 'float16', (3, 3))]``
    * ``[('a', [('b', 'complex64')], (2, 1, 3))]``

    But the following do

    * ``('uint8', (1, 0))``
    * ``[('a', 'int32'), ('blah', 'float16', (3, 0))]``
    * ``[('a', [('b', 'complex64')], (2, 0, 3))]``

    Parameters
    ----------
    dt : numpy.dtype
        The dtype to check.

    Returns
    -------
    yesno : bool
        Whether `dt` or one of its fields has a shape with at least one
        element that is zero.

    Raises
    ------
    TypeError
        If `dt` is not a ``numpy.dtype``.

    """
    components = [dt]
    while 0 != len(components):
        c = components.pop()
        if 0 in c.shape:
            return True
        if c.names is not None:
            components.extend([v[0] for v in c.fields.values()])
        if c.base != c:
            components.append(c.base)
    return False


def read_matlab_fields_attribute(attrs):
    """ Reads the ``MATLAB_fields`` Attribute.

    On some versions of ``h5py``, the ``MATLAB_fields`` Attribute cannot
    be read in the standard way and must instead be read in a more
    manual fashion. This function reads the Attribute by the proper
    method.

    Parameters
    ----------
    attrs : h5py.AttributeManager
        The Attribute manager to read from.

    Returns
    -------
    value : numpy.ndarray or None
        The value of the ``MATLAB_fields`` Attribute, or ``None`` if it
        isn't available or its format is invalid.

    Raises
    ------
    TypeError
        If an argument has the wrong type.

    """
    if not isinstance(attrs, h5py.AttributeManager):
        raise TypeError('attrs must be a h5py.AttributeManager.')
    if not _handle_matlab_fields_specially:
        return attrs.get('MATLAB_fields')
    if 'MATLAB_fields' not in attrs:
        return None
    # The following method is loosely based on the method provided by
    # takluyver at
    # https://github.com/h5py/h5py/issues/1817#issuecomment-781385699
    #
    # but has been improved by reading it directly as (size_t, void*)
    # pairs uint64s instead of using struct.unpack, and avoiding making
    # intermediate copies of the data by copying directly to the output
    # array.
    with h5py._objects.phil:
        attr_id = attrs.get_id('MATLAB_fields')
        dt = np.dtype([('length', np.uintp), ('pointer', np.intp)])
        raw_buf = np.empty(attr_id.shape, dtype=dt)
        attr_id.read(raw_buf, mtype=attr_id.get_type())
        attr = np.empty(raw_buf.shape, dtype='object')
        for i, (length, ptr) in enumerate(raw_buf.flat):
            at = np.empty(length, dtype='S1')
            ctypes.memmove(at.ctypes.data, int(ptr), int(length))
            attr.flat[i] = at
        return attr


def read_all_attributes_into(attrs, out):
    """ Reads all Attributes into a MutableMapping (dict-like)

    Reads all Attributes into the MutableMapping (dict-like) out,
    including the special handling of the ``MATLAB_fields`` Attribute on
    versions of ``h5py`` where it cannot be read in the standard
    fashion.

    Parameters
    ----------
    attrs : h5py.AttributeManager
        The Attribute manager to read from.
    out : MutableMapping
        The MutableMapping (dict-like) to write the Attributes into.

    Raises
    ------
    TypeError
        If an argument has the wrong type.

    See Also
    --------
    read_matlab_fields_attribute

    """
    if not isinstance(attrs, h5py.AttributeManager):
        raise TypeError('attrs must be a h5py.AttributeManager.')
    if not isinstance(out, (dict, collections.defaultdict,
                            collections.abc.MutableMapping)):
        raise TypeError('out must be a MutableMapping.')
    if not _handle_matlab_fields_specially \
            or 'MATLAB_fields' not in attrs:
        out.update(attrs.items())
    else:
        for k in attrs:
            if k != 'MATLAB_fields':
                out[k] = attrs[k]
            else:
                out[k] = read_matlab_fields_attribute(attrs)


class LowLevelFile(object):
    """ Low level wrapper for the HDF5 file object with utilities.

    Wraps a ``h5py.File`` and provides numerous utilities to help with
    writing and reading Python objects to the file, providing the
    options, etc.

    .. versionadded:: 0.2

    Parameters
    ----------
    f : h5py.File
        The raw file handle.
    options : hdf5storage.Options
        The options used for reading and writing.

    Raises
    ------
    TypeError
        If an argument has an invalid type.

    Attributes
    ----------
    f : h5py.File
        The raw file handle.
    options : hdf5storage.Options
        The options used for reading and writing.

    """
    def __init__(self, f, options):
        # Check the types of the arguments real quick to be on the safe
        # side. options has to be checked using the __module__ and
        # __name__ attributes since we can't import the main hdf5storage
        # module since that would lead to a circular import.
        if not isinstance(f, h5py.File):
            raise TypeError('f must be a h5py.File.')
        if options.__class__.__module__ != 'hdf5storage' \
                or options.__class__.__name__ != 'Options':
            raise TypeError('options must be a hdf5storage.Options.')
        self._f = f
        self._options = options

        # We need to keep track of the references group after we first
        # use it, whether we created it or not, and a reference to the
        # canonical empty. They will initially be None to indicate that
        # we don't know yet (accessed lazily). We will also store the
        # name of the references group.
        self._refs_group = None
        self._created_refs_group = None
        self._canonical_empty = None
        self._refs_group_name = None
        # When we are creating names for the references group, we don't
        # have to worry about checking for a name already being present
        # if we created the Group. Instead, we can just use a counter
        # that we increment by one each time a name is needed. We start
        # it at 0xB since 'a' is the name of the canonical empty and we
        # want to skip past it in hexidecimal.
        self._refs_group_counter = 0xB
        # Length in characters we will use for random names in the
        # references Group.
        self._refs_group_name_length = 16

    @property
    def f(self):
        return self._f

    @property
    def options(self):
        return self._options

    def write_data(self, grp, name, data, type_string):
        """ Writes a piece of data into the file in the given group.

        Low level method to store a Python type (`data`) into the
        specified Group.

        Parameters
        ----------
        grp : h5py.Group or h5py.File
            The Group to place the data in.
        name : str
            The name to write the data to.
        data : any
            The data to write.
        type_string : str or None
            The type string of the data, or ``None`` to deduce
            automatically.

        Returns
        -------
        obj : h5py.Dataset or h5py.Group or None
            The base Dataset or Group having the name `name` in `grp`
            that was made, or ``None`` if nothing was written.

        Raises
        ------
        NotImplementedError
            If writing `data` is not supported.
        TypeNotMatlabCompatibleError
            If writing a type not compatible with MATLAB and
            ``self.options.action_for_matlab_incompatible`` is set to
            ``'error'``.

        See Also
        --------
        read_data
        hdf5storage.Options

        """
        # Get the marshaller for type(data). The required modules should
        # be here and imported. A workaround must be when data is a
        # dtype since dtypes are no longer type numpy.dtype in numpy
        # 1.20.
        if isinstance(data, np.dtype):
            tp = np.dtype
        else:
            tp = type(data)
        m, has_modules = \
            self._options.marshaller_collection.get_marshaller_for_type(tp)

        # If a marshaller was found and we have the required modules,
        # use it to write the data. Otherwise, return an error. If we
        # get something other than None back, then we must recurse
        # through the entries. Also, we must set the H5PATH attribute to
        # be the path to the containing group.

        if m is not None and has_modules:
            return m.write(self, grp, name, data, type_string)
        else:
            raise NotImplementedError('Can''t write data type: '
                                      + str(tp))

    def read_data(self, grp, name, dsetgrp=None):
        """ Writes a piece of data into the file.

        Low level method to read a Python type of the specified name
        from specified Group.

        Parameters
        ----------
        grp : h5py.Group or h5py.File
            The Group to read the data from.
        name : str
            The name of the data to read.
        dsetgrp : h5py.Dataset or h5py.Group or None, optional
            The Dataset or Group object to read if that has already been
            obtained and thus should not be re-obtained (``None``
            otherwise). If given, overrides `grp` and `name`.

        Returns
        -------
        data
            The data named `name` in Group `grp`.

        Raises
        ------
        KeyError
            If the data cannot be found.
        CantReadError
            If the data cannot be read successfully.

        See Also
        --------
        write_data
        hdf5storage.Options

        """
        if dsetgrp is None:
            # If name isn't found, return error.
            try:
                dsetgrp = grp[name]
            except:
                raise KeyError('Could not find '
                               + posixpath.join(grp.name, name))

        # Get all attributes with values, with the default being for any
        # unavailable ones being None.
        attributes = collections.defaultdict(type(None))
        read_all_attributes_into(dsetgrp.attrs, attributes)

        # Get the different attributes that can be used to identify they
        # type, which are the type string and the MATLAB class.
        type_string = convert_attribute_to_string(
            attributes['Python.Type'])
        matlab_class = convert_attribute_to_string(
            attributes['MATLAB_class'])

        # If the type_string is present, get the marshaller for it. If
        # it is not, use the one for the matlab class if it is
        # given. Otherwise, use the fallback (NumpyScalarArrayMarshaller
        # for both Datasets and Groups). If calls to the marshaller
        # collection to get the right marshaller don't return one
        # (return None), we also go to the default). Also get whether we
        # have the modules required to read it accurately or not
        # (approximately)

        m = None
        has_modules = False
        mc = self._options.marshaller_collection
        if type_string is not None:
            m, has_modules = mc.get_marshaller_for_type_string(
                type_string)
        elif matlab_class is not None:
            m, has_modules = mc.get_marshaller_for_matlab_class(
                matlab_class)
        elif hasattr(dsetgrp, 'dtype'):
            # Numpy dataset
            m, has_modules = mc.get_marshaller_for_type(
                dsetgrp.dtype.type)
        elif isinstance(dsetgrp, (h5py.Group, h5py.File)):
            # Groups and files are like Matlab struct
            m, has_modules = mc.get_marshaller_for_matlab_class(
                'struct')
        if m is None:
            # use Numpy as a fallback
            m, has_modules = mc.get_marshaller_for_type(np.uint8)

        # If a marshaller was found, use it to read the data. Otherwise,
        # return an error.

        if m is not None:
            if has_modules:
                return m.read(self, dsetgrp, attributes)
            else:
                return m.read_approximate(self, dsetgrp, attributes)
        else:
            raise hdf5storage.exceptions.CantReadError('Could not read '
                                                       + dsetgrp.name)

    def write_object_array(self, data):
        """ Writes an array of objects recursively.

        Writes the elements of the given object array recursively in the
        HDF5 Group ``self.options.group_for_references`` and returns an
        ``h5py.Reference`` array to all the elements.

        Parameters
        ----------
        data : numpy.ndarray of objects
            Numpy object array to write the elements of.

        Returns
        -------
        obj_array : numpy.ndarray of h5py.Reference
            A reference array pointing to all the elements written to
            the HDF5 file. For those that couldn't be written, the
            respective element points to the canonical empty.

        Raises
        ------
        TypeNotMatlabCompatibleError
            If writing a type not compatible with MATLAB and
            ``self.options.action_for_matlab_incompatible`` is set to
            ``'error'``.

        See Also
        --------
        read_object_array
        hdf5storage.Options.group_for_references
        h5py.Reference

        """
        # We need the Group to hold references. We might already have
        # it. If not, we need to create the Group if it isn't present
        # and get its handle, while storing the handle and noting
        # whether we created it or not.
        if self._refs_group is None:
            self._refs_group = self._f.get(
                self._options.group_for_references,
                default=None)
            if self._refs_group is None or not isinstance(
                    self._refs_group, h5py.Group):
                # It doesn't exist yet or isn't a Group, so it needs to
                # be created (and deleted if it is something else).
                if self._refs_group is not None:
                    del self._f[self._options.group_for_references]
                self._refs_group = self._f.create_group(
                    self._options.group_for_references)
                self._created_refs_group = True
            else:
                # Was already present, which means we didn't create it.
                self._created_refs_group = False
            # Get the name if we don't have it.
            if self._refs_group_name is None:
                self._refs_group_name = self._refs_group.name

        # The Dataset 'a' needs to be present as the canonical empty. It
        # is just a np.uint32/64([0, 0]) with its a MATLAB_class of
        # 'canonical empty' and the 'MATLAB_empty' attribute set. If it
        # isn't present or is incorrectly formatted, it is created
        # truncating anything previously there.
        if self._canonical_empty is None:
            self._canonical_empty = self._refs_group.get(
                'a', default=None)
            if self._canonical_empty is not None and (
                    not isinstance(self._canonical_empty, h5py.Dataset)
                    or self._canonical_empty.shape != (2,)
                    or not self._canonical_empty.dtype.name.startswith(
                        'uint')
                    or np.any(self._canonical_empty[...]
                              != np.uint64([0, 0]))
                    or get_attribute_string(self._canonical_empty,
                                            'MATLAB_class')
                    != 'canonical empty'
                    or get_attribute(self._canonical_empty,
                                     'MATLAB_empty') != 1):
                del self._refs_group['a']
                self._canonical_empty = None
            if self._canonical_empty is None:
                self._canonical_empty = self._refs_group.create_dataset(
                    'a', data=np.uint64([0, 0]))
                set_attribute_string(self._canonical_empty,
                                     'MATLAB_class',
                                     'canonical empty')
                set_attribute(self._canonical_empty, 'MATLAB_empty',
                              np.uint8(1))

        # We need to grab the special reference dtype and make an empty
        # array to store all the references in.
        data_refs = np.full(data.shape, self._canonical_empty.ref,
                            dtype=h5py.special_dtype(
                                ref=h5py.Reference))

        # Go through all the elements of data and write them, gabbing
        # their references and putting them in data_refs. They will be
        # put in group_for_references, which is also what the H5PATH
        # needs to be set to if we are doing MATLAB compatibility
        # (otherwise, the attribute needs to be deleted). If an element
        # can't be written (doing matlab compatibility, but it isn't
        # compatible with matlab and action_for_matlab_incompatible
        # option is True), the reference to the canonical empty will be
        # used for the reference array to point to.
        data_refs_flat = data_refs.reshape(-1)
        for index, x in enumerate(data.flat):
            name_for_ref = self.next_unused_ref_group_name()
            obj = self.write_data(self._refs_group, name_for_ref, x,
                                  None)
            if obj is not None:
                data_refs_flat[index] = obj.ref
                if self._options.matlab_compatible:
                    set_attribute_string(obj,
                                         'H5PATH',
                                         self._refs_group_name)
                else:
                    del_attribute(obj, 'H5PATH')

        # Now, the dtype needs to be changed to the reference type,
        # which will incidentally copy it.
        return data_refs

    def read_object_array(self, data):
        """ Reads an array of objects recursively.

        Reads the elements of the given HDF5 Reference array recursively
        and constructs a ``numpy.object_`` array from its elements,
        which is returned.

        Parameters
        ----------
        data : numpy.ndarray of h5py.Reference
            The array of HDF5 References to read and make an object
            array from.

        Raises
        ------
        NotImplementedError
            If reading the object from file is currently not supported.

        Returns
        -------
        obj_array : numpy.ndarray of numpy.object\\_
            The Python object array containing the items pointed to by
            `data`.

        See Also
        --------
        write_object_array
        hdf5storage.Options.group_for_references
        h5py.Reference

        """
        # Go through all the elements of data and read them using their
        # references, and the putting the output in new object array.
        data_derefed = np.zeros(shape=data.shape, dtype='object')
        data_derefed_flat = data_derefed.reshape(-1)
        data_flat = data[...].ravel()
        for index, x in enumerate(data_flat):
            data_derefed_flat[index] = self.read_data(
                None, None, dsetgrp=self._f[x])
        return data_derefed

    def next_unused_ref_group_name(self):
        """ Gives the next unused name that the references Group.

        Generates the next unused name for use in the references
        Group. If the Group is full enough, there may be no available
        names meaning that this function will hang.

        Returns
        -------
        name : str
            A name that isn't already an existing Dataset or Group in
            the references Group.

        See Also
        --------
        hdf5storage.Options.group_for_references

        """
        # If we created the references group, we can just use the
        # counter to generate the name and not check for collisions and
        # increment the counter afterwards.
        if self._created_refs_group:
            name = '%x' % self._refs_group_counter
            self._refs_group_counter += 1
            return name
        # We need to make a random name and check for collisions.
        #
        # While
        #
        # ltrs = string.ascii_letters + string.digits
        # name = ''.join([random.choice(ltrs)
        #                 for i in range(self._refs_group_name_length)])
        #
        # seems intuitive, its performance is abysmal compared to
        #
        # '%0{0}x'.format(self._refs_group_name_length) \
        #     % random.getrandbits(self._refs_group_name_length * 4)
        #
        # The difference is a factor of 20. Idea from
        #
        # https://stackoverflow.com/questions/2782229/most-lightweight-way-
        #   to-create-a-random-string-and-a-random-hexadecimal-number/
        #   35161595#35161595
        fmt = '%0{0}x'.format(self._refs_group_name_length)
        bits = self._refs_group_name_length * 4
        name = fmt % random.getrandbits(bits)
        while name in self._refs_group:
            name = fmt % random.getrandbits(bits)
        return name


def convert_dtype_to_str(dtype):
    """ Convert a dtype to str.

    Converts a ``numpy.dtype`` to ``str`` in such a way that the result
    can be passed through ``ast.literal_eval`` and then passed directly
    to the constructor of ``numpy.dtype`` to recreate `dtype`.

    Warning
    -------
    The output of this function is suitable for ``ast.literal_eval``,
    which is safe. **NEVER** use ``eval`` for this purpose because
    ``eval`` is a security risk if the data is ever tampered with.

    Parameters
    ----------
    dtype : numpy.dtype
        The dtype to convert

    Returns
    -------
    out : str
        The converted dtype. Can be passed through ``ast.literal_eval``.

    Raises
    ------
    TypeError
        If the argument is not the right type.

    See Also
    --------
    ast.literal_eval

    """
    if not isinstance(dtype, np.dtype):
        raise TypeError('dtype must be a numpy.dtype.')
    out = str(dtype)
    if out[0] not in '([{':
        return "'" + out + "'"
    else:
        return out


def convert_numpy_str_to_uint16(data):
    """ Converts a ``numpy.unicode_`` to UTF-16 in numpy.uint16 form.

    Convert a ``numpy.unicode_`` or an array of them (they are UTF-32
    strings) to UTF-16 in the equivalent array of ``numpy.uint16``. The
    conversion will throw an exception if any characters cannot be
    converted to UTF-16. Strings are expanded along rows (across columns)
    so a 2x3x4 array of 10 element strings will get turned into a 2x2x40
    array of uint16's if every UTF-32 character converts easily to a
    UTF-16 singlet, as opposed to a UTF-16 doublet.

    Parameters
    ----------
    data : numpy.unicode\\_ or numpy.ndarray of numpy.unicode\\_
        The string or array of them to convert.

    Returns
    -------
    array : numpy.ndarray of numpy.uint16
        The result of the conversion.

    Raises
    ------
    UnicodeEncodeError
        If a UTF-32 character has no UTF-16 representation.

    See Also
    --------
    convert_numpy_str_to_uint32
    convert_to_numpy_str

    """
    # An empty string should be an empty uint16
    if data.nbytes == 0:
        return np.uint16([])

    # We need to use the UTF-16 codec for our endianness. Using the
    # right one means we don't have to worry about removing the BOM.
    if sys.byteorder == 'little':
        codec = 'UTF-16LE'
    else:
        codec = 'UTF-16BE'

    # numpy.char.encode can do the conversion element wise. Then, we
    # just have convert to uin16 with the appropriate dimensions. The
    # dimensions are gotten from the shape of the converted data with
    # the number of column increased by the number of words (pair of
    # bytes) in the strings.
    cdata = np.char.encode(np.atleast_1d(data), codec)
    shape = list(cdata.shape)
    shape[-1] *= (cdata.dtype.itemsize // 2)
    return np.ndarray(shape=shape, dtype='uint16',
                      buffer=cdata)


def convert_numpy_str_to_uint32(data):
    """ Converts ``numpy.unicode_`` to its numpy.uint32 representation.

    Convert a ``numpy.unicode_`` or an array of them (they are UTF-32
    strings) into the equivalent array of ``numpy.uint32`` that is byte
    for byte identical. Strings are expanded along rows (across columns)
    so a 2x3x4 array of 10 element strings will get turned into a 2x3x40
    array of uint32's.

    Parameters
    ----------
    data : numpy.unicode\\_ or numpy.ndarray of numpy.unicode\\_
        The string or array of them to convert.

    Returns
    -------
    array : numpy.ndarray of numpy.uint32
        The result of the conversion.

    See Also
    --------
    convert_numpy_str_to_uint16
    convert_to_numpy_str

    """
    if data.nbytes == 0:
        # An empty string should be an empty uint32.
        return np.uint32([])
    else:
        # We need to calculate the new shape from the current shape,
        # which will have to be expanded along the rows to fit all the
        # characters (the dtype.itemsize gets the number of bytes in
        # each string, which is just 4 times the number of
        # characters. Then it is a mstter of getting a view of the
        # string (in flattened form so that it is contiguous) as uint32
        # and then reshaping it.
        shape = list(np.atleast_1d(data).shape)
        shape[-1] *= data.dtype.itemsize//4
        return data.ravel().view(np.uint32).reshape(tuple(shape))


def convert_to_str(data):
    """ Decodes data to the ``str`` type.

    Decodes `data` to a ``str``. If it can't be decoded, it is returned
    as is. Unsigned integers, Python ``bytes``, and Numpy strings
    (``numpy.unicode_`` and ``numpy.bytes_``). Python 3.x ``bytes`` and
    ``numpy.bytes_`` are assumed to be encoded in UTF-8.

    Parameters
    ----------
    data : some type
        Data decode into an ``str`` string.

    Returns
    -------
    s : str or data
        If `data` can be decoded into a ``str``, the decoded version is
        returned. Otherwise, `data` is returned unchanged.

    See Also
    --------
    convert_to_numpy_str
    convert_to_numpy_bytes

    """
    # How the conversion is done depends on the exact  underlying
    # type. Numpy types are handled separately. For uint types, it is
    # assumed to be stored as UTF-8, UTF-16, or UTF-32 depending on the
    # size when converting to an str. numpy.string_ is just like
    # converting a bytes. numpy.unicode has to be encoded into bytes
    # before it can be decoded back into an str. bytes is decoded
    # assuming it is in UTF-8. Otherwise, data has to be returned as is.

    if isinstance(data, (np.ndarray, np.uint8, np.uint16, np.uint32,
                  np.bytes_, np.unicode_)):
        if data.dtype.name == 'uint8':
            return data.tobytes().decode('UTF-8')
        elif data.dtype.name == 'uint16':
            return data.tobytes().decode('UTF-16')
        elif data.dtype.name == 'uint32':
            return data.tobytes().decode('UTF-32')
        elif data.dtype.char == 'S':
            return data.decode('UTF-8')
        else:
            if isinstance(data, np.ndarray):
                return data.tobytes().decode('UTF-32')
            else:
                return data.encode('UTF-32').decode('UTF-32')

    if isinstance(data, bytes):
        return data.decode('UTF-8')
    else:
        return data


def convert_to_numpy_str(data, length=None):
    """ Decodes data to Numpy unicode string (``numpy.unicode_``).

    Decodes `data` to Numpy unicode string (UTF-32), which is
    ``numpy.unicode_``, or an array of them. If it can't be decoded, it
    is returned as is. Unsigned integers, Python string types (``str``,
    ``bytes``), and ``numpy.bytes_`` are supported. If it is an array of
    ``numpy.bytes_``, an array of those all converted to
    ``numpy.unicode_`` is returned. ``bytes`` and ``numpy.bytes_`` are
    assumed to be encoded in UTF-8.

    For an array of unsigned integers, it may be desirable to make an
    array with strings of some specified length as opposed to an array
    of the same size with each element being a one element string. This
    naturally arises when converting strings to unsigned integer types
    in the first place, so it needs to be reversible.  The `length`
    parameter specifies how many to group together into a string
    (desired string length). For 1d arrays, this is along its only
    dimension. For higher dimensional arrays, it is done along each row
    (across columns). So, for a 3x5x10 input array of uints and a
    `length` of 5, the output array would be a 3x5x2 of 5 element
    strings.

    Parameters
    ----------
    data : some type
        Data decode into a Numpy unicode string.
    length : int or None, optional
        The number of consecutive elements (in the case of unsigned
        integer `data`) to compose each string in the output array from.
        ``None`` indicates the full amount for a 1d array or the number
        of columns (full length of row) for a higher dimension array.

    Returns
    -------
    s : numpy.unicode\\_ or numpy.ndarray of numpy.unicode\\_ or data
        If `data` can be decoded into a ``numpy.unicode_`` or a
        ``numpy.ndarray`` of them, the decoded version is returned.
        Otherwise, `data` is returned unchanged.

    See Also
    --------
    convert_to_str
    convert_to_numpy_bytes
    numpy.unicode_

    """
    # The method of conversion depends on its type.
    if isinstance(data, np.unicode_) or (isinstance(data, np.ndarray) \
            and data.dtype.char == 'U'):
        # It is already an np.str_ or array of them, so nothing needs to
        # be done.
        return data
    elif isinstance(data, str):
        # Easily converted through constructor.
        return np.unicode_(data)
    elif isinstance(data, (bytes, bytearray, np.bytes_)):
        # All of them can be decoded and then passed through the
        # constructor.
        return np.unicode_(data.decode('UTF-8'))
    elif isinstance(data, (np.uint8, np.uint16)):
        # They are single UTF-8 or UTF-16 scalars, which can be wrapped
        # into an array and recursed.
        return convert_to_numpy_str(np.atleast_1d(data))[0]
    elif isinstance(data, np.uint32):
        # It is just the uint32 version of the character, so it just
        # needs to be have the dtype essentially changed by having its
        # bytes read into ndarray.
        return np.ndarray(shape=tuple(), dtype='U1',
                          buffer=data)[()]
    elif isinstance(data, np.ndarray) and data.dtype.char == 'S':
        return np.char.encode(data, 'UTF-32')
    elif isinstance(data, np.ndarray) \
            and data.dtype.name in ('uint8', 'uint16', 'uint32'):
        # It is an ndarray of some uint type. How it is converted
        # depends on its shape. If its shape is just (), then it is just
        # a scalar wrapped in an array, which can be converted by
        # recursing the scalar value back into this function.
        shape = list(data.shape)
        if len(shape) == 0:
            return convert_to_numpy_str(data[()])

        # As there are more than one element, it gets a bit more
        # complicated. We need to take the subarrays of the specified
        # length along columns (1D arrays will be treated as row arrays
        # here), each of those converted to an str_ scalar (normal
        # string) and stuffed into a new array.
        #
        # If the length was not given, it needs to be set to full. Then
        # the shape of the new array needs to be calculated (divide the
        # appropriate dimension, which depends on the number of
        # dimentions).
        if len(shape) == 1:
            if length is None:
                length = shape[0]
            new_shape = (shape[0]//length,)
        else:
            if length is None:
                length = shape[-1]
            new_shape = copy.deepcopy(shape)
            new_shape[-1] //= length

        # numpy.char.decode will be used to decode. It needs the
        # encoding (UTF-8/16/32) which is gotten from the dtype. But it
        # also needs the data to be in big endian format, so it must be
        # byteswapped if it isn't. Without the swapping, an error occurs
        # since trailing nulls are dropped in numpy bytes_ arrays. The
        # dtype for each string element is just 'SX' where X is the
        # number of bytes.
        if data.dtype.name == 'uint8':
            encoding = 'UTF-8'
            swapbytes = False
            dt = 'S' + str(length)
        else:
            if data.dtype.name == 'uint16':
                encoding = 'UTF-16BE'
                dt = 'S' + str(2 * length)
            else:
                encoding = 'UTF-32BE'
                dt = 'S' + str(4 * length)
            if (data.dtype.byteorder == '<'
                or (sys.byteorder == 'little'
                    and data.dtype.byteorder == '=')):
                swapbytes = True
            else:
                swapbytes = False
        # Copy is needed to prevent errors.
        if swapbytes:
            return np.char.decode(data.copy().byteswap().view(dt),
                                  encoding)
        else:
            return np.char.decode(data.copy().view(dt), encoding)
    else:
        # Couldn't figure out what it is, so nothing can be done but
        # return it as is.
        return data


def convert_to_numpy_bytes(data, length=None):
    """ Decodes data to Numpy UTF-8 econded string (``numpy.bytes_``).

    Decodes `data` to a Numpy UTF-8 encoded string, which is
    ``numpy.bytes_``, or an array of them in which case it will be ASCII
    encoded instead. If it can't be decoded, it is returned as
    is. Unsigned integers, Python string types (``str``, ``bytes``), and
    ``numpy.unicode_`` (UTF-32) are supported.

    For an array of unsigned integers, it may be desirable to make an
    array with strings of some specified length as opposed to an array
    of the same size with each element being a one element string. This
    naturally arises when converting strings to unsigned integer types
    in the first place, so it needs to be reversible.  The `length`
    parameter specifies how many to group together into a string
    (desired string length). For 1d arrays, this is along its only
    dimension. For higher dimensional arrays, it is done along each row
    (across columns). So, for a 3x5x10 input array of uints and a
    `length` of 5, the output array would be a 3x5x2 of 5 element
    strings.

    Parameters
    ----------
    data : some type
        Data decode into a Numpy UTF-8 encoded string/s.
    length : int or None, optional
        The number of consecutive elements (in the case of unsigned
        integer `data`) to compose each string in the output array from.
        ``None`` indicates the full amount for a 1d array or the number
        of columns (full length of row) for a higher dimension array.

    Returns
    -------
    b : numpy.bytes\\_ or numpy.ndarray of numpy.bytes\\_ or data
        If `data` can be decoded into a ``numpy.bytes_`` or a
        ``numpy.ndarray`` of them, the decoded version is returned.
        Otherwise, `data` is returned unchanged.

    See Also
    --------
    convert_to_str
    convert_to_numpy_str
    numpy.bytes_

    """
    # The method of conversion depends on its type.
    if isinstance(data, np.bytes_) or (isinstance(data, np.ndarray) \
            and data.dtype.char == 'S'):
        # It is already an np.bytes_ or array of them, so nothing needs
        # to be done.
        return data
    elif isinstance(data, (bytes, bytearray)):
        # Easily converted through constructor.
        return np.bytes_(data)
    elif isinstance(data, str):
        return np.bytes_(data.encode('UTF-8'))
    elif isinstance(data, (np.uint16, np.uint32)):
        # They are single UTF-16 or UTF-32 scalars, and are easily
        # converted to a UTF-8 string and then passed through the
        # constructor.
        return np.bytes_(convert_to_str(data).encode('UTF-8'))
    elif isinstance(data, np.uint8):
        # It is just the uint8 version of the character, so it just
        # needs to be have the dtype essentially changed by having its
        # bytes read into ndarray.
        return np.ndarray(shape=(), dtype='S1',
                          buffer=data)[()]
    elif isinstance(data, np.ndarray) and data.dtype.char == 'U':
        # We just need to convert it elementwise.
        new_data = np.zeros(shape=data.shape,
                            dtype='S' + str(data.dtype.itemsize))
        for index, x in np.ndenumerate(data):
            new_data[index] = np.bytes_(x.encode('UTF-8'))
        return new_data
    elif isinstance(data, np.ndarray) \
            and data.dtype.name in ('uint8', 'uint16', 'uint32'):
        # It is an ndarray of some uint type. How it is converted
        # depends on its shape. If its shape is just (), then it is just
        # a scalar wrapped in an array, which can be converted by
        # recursing the scalar value back into this function.
        shape = list(data.shape)
        if len(shape) == 0:
            return convert_to_numpy_bytes(data[()])

        # As there are more than one element, it gets a bit more
        # complicated. We need to take the subarrays of the specified
        # length along columns (1D arrays will be treated as row arrays
        # here), each of those converted to an str_ scalar (normal
        # string) and stuffed into a new array.
        #
        # If the length was not given, it needs to be set to full. Then
        # the shape of the new array needs to be calculated (divide the
        # appropriate dimension, which depends on the number of
        # dimentions).
        if len(shape) == 1:
            if length is None:
                length2 = shape[0]
                new_shape = (shape[0],)
            else:
                length2 = length
                new_shape = (shape[0]//length2,)
        else:
            if length is None:
                length2 = shape[-1]
            else:
                length2 = length
            new_shape = copy.deepcopy(shape)
            new_shape[-1] //= length2

        # If it is uint8, we can just use the object directly as the
        # buffer for the new data.
        if data.dtype.name == 'uint8':
            return np.ndarray(shape=new_shape, dtype='S'+str(length2),
                              buffer=data)

        # The new array can be made as all zeros (nulls) with enough
        # padding to hold everything (dtype='UL' where 'L' is the
        # length). It will start out as a 1d array and be reshaped into
        # the proper shape later (makes indexing easier).
        new_data = np.zeros(shape=(np.prod(new_shape),),
                            dtype='S'+str(length2))

        # With data flattened into a 1d array, we just need to take
        # length sized chunks, convert them (if they are uint8 or 16,
        # then decode to str first, if they are uint32, put them as an
        # input buffer for an ndarray of type 'U').
        data = data.ravel()
        for i in range(0, new_data.shape[0]):
            chunk = data[(i*length2):((i+1)*length2)]
            new_data[i] = np.bytes_(
                convert_to_str(chunk).encode('UTF-8'))

        # Only thing is left is to reshape it.
        return new_data.reshape(tuple(new_shape))
    else:
        # Couldn't figure out what it is, so nothing can be done but
        # return it as is.
        return data


def decode_complex(data, complex_names=(None, None)):
    """ Decodes possibly complex data read from an HDF5 file.

    Decodes possibly complex datasets read from an HDF5 file. HDF5
    doesn't have a native complex type, so they are stored as
    H5T_COMPOUND types with fields such as 'r' and 'i' for the real and
    imaginary parts. As there is no standardization for field names, the
    field names have to be given explicitly, or the fieldnames in `data`
    analyzed for proper decoding to figure out the names. A variety of
    reasonably expected combinations of field names are checked and used
    if available to decode. If decoding is not possible, it is returned
    as is.

    Parameters
    ----------
    data : arraylike
        The data read from an HDF5 file, that might be complex, to
        decode into the proper Numpy complex type.
    complex_names : tuple of 2 str and/or Nones, optional
        ``tuple`` of the names to use (in order) for the real and
        imaginary fields. A ``None`` indicates that various common
        field names should be tried.

    Returns
    -------
    c : decoded data or data
        If `data` can be decoded into a complex type, the decoded
        complex version is returned. Otherwise, `data` is returned
        unchanged.

    See Also
    --------
    encode_complex

    Notes
    -----
    Currently looks for real field names of ``('r', 're', 'real')`` and
    imaginary field names of ``('i', 'im', 'imag', 'imaginary')``
    ignoring case.

    """
    # Now, complex types are stored in HDF5 files as an H5T_COMPOUND type
    # with fields along the lines of ('r', 're', 'real') and ('i', 'im',
    # 'imag', 'imaginary') for the real and imaginary parts, which most
    # likely won't be properly extracted back into making a Python
    # complex type unless the proper h5py configuration is set. Since we
    # can't depend on it being set and adjusting it is hazardous (the
    # setting is global), it is best to just decode it manually. These
    # fields are obtained from the fields of its dtype. Obviously, if
    # there are no fields, then there is nothing to do.
    if data.dtype.fields is None:
        return data

    fields = list(data.dtype.fields)

    # If there aren't exactly two fields, then it can't be complex.
    if len(fields) != 2:
        return data

    # We need to grab the field names for the real and imaginary
    # parts. This will be done by seeing which list, if any, each field
    # is and setting variables to the proper name if it is in it (they
    # are initialized to None so that we know if one isn't found).

    real_fields = ['r', 're', 'real']
    imag_fields = ['i', 'im', 'imag', 'imaginary']

    cnames = list(complex_names)
    for s in fields:
        if s.lower() in real_fields:
            cnames[0] = s
        elif s.lower() in imag_fields:
            cnames[1] = s

    # If the real and imaginary fields were found, construct the complex
    # form from the fields. This is done by finding the complex type
    # that they cast to, making an array, and then setting the
    # parts. Otherwise, return what we were given because it isn't in
    # the right form.
    if cnames[0] is not None and cnames[1] is not None:
        cdata = np.result_type(
            data[cnames[0]].dtype,
            data[cnames[1]].dtype, 'complex64').type(data[cnames[0]])
        cdata.imag = data[cnames[1]]
        return cdata
    else:
        return data


def encode_complex(data, complex_names):
    """ Encodes complex data to having arbitrary complex field names.

    Encodes complex `data` to have the real and imaginary field names
    given in `complex_numbers`. This is needed because the field names
    have to be set so that it can be written to an HDF5 file with the
    right field names (HDF5 doesn't have a native complex type, so
    H5T_COMPOUND have to be used).

    Parameters
    ----------
    data : arraylike
        The data to encode as a complex type with the desired real and
        imaginary part field names.
    complex_names : tuple of 2 str
        ``tuple`` of the names to use (in order) for the real and
        imaginary fields.

    Returns
    -------
    d : encoded data
        `data` encoded into having the specified field names for the
        real and imaginary parts.

    See Also
    --------
    decode_complex

    """
    # Grab the dtype name, and convert it to the right non-complex type
    # if it isn't already one.
    dtype_name = data.dtype.name
    if dtype_name[0:7] == 'complex':
        dtype_name = 'float' + str(int(float(dtype_name[7:])/2))

    # Create the new version of the data with the right field names for
    # the real and complex parts. This is easy to do with putting the
    # right dtype in the view function.
    return data.view([(complex_names[0], dtype_name),
                      (complex_names[1], dtype_name)])


def get_attribute(target, name):
    """ Gets an attribute from a Dataset or Group.

    Gets the value of an Attribute if it is present (get ``None`` if
    not).

    Parameters
    ----------
    target : Dataset or Group
        Dataset or Group to get the attribute of.
    name : str
        Name of the attribute to get.

    Returns
    -------
    value
        The value of the attribute if it is present, or ``None`` if it
        isn't.

    """
    if name not in target.attrs:
        return None
    else:
        return target.attrs[name]


def convert_attribute_to_string(value):
    """ Convert an attribute value to a string.

    Converts the attribute value to a string if possible (get ``None``
    if isn't a string type).

    .. versionadded:: 0.2

    Parameters
    ----------
    value :
        The Attribute value.

    Returns
    -------
    s : str or None
        The ``str`` value of the attribute if the conversion is
        possible, or ``None`` if not.

    """
    if value is None:
        return value
    elif isinstance(value, str):
        return value
    elif isinstance(value, bytes):
        return value.decode()
    elif isinstance(value, np.unicode_):
        return str(value)
    elif isinstance(value, np.bytes_):
        return value.decode()
    else:
        return None


def get_attribute_string(target, name):
    """ Gets a string attribute from a Dataset or Group.

    Gets the value of an Attribute that is a string if it is present
    (get ``None`` if it is not present or isn't a string type).

    Parameters
    ----------
    target : Dataset or Group
        Dataset or Group to get the string attribute of.
    name : str
        Name of the attribute to get.

    Returns
    -------
    s : str or None
        The ``str`` value of the attribute if it is present, or ``None``
        if it isn't or isn't a type that can be converted to ``str``

    """
    return convert_attribute_to_string(get_attribute(target, name))


def convert_attribute_to_string_array(value):
    """ Converts an Attribute value to a string array.

    Converts the value of an Attribute to a string array if possible
    (get ``None`` if not).

    .. versionadded:: 0.2

    Parameters
    ----------
    value :
        The Attribute value.

    Returns
    -------
    array : list of str or None
        The converted string array value if possible, or ``None`` if it
        isn't.

    """
    if value is None:
        return value
    return [convert_to_str(x) for x in value]


def get_attribute_string_array(target, name):
    """ Gets a string array Attribute from a Dataset or Group.

    Gets the value of an Attribute that is a string array if it is
    present (get ``None`` if not).

    Parameters
    ----------
    target : Dataset or Group
        Dataset or Group to get the attribute of.
    name : str
        Name of the string array Attribute to get.

    Returns
    -------
    array : list of str or None
        The string array value of the Attribute if it is present, or
        ``None`` if it isn't.

    """
    return convert_attribute_to_string_array(get_attribute(target,
                                                           name))


def set_attribute(target, name, value):
    """ Sets an attribute on a Dataset or Group.

    If the attribute `name` doesn't exist yet, it is created. If it
    already exists, it is overwritten if it differs from `value`.

    Notes
    -----
    ``set_attributes_all`` is the fastest way to set and delete
    Attributes in bulk.

    Parameters
    ----------
    target : Dataset or Group
        Dataset or Group to set the attribute of.
    name : str
        Name of the attribute to set.
    value : numpy type other than numpy.unicode\\_
        Value to set the attribute to.

    See Also
    --------
    set_attributes_all

    """
    try:
        target.attrs.modify(name, value)
    except:
        target.attrs.create(name, value)


def set_attribute_string(target, name, value):
    """ Sets an attribute to a string on a Dataset or Group.

    If the attribute `name` doesn't exist yet, it is created. If it
    already exists, it is overwritten if it differs from `value`.

    Notes
    -----
    ``set_attributes_all`` is the fastest way to set and delete
    Attributes in bulk.

    Parameters
    ----------
    target : Dataset or Group
        Dataset or Group to set the string attribute of.
    name : str
        Name of the attribute to set.
    value : string
        Value to set the attribute to. Can be any sort of string type
        that will convert to a ``numpy.bytes_``

    See Also
    --------
    set_attributes_all

    """
    set_attribute(target, name, np.bytes_(value))


def set_attribute_string_array(target, name, string_list):
    """ Sets an attribute to an array of string on a Dataset or Group.

    If the attribute `name` doesn't exist yet, it is created. If it
    already exists, it is overwritten with the list of string
    `string_list` (they will be vlen strings).

    Notes
    -----
    ``set_attributes_all`` is the fastest way to set and delete
    Attributes in bulk.

    Parameters
    ----------
    target : Dataset or Group
        Dataset or Group to set the string array attribute of.
    name : str
        Name of the attribute to set.
    string_list : list of str
        List of strings to set the attribute to. Strings must be ``str``

    See Also
    --------
    set_attributes_all

    """
    s_list = [convert_to_str(s) for s in string_list]
    target.attrs.create(name, s_list,
                        dtype=h5py.special_dtype(vlen=str))


def set_attributes_all(target, attributes, discard_others=True):
    """ Set Attributes in bulk and optionally discard others.

    Sets each Attribute in turn (modifying it in place if possible if it
    is already present) and optionally discarding all other Attributes
    not explicitly set. This function yields much greater performance
    than the required individual calls to ``set_attribute``,
    ``set_attribute_string``, ``set_attribute_string_array`` and
    ``del_attribute`` put together.

    .. versionadded:: 0.2

    Parameters
    ----------
    target : Dataset or Group
        Dataset or Group to set the Attributes of.
    attributes : dict
        The Attributes to set. The keys (``str``) are the names. The
        values are ``tuple`` of the Attribute kind and the value to
        set. Valid kinds are ``'string_array'``, ``'string'``, and
        ``'value'``. The values must correspond to what
        ``set_attribute_string_array``, ``set_attribute_string`` and
        ``set_attribute`` would take respectively.
    discard_others : bool, optional
        Whether to discard all other Attributes not explicitly set
        (default) or not.

    See Also
    --------
    set_attribute
    set_attribute_string
    set_attribute_string_array

    """
    attrs = target.attrs
    existing = dict()
    read_all_attributes_into(attrs, existing)
    # Generate special dtype for string arrays.
    str_arr_dtype = h5py.special_dtype(vlen=str)
    # Go through each attribute. If it is already present, modify it if
    # possible and create it otherwise (deletes old value.)
    for k, (kind, value) in attributes.items():
        if kind == 'string_array':
            attrs.create(k, [convert_to_str(s) for s in value],
                         dtype=str_arr_dtype)
        else:
            if kind == 'string':
                value = np.bytes_(value)
            if k not in existing:
                attrs.create(k, value)
            elif k == 'MATLAB_fields':
                if not np.array_equal(value, existing[k]):
                    attrs.create(k, value)
            else:
                try:
                    if value.dtype == existing[k].dtype \
                            and value.shape == existing[k].shape:
                        attrs.modify(k, value)
                except:
                    attrs.create(k, value)
    # Discard all other attributes.
    if discard_others:
        for k in set(existing) - set(attributes):
            del attrs[k]


def del_attribute(target, name):
    """ Deletes an attribute on a Dataset or Group.

    If the attribute `name` exists, it is deleted.

    Parameters
    ----------
    target : Dataset or Group
        Dataset or Group to delete attribute of.
    name : str
        Name of the attribute to delete.

    """
    try:
        del target.attrs[name]
    except:
        pass
