# Copyright (c) 2013-2023, Freja Nordsiek
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

""" Module for the classes to marshall Python types to/from file.

"""

import sys
import posixpath
import collections

try:
    from pkg_resources import parse_version
except:
    from distutils.version import StrictVersion as parse_version

import numpy as np
import h5py

from hdf5storage.utilities import *
from hdf5storage import lowlevel
from hdf5storage.lowlevel import write_data, read_data


# Ubuntu 12.04's h5py doesn't have __version__ set so we need to try to
# grab the version and if it isn't available, just assume it is 2.0.
try:
    _H5PY_VERSION = h5py.__version__
except:
    _H5PY_VERSION = '2.0'


def write_object_array(f, data, options):
    """ Writes an array of objects recursively.

    Writes the elements of the given object array recursively in the
    HDF5 Group ``options.group_for_references`` and returns an
    ``h5py.Reference`` array to all the elements.

    Parameters
    ----------
    f : h5py.File
        The HDF5 file handle that is open.
    data : numpy.ndarray of objects
        Numpy object array to write the elements of.
    options : hdf5storage.core.Options
        hdf5storage options object.

    Returns
    -------
    numpy.ndarray of h5py.Reference
        A reference array pointing to all the elements written to the
        HDF5 file. For those that couldn't be written, the respective
        element points to the canonical empty.

    Raises
    ------
    TypeNotMatlabCompatibleError
        If writing a type not compatible with MATLAB and
        `options.action_for_matlab_incompatible` is set to ``'error'``.

    See Also
    --------
    read_object_array
    hdf5storage.Options.group_for_references
    h5py.Reference

    """
    # We need to grab the special reference dtype and make an empty
    # array to store all the references in.
    ref_dtype = h5py.special_dtype(ref=h5py.Reference)
    data_refs = np.zeros(shape=data.shape, dtype='object')

    # We need to make sure that the group to hold references is present,
    # and create it if it isn't.

    if options.group_for_references not in f:
        f.create_group(options.group_for_references)

    grp2 = f[options.group_for_references]

    if not isinstance(grp2, h5py.Group):
        del f[options.group_for_references]
        f.create_group(options.group_for_references)
        grp2 = f[options.group_for_references]

    # The Dataset 'a' needs to be present as the canonical empty. It is
    # just and np.uint32/64([0, 0]) with its a MATLAB_class of
    # 'canonical empty' and the 'MATLAB_empty' attribute set. If it
    # isn't present or is incorrectly formatted, it is created
    # truncating anything previously there.
    if 'a' not in grp2 or grp2['a'].shape != (2,) \
            or not grp2['a'].dtype.name.startswith('uint') \
            or np.any(grp2['a'][...] != np.uint64([0, 0])) \
            or get_attribute_string(grp2['a'], 'MATLAB_class') != \
            'canonical empty' \
            or get_attribute(grp2['a'], 'MATLAB_empty') != 1:
        if 'a' in grp2:
            del grp2['a']
        grp2.create_dataset('a', data=np.uint64([0, 0]))
        set_attribute_string(grp2['a'], 'MATLAB_class',
                             'canonical empty')
        set_attribute(grp2['a'], 'MATLAB_empty',
                      np.uint8(1))

    # Go through all the elements of data and write them, gabbing their
    # references and putting them in data_refs. They will be put in
    # group_for_references, which is also what the H5PATH needs to be
    # set to if we are doing MATLAB compatibility (otherwise, the
    # attribute needs to be deleted). If an element can't be written
    # (doing matlab compatibility, but it isn't compatible with matlab
    # and action_for_matlab_incompatible option is True), the reference
    # to the canonical empty will be used for the reference array to
    # point to.
    for index, x in np.ndenumerate(data):
        data_refs[index] = None
        name_for_ref = next_unused_name_in_group(grp2, 16)
        write_data(f, grp2, name_for_ref, x, None, options)
        if name_for_ref in grp2:
            data_refs[index] = grp2[name_for_ref].ref
            if options.matlab_compatible:
                set_attribute_string(grp2[name_for_ref],
                                     'H5PATH', grp2.name)
            else:
                del_attribute(grp2[name_for_ref], 'H5PATH')
        else:
            data_refs[index] = grp2['a'].ref

    # Now, the dtype needs to be changed to the reference type and the
    # whole thing copied over to data_to_store.
    return data_refs.astype(ref_dtype).copy()


def read_object_array(f, data, options):
    """ Reads an array of objects recursively.

    Read the elements of the given HDF5 Reference array recursively
    in the and constructs a ``numpy.object_`` array from its elements,
    which is returned.

    Parameters
    ----------
    f : h5py.File
        The HDF5 file handle that is open.
    data : numpy.ndarray of h5py.Reference
        The array of HDF5 References to read and make an object array
        from.
    options : hdf5storage.core.Options
        hdf5storage options object.

    Raises
    ------
    NotImplementedError
        If reading the object from file is currently not supported.

    Returns
    -------
    numpy.ndarray of numpy.object\\_
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
    for index, x in np.ndenumerate(data):
        try:
            data_derefed[index] = read_data(f, f[x].parent, \
                posixpath.basename(f[x].name), options)
        except:
            raise
    return data_derefed


class TypeMarshaller(object):
    """ Base class for marshallers of Python types.

    Base class providing the class interface for marshallers of Python
    types to/from disk. All marshallers should inherit from this class
    or at least replicate its functionality. This includes several
    attributes that are needed in order for reading/writing methods to
    know if it is the appropriate marshaller to use and methods to
    actually do the reading and writing.

    Subclasses should run this class's ``__init__()`` first
    thing. Inheritance information is in the **Notes** section of each
    method. Generally, ``read``, ``write``, and ``write_metadata`` need
    to be overridden and the different attributes set to the proper
    values.

    For marshalling types that are containers of other data, one will
    need to appropriate read/write them with the lowlevel functions
    ``lowlevel.read_data`` and ``lowlevel.write_data``.

    Attributes
    ----------
    python_attributes : set of str
        Attributes used to store type information.
    matlab_attributes : set of str
        Attributes used for MATLAB compatibility.
    types : list of types
        Types the marshaller can work on.
    python_type_strings : list of str
        Type strings of readable types.
    matlab_classes : list of str
        Readable MATLAB classes.

    See Also
    --------
    hdf5storage.core.Options
    h5py.Dataset
    h5py.Group
    h5py.AttributeManager
    hdf5storage.lowlevel.read_data
    hdf5storage.lowlevel.write_data

    """
    def __init__(self):
        #: Attributes used to store type information.
        #:
        #: set of str
        #:
        #: ``set`` of attribute names the marshaller uses when
        #: an ``Option.store_python_metadata`` is ``True``.
        self.python_attributes = set(['Python.Type'])

        #: Attributes used for MATLAB compatibility.
        #:
        #: ``set`` of ``str``
        #:
        #: ``set`` of attribute names the marshaller uses when maintaing
        #: Matlab HDF5 based mat file compatibility
        #: (``Option.matlab_compatible`` is ``True``).
        self.matlab_attributes = set(['H5PATH'])

        #: List of Python types that can be marshalled.
        #:
        #: list of types
        #:
        #: ``list`` of the types (gotten by doing ``type(data)``) that the
        #: marshaller can marshall. Default value is ``[]``.
        self.types = []

        #: Type strings of readable types.
        #:
        #: list of str
        #:
        #: ``list`` of the ``str`` that the marshaller would put in the
        #: HDF5 attribute 'Python.Type' to identify the Python type to be
        #: able to read it back correctly. Default value is ``[]``.
        self.python_type_strings = []

        #: MATLAB class strings of readable types.
        #:
        #: list of str
        #:
        #: ``list`` of the MATLAB class ``str`` that the marshaller can
        #: read into Python objects. Default value is ``[]``.
        self.matlab_classes = []

    def get_type_string(self, data, type_string):
        """ Gets type string.

        Finds the type string for 'data' contained in
        ``python_type_strings`` using its ``type``. Non-``None``
        'type_string` overrides whatever type string is looked up.
        The override makes it easier for subclasses to convert something
        that the parent marshaller can write to disk but still put the
        right type string in place).

        Parameters
        ----------
        data : type to be marshalled
            The Python object that is being written to disk.
        type_string : str or None
            If it is a ``str``, it overrides any looked up type
            string. ``None`` means don't override.

        Returns
        -------
        str
            The type string associated with 'data'. Will be
            'type_string' if it is not ``None``.

        Notes
        -----
        Subclasses probably do not need to override this method.

        """
        if type_string is not None:
            return type_string
        else:
            i = self.types.index(type(data))
            return self.python_type_strings[i]

    def write(self, f, grp, name, data, type_string, options):
        """ Writes an object's metadata to file.

        Writes the Python object 'data' to 'name' in h5py.Group 'grp'.

        Parameters
        ----------
        f : h5py.File
            The HDF5 file handle that is open.
        grp : h5py.Group or h5py.File
            The parent HDF5 Group (or File if at '/') that contains the
            object with the specified name.
        name : str
            Name of the object.
        data
            The object to write to file.
        type_string : str or None
            The type string for `data`. If it is ``None``, one will have
            to be gotten by ``get_type_string``.
        options : hdf5storage.core.Options
            hdf5storage options object.

        Raises
        ------
        NotImplementedError
            If writing 'data' to file is currently not supported.
        TypeNotMatlabCompatibleError
            If writing a type not compatible with MATLAB and
            `options.action_for_matlab_incompatible` is set to
            ``'error'``.

        Notes
        -----
        Must be overridden in a subclass because a
        ``NotImplementedError`` is thrown immediately.

        See Also
        --------
        hdf5storage.lowlevel.write_data

        """
        raise NotImplementedError('Can''t write data type: '
                                  + str(type(data)))

    def write_metadata(self, f, grp, name, data, type_string, options):
        """ Writes an object to file.

        Writes the metadata for a Python object `data` to file at `name`
        in h5py.Group `grp`. Metadata is written to HDF5
        Attributes. Existing Attributes that are not being used are
        deleted.

        Parameters
        ----------
        f : h5py.File
            The HDF5 file handle that is open.
        grp : h5py.Group or h5py.File
            The parent HDF5 Group (or File if at '/') that contains the
            object with the specified name.
        name : str
            Name of the object.
        data
            The object to write to file.
        type_string : str or None
            The type string for `data`. If it is ``None``, one will have
            to be gotten by ``get_type_string``.
        options : hdf5storage.core.Options
            hdf5storage options object.

        Notes
        -----
        The attribute 'Python.Type' is set to the type string. All H5PY
        Attributes not in ``python_attributes`` and/or
        ``matlab_attributes`` (depending on the attributes of 'options')
        are deleted. These are needed functions for writting essentially
        any Python object, so subclasses should probably call the
        baseclass's version of this function if they override it and
        just provide the additional functionality needed. This requires
        that the names of any additional HDF5 Attributes are put in the
        appropriate set.

        """
        # Make sure we have a complete type_string.
        type_string = self.get_type_string(data, type_string)

        # The metadata that is written depends on the format.

        dsetgrp = grp[name]
        if options.store_python_metadata:
            set_attribute_string(dsetgrp, 'Python.Type', type_string)

        # If we are not storing python information or doing MATLAB
        # compatibility, then attributes not in the python and/or
        # MATLAB lists need to be removed.

        attributes_used = set()

        if options.store_python_metadata:
            attributes_used |= self.python_attributes

        if options.matlab_compatible:
            attributes_used |= self.matlab_attributes

        for attribute in (set(dsetgrp.attrs.keys()) - attributes_used):
            del_attribute(dsetgrp, attribute)

    def read(self, f, grp, name, options):
        """ Read a Python object from file.

        Reads the Python object 'name' from the HDF5 Group 'grp', if
        possible, and returns it.

        Parameters
        ----------
        f : h5py.File
            The HDF5 file handle that is open.
        grp : h5py.Group or h5py.File
            The parent HDF5 Group (or File if at '/') that contains the
            object with the specified name.
        name : str
            Name of the object.
        options : hdf5storage.core.Options
            hdf5storage options object.

        Raises
        ------
        NotImplementedError
            If reading the object from file is currently not supported.

        Returns
        -------
        data
            The Python object 'name' in the HDF5 Group 'grp'.

        Notes
        -----
        Must be overridden in a subclass because a
        ``NotImplementedError`` is thrown immediately.

        See Also
        --------
        hdf5storage.lowlevel.read_data

        """
        raise NotImplementedError('Can''t read data: ' + name)


class NumpyScalarArrayMarshaller(TypeMarshaller):
    def __init__(self):
        TypeMarshaller.__init__(self)
        self.python_attributes |= set(['Python.Shape', 'Python.Empty',
                                   'Python.numpy.UnderlyingType',
                                   'Python.numpy.Container',
                                   'Python.Fields'])
        self.matlab_attributes |= set(['MATLAB_class', 'MATLAB_empty',
                                      'MATLAB_int_decode',
                                      'MATLAB_fields'])
        # As np.str_ is the unicode type string in Python 3 and the bare
        # bytes string in Python 2, we have to use np.unicode_ which is
        # or points to the unicode one in both versions.
        self.types = [np.ndarray, np.matrix,
                      np.chararray, np.core.records.recarray,
                      np.bool_, np.void,
                      np.uint8, np.uint16, np.uint32, np.uint64,
                      np.int8, np.int16, np.int32, np.int64,
                      np.float32, np.float64,
                      np.complex64, np.complex128,
                      np.bytes_, np.unicode_, np.object_]
        self._numpy_types = list(self.types)
        # Using Python 3 type strings.
        self.python_type_strings = ['numpy.ndarray', 'numpy.matrix',
                                    'numpy.chararray',
                                    'numpy.recarray',
                                    'numpy.bool_', 'numpy.void',
                                    'numpy.uint8', 'numpy.uint16',
                                    'numpy.uint32', 'numpy.uint64',
                                    'numpy.int8', 'numpy.int16',
                                    'numpy.int32', 'numpy.int64',
                                    'numpy.float32', 'numpy.float64',
                                    'numpy.complex64',
                                    'numpy.complex128',
                                    'numpy.bytes_', 'numpy.str_',
                                    'numpy.object_']

        # If we are storing in MATLAB format, we will need to be able to
        # set the MATLAB_class attribute. The different numpy types just
        # need to be properly mapped to the right strings. Some types do
        # not have a string since MATLAB does not support them.

        self.__MATLAB_classes = {np.bool_: 'logical',
                                 np.uint8: 'uint8',
                                 np.uint16: 'uint16',
                                 np.uint32: 'uint32',
                                 np.uint64: 'uint64',
                                 np.int8: 'int8',
                                 np.int16: 'int16',
                                 np.int32: 'int32',
                                 np.int64: 'int64',
                                 np.float32: 'single',
                                 np.float64: 'double',
                                 np.complex64: 'single',
                                 np.complex128: 'double',
                                 np.bytes_: 'char',
                                 np.unicode_: 'char',
                                 np.object_: 'cell'}

        # Make a dict to look up the opposite direction (given a matlab
        # class, what numpy type to use.

        self.__MATLAB_classes_reverse = {'logical': np.bool_,
                                         'uint8': np.uint8,
                                         'uint16': np.uint16,
                                         'uint32': np.uint32,
                                         'uint64': np.uint64,
                                         'int8': np.int8,
                                         'int16': np.int16,
                                         'int32': np.int32,
                                         'int64': np.int64,
                                         'single': np.float32,
                                         'double': np.float64,
                                         'char': np.unicode_,
                                         'cell': np.object_,
                                         'canonical empty': np.float64,
                                         'struct': np.object_}


        # Set matlab_classes to the supported classes (the values).
        self.matlab_classes = list(self.__MATLAB_classes.values())

        # For h5py >= 2.2, half precisions (np.float16) are supported.
        if parse_version(_H5PY_VERSION) \
                >= parse_version('2.2'):
            self.types.append(np.float16)
            self.python_type_strings.append('numpy.float16')

    def write(self, f, grp, name, data, type_string, options):
        # If we are doing matlab compatibility and the data type is not
        # one of those that is supported for matlab, skip writing the
        # data or throw an error if appropriate. structured ndarrays and
        # recarrays are compatible if the
        # structured_numpy_ndarray_as_struct option is set.
        if options.matlab_compatible \
                and not (data.dtype.type in self.__MATLAB_classes \
                or (data.dtype.fields is not None \
                and options.structured_numpy_ndarray_as_struct)):
            if options.action_for_matlab_incompatible == 'error':
                raise lowlevel.TypeNotMatlabCompatibleError( \
                    'Data type ' + data.dtype.name
                    + ' not supported by MATLAB.')
            elif options.action_for_matlab_incompatible == 'discard':
                return

        # Need to make a set of data that will be stored. It will start
        # out as a copy of data and then be steadily manipulated.

        data_to_store = data.copy()

        # recarrays must be converted to structured ndarrays in order
        # for h5py to be able to write them.
        if isinstance(data_to_store, np.core.records.recarray):
            data_to_store = data_to_store.view(np.ndarray)

        # Optionally convert bytes_ strings to UTF-16, if possible (all
        # are in the ASCII character set). This is done by simply
        # converting to uint16's and checking that each one's value is
        # less than 128 (in the ASCII character set). This will require
        # making them at least 1 dimensional. If it fails, throw an
        # exception.
        if data.dtype.type == np.bytes_ \
                and options.convert_numpy_bytes_to_utf16:
            if data_to_store.nbytes == 0:
                data_to_store = np.uint16([])
            else:
                data_to_store = np.uint16(np.atleast_1d( \
                    data_to_store).view(np.ndarray).view(np.uint8))
                if np.any(data_to_store >= 128):
                    raise NotImplementedError( \
                        'Can''t write non-ASCII numpy.bytes_.')

        # As of 2013-12-13, h5py cannot write numpy.str_ (UTF-32
        # encoding) types (its numpy.unicode_ in Python 2, which is an
        # alias for it in Python 3). If the option is set to try to
        # convert them to UTF-16, then an attempt at the conversion is
        # made. If no conversion is to be done, the conversion throws an
        # exception (a UTF-32 character had no UTF-16 equivalent), or a
        # UTF-32 character gets turned into a UTF-16 doublet (the
        # increase in the number of columns will be by a factor more
        # than the length of the strings); then it will be simply
        # converted to uint32's byte for byte instead.

        if data.dtype.type == np.unicode_:
            new_data = None
            if options.convert_numpy_str_to_utf16:
                try:
                    new_data = convert_numpy_str_to_uint16( \
                        data_to_store)
                except:
                    pass
            if new_data is None or (type(data_to_store) == np.unicode_ \
                    and len(data_to_store) != len(new_data)) \
                    or (isinstance(data_to_store, np.ndarray) \
                    and new_data.shape[-1] != data_to_store.shape[-1] \
                    * (data_to_store.dtype.itemsize//4)):
                data_to_store = convert_numpy_str_to_uint32( \
                    data_to_store)
            else:
                data_to_store = new_data

        # Convert scalars to arrays if that option is set. For 1d
        # arrays, an option determines whether they become row or column
        # vectors.

        if options.make_atleast_2d:
            new_data = np.atleast_2d(data_to_store)
            if len(data_to_store.shape) == 1 \
                    and options.oned_as == 'column':
                new_data = new_data.T
            data_to_store = new_data

        # Reverse the dimension order if that option is set.

        if options.reverse_dimension_order:
            data_to_store = data_to_store.T

        # Bools need to be converted to uint8 if the option is given.
        if data_to_store.dtype.name == 'bool' \
                and options.convert_bools_to_uint8:
            data_to_store = np.uint8(data_to_store)

        # If data is empty, we instead need to store the shape of the
        # array if the appropriate option is set.

        if options.store_shape_for_empty and (data.size == 0 \
                or ((data.dtype.type == np.bytes_ \
                or data.dtype.type == np.str_) \
                and data.nbytes == 0)):
            data_to_store = np.uint64(data_to_store.shape)

        # If it is a complex type, then it needs to be encoded to have
        # the proper complex field names.
        if np.iscomplexobj(data_to_store):
            data_to_store = encode_complex(data_to_store,
                                           options.complex_names)

        # If we are storing an object type and it isn't empty
        # (data_to_store is still an object), then we must recursively
        # write what each element points to and make an array of the
        # references to them.
        if data_to_store.dtype.name == 'object':
            data_to_store = write_object_array(f, data_to_store,
                                               options)

        # If it an ndarray with fields and we are writing such things as
        # a Group/struct or if its shape is zero (h5py can't write it
        # Dataset then), that needs to be handled. Otherwise, it is
        # simply written as is to a Dataset. As HDF5 Reference types do
        # look like a structured object array, those have to be excluded
        # explicitly. Complex types may have been converted so that they
        # can have different field names as an HDF5 COMPOUND type, so
        # those have to be excluded too. Also, if any of its fields are
        # an object time (no matter how nested), then rather than
        # converting that field to a HDF5 Reference types, it will just
        # be written as a Group instead (just have to see if ", 'O'" is
        # in str(data_to_store.dtype).
        #
        # A flag, wrote_as_struct, is set depending on which path is
        # taken, which is then passed onto write_metadata.

        if data_to_store.dtype.fields is not None \
                and h5py.check_dtype(ref=data_to_store.dtype) \
                is not h5py.Reference \
                and not np.iscomplexobj(data) \
                and (options.structured_numpy_ndarray_as_struct \
                or (data_to_store.dtype.hasobject \
                or '\\x00' in str(data_to_store.dtype)) \
                or does_dtype_have_a_zero_shape(data_to_store.dtype)):
            wrote_as_struct = True
            # Grab the list of fields that don't have a null character
            # or a / in them since those can't be written.
            field_names = [n for n in data_to_store.dtype.names
                           if '/' not in n and '\x00' not in n]

            # Throw and exception if we had to exclude any field names.
            if len(field_names) != len(data_to_store.dtype.names):
                raise NotImplementedError("Null characters ('\x00') " \
                    + "and '/' in the field names of this type of " \
                    + 'numpy.ndarray are not supported.')

            # If the group doesn't exist, it needs to be created. If it
            # already exists but is not a group, it needs to be deleted
            # before being created.

            if name not in grp:
                grp.create_group(name)
            elif not isinstance(grp[name], h5py.Group):
                del grp[name]
                grp.create_group(name)

            grp2 = grp[name]

            # Write the metadata, and set the MATLAB_class to 'struct'
            # explicitly.
            if options.matlab_compatible:
                set_attribute_string(grp2, 'MATLAB_class',
                                     'struct')

            # Delete any Datasets/Groups not corresponding to a field
            # name in data if that option is set.

            if options.delete_unused_variables:
                for field in set([i for i in grp2]).difference( \
                        set(field_names)):
                    del grp2[field]

            # Go field by field making an object array (make an empty
            # object array and assign element wise) and write it inside
            # the Group. If it only has a single element, write that
            # single element extracted from it (will be a standard
            # Dataset as opposed to a HDF5 Reference array). The H5PATH
            # attribute needs to be set appropriately, while all other
            # attributes need to be deleted.
            grp2_name = grp2.name
            for field in field_names:
                new_data = np.zeros(shape=data_to_store.shape,
                                    dtype='object')
                for index, x in np.ndenumerate(data_to_store):
                    new_data[index] = x[field]

                # If we are supposed to reverse dimension order, it has
                # already been done, but write_data expects that it
                # hasn't, so it needs to be reversed again before
                # passing it on.
                if options.reverse_dimension_order:
                    new_data = new_data.T

                # If there is only a single element, write it extracted
                # (don't need to use a Reference array in this
                # case). Otherwise, write the whole thing.
                if np.prod(new_data.shape) == 1:
                    write_data(f, grp2, field, new_data.flatten()[0],
                               None, options)
                else:
                    write_data(f, grp2, field, new_data, None, options)

                if field in grp2:
                    grp2_field = grp2[field]
                    if options.matlab_compatible:
                        set_attribute_string(grp2_field, 'H5PATH',
                                             grp2_name)
                    else:
                        del_attribute(grp2_field, 'H5PATH')

                    # In the case that we wrote a Reference array (not a
                    # single element), then all other attributes need to
                    # be removed.
                    if np.prod(new_data.shape) != 1:
                        for attribute in (set( \
                                grp2_field.attrs.keys()) \
                                - set(['H5PATH'])):
                            del_attribute(grp2_field, attribute)
        else:
            wrote_as_struct = False
            # If it has fields and it isn't a Reference type, none of
            # them can contain a / character.
            if data_to_store.dtype.fields is not None \
                    and h5py.check_dtype(ref=data_to_store.dtype) \
                    is not h5py.Reference:
                for n in data_to_store.dtype.fields:
                    if '\x00' in n:
                        raise NotImplementedError( \
                            "Null characters ('\x00') " \
                            + 'in the field names of this type of ' \
                            + 'numpy.ndarray are not supported.')

            # Set the storage options such as compression, chunking,
            # filters, etc. If the data is being compressed (compression
            # is enabled and the data is bigger than the threshold),
            # turn on compression, set the algorithm, set the
            # compression level, and enable the shuffle and fletcher32
            # filters appropriately. If the data is not being
            # compressed, turn on the fletcher32 filter if
            # indicated. Compression should not be done for scalars.
            filters = dict()
            is_scalar = (data_to_store.shape != tuple())
            if is_scalar and options.compress \
                    and data_to_store.nbytes \
                    >= options.compress_size_threshold:
                filters['compression'] = \
                    options.compression_algorithm
                if filters['compression'] == 'gzip':
                    filters['compression_opts'] = \
                        options.gzip_compression_level
                filters['shuffle'] = options.shuffle_filter
                filters['fletcher32'] = \
                    options.compressed_fletcher32_filter
            else:
                filters['compression'] = None
                filters['shuffle'] = False
                filters['compression_opts'] = None
                if is_scalar:
                    filters['fletcher32'] = \
                        options.uncompressed_fletcher32_filter
                else:
                    filters['fletcher32'] = False

            # Set the chunking to auto if it is being chuncked
            # (compressed or using the fletcher32 filter).
            if filters['compression'] is not None \
                    or filters['fletcher32']:
                filters['chunks'] = True
            else:
                filters['chunks'] = None

            # The data must first be written. If name is not present
            # yet, then it must be created. If it is present, but not a
            # Dataset, has the wrong dtype, is the wrong shape, doesn't
            # use the same compression, or doesn't use the same filters;
            # then it must be deleted and then written. Otherwise, it is
            # just overwritten in place.
            if name not in grp:
                grp.create_dataset(name, data=data_to_store,
                                   **filters)
            else:
                # avoid multiple calls to __getitem__ by storing the
                # reference in a local variable
                dset = grp[name]
                if not isinstance(dset, h5py.Dataset) \
                        or dset.dtype != data_to_store.dtype \
                        or dset.shape != data_to_store.shape \
                        or dset.compression != filters['compression'] \
                        or dset.shuffle != filters['shuffle'] \
                        or dset.fletcher32 != filters['fletcher32'] \
                        or dset.compression_opts != \
                        filters['compression_opts']:
                    del grp[name]
                    grp.create_dataset(name, data=data_to_store,
                                       **filters)
                else:
                    dset[...] = data_to_store

        # Write the metadata using the inherited function (good enough).
        self.write_metadata(f, grp, name, data, type_string,
                            options, wrote_as_struct=wrote_as_struct)

    def write_metadata(self, f, grp, name, data, type_string, options,
                       wrote_as_struct=False):
        # wote_as_struct is used to pass whether data was written like a
        # matlab struct or not. If yes, then the field names must be put
        # in the metadata.

        # First, call the inherited version to do most of the work.

        TypeMarshaller.write_metadata(self, f, grp, name, data,
                                      type_string, options)

        # Write the underlying numpy type if we are storing python
        # information.

        # If we are storing python information; the shape, underlying
        # numpy type, and its type of container ('scalar', 'ndarray',
        # 'matrix', or 'chararray') need to be stored.

        # avoid multiple calls to __getitem__ by storing the
        # reference in a local variable
        dsetgrp = grp[name]

        if options.store_python_metadata:
            set_attribute(dsetgrp, 'Python.Shape',
                          np.uint64(data.shape))

            # Now, in Python 3, the dtype names for bare bytes and
            # unicode strings start with 'bytes' and 'str' respectively,
            # but in Python 2, they start with 'string' and 'unicode'
            # respectively. The Python 2 ones must be converted to the
            # Python 3 ones for writing.
            set_attribute_string(dsetgrp, \
                'Python.numpy.UnderlyingType', \
                data.dtype.name.replace('string', 'bytes').replace( \
                'unicode', 'str'))
            if isinstance(data, np.matrix):
                container = 'matrix'
            elif isinstance(data, np.chararray):
                container = 'chararray'
            elif isinstance(data, np.core.records.recarray):
                container = 'recarray'
            elif isinstance(data, np.ndarray):
                container = 'ndarray'
            else:
                container = 'scalar'
            set_attribute_string(dsetgrp, 'Python.numpy.Container',
                                 container)

        # If it was written like a matlab struct, then we set the
        # 'Python.Fields' and 'MATLAB_fields' Attributes to the field
        # names if we are storing python metadata or doing matlab
        # compatibility and we are storing a structured ndarray as a
        # structure.
        if wrote_as_struct:
            # Grab the list of fields. They need to be converted to
            # unicode in Python 2.x.
            if sys.hexversion >= 0x03000000:
                field_names = list(data.dtype.names)
            else:
                field_names = [c.decode('UTF-8')
                               for c in list(data.dtype.names)]

            # Write or delete 'Python.Fields' as appropriate.
            if options.store_python_metadata:
                set_attribute_string_array(dsetgrp,
                                           'Python.Fields',
                                           field_names)
            else:
                del_attribute(dsetgrp, 'Python.Fields')

            # If we are making it MATLAB compatible and have h5py
            # version >= 2.3, then we can set the MATLAB_fields
            # Attribute as long as all keys are mappable to
            # ASCII. Otherwise, the attribute should be deleted. It is
            # written as a vlen='S1' array of bytes_ arrays of the
            # individual characters.
            if options.matlab_compatible \
                    and parse_version( \
                    _H5PY_VERSION) \
                    >= parse_version('2.3'):
                try:
                    dt = h5py.special_dtype(vlen=np.dtype('S1'))
                    fs = np.empty(shape=(len(field_names),), dtype=dt)
                    for i, s in enumerate(field_names):
                        fs[i] = np.array([c.encode('ascii') for c in s],
                                         dtype='S1')
                except UnicodeEncodeError:
                    del_attribute(dsetgrp, 'MATLAB_fields')
                else:
                    set_attribute(dsetgrp, 'MATLAB_fields', fs)
            else:
                del_attribute(dsetgrp, 'MATLAB_fields')
        else:
            del_attribute(dsetgrp, 'Python.Fields')
            del_attribute(dsetgrp, 'MATLAB_fields')

        # If data is empty, we need to set the Python.Empty and
        # MATLAB_empty attributes to 1 if we are storing type info or
        # making it MATLAB compatible. Otherwise, no empty attribute is
        # set and existing ones must be deleted.

        if data.size == 0  or ((data.dtype.type == np.bytes_ \
                or data.dtype.type == np.str_)
                and data.nbytes == 0):
            if options.store_python_metadata:
                set_attribute(dsetgrp, 'Python.Empty',
                              np.uint8(1))
            else:
                del_attribute(dsetgrp, 'Python.Empty')
            if options.matlab_compatible:
                set_attribute(dsetgrp, 'MATLAB_empty',
                              np.uint8(1))
            else:
                del_attribute(dsetgrp, 'MATLAB_empty')
        else:
            del_attribute(dsetgrp, 'Python.Empty')
            del_attribute(dsetgrp, 'MATLAB_empty')

        # If we are making it MATLAB compatible, the MATLAB_class
        # attribute needs to be set looking up the data type (gotten
        # using np.dtype.type). If it is a string or bool type, then
        # the MATLAB_int_decode attribute must be set to the number of
        # bytes each element takes up (dtype.itemsize). If the dtype has
        # fields and we are writing it as a structure, the class needs
        # to be overriddent to 'struct'. Otherwise, the attributes must
        # be deleted.

        tp = data.dtype.type
        if options.matlab_compatible:
            if data.dtype.fields is not None \
                    and options.structured_numpy_ndarray_as_struct:
                set_attribute_string(dsetgrp, 'MATLAB_class',
                                     'struct')
            elif tp in self.__MATLAB_classes:
                set_attribute_string(dsetgrp, 'MATLAB_class',
                                     self.__MATLAB_classes[tp])
                if tp in (np.bytes_, np.str_, np.bool_):
                    set_attribute(dsetgrp, 'MATLAB_int_decode',
                                  np.int64(grp[name].dtype.itemsize))
                else:
                    del_attribute(dsetgrp, 'MATLAB_int_decode')
            else:
                del_attribute(dsetgrp, 'MATLAB_class')
                del_attribute(dsetgrp, 'MATLAB_empty')
                del_attribute(dsetgrp, 'MATLAB_int_decode')
        else:
            del_attribute(dsetgrp, 'MATLAB_class')
            del_attribute(dsetgrp, 'MATLAB_empty')
            del_attribute(dsetgrp, 'MATLAB_int_decode')

    def read(self, f, grp, name, options):
        # If name is not present, then we can't read it and have to
        # throw an error.
        if name not in grp:
            raise NotImplementedError(name + ' is not present.')

        # Get the object.
        dsetgrp = grp[name]

        # Get the different attributes this marshaller uses.

        if sys.hexversion >= 0x03000000:
            defaultfactory = type(None)
        else:
            defaultfactory = lambda : None
        attributes = collections.defaultdict(defaultfactory)
        read_all_attributes_into(dsetgrp.attrs, attributes)

        str_attrs = dict()
        for attr_name in ('Python.Type',
                          'Python.numpy.UnderlyingType',
                          'Python.numpy.Container',
                          'MATLAB_class'):
            value = attributes[attr_name]
            if value is None:
                str_attrs[attr_name] = value
            elif (sys.hexversion >= 0x03000000 \
                    and isinstance(value, str)) \
                    or (sys.hexversion < 0x03000000 \
                    and isinstance(value, unicode)):
                str_attrs[attr_name] = value
            elif isinstance(value, bytes):
                str_attrs[attr_name] = value.decode()
            elif isinstance(value, np.unicode_):
                str_attrs[attr_name] = str(value)
            elif isinstance(value, np.bytes_):
                str_attrs[attr_name] = value.decode()
            else:
                str_attrs[attr_name] = None

        type_string = str_attrs['Python.Type']
        underlying_type = str_attrs['Python.numpy.UnderlyingType']
        container = str_attrs['Python.numpy.Container']
        matlab_class = str_attrs['MATLAB_class']

        shape = attributes['Python.Shape']
        python_empty = attributes['Python.Empty']
        matlab_empty = attributes['MATLAB_empty']

        python_fields = attributes['Python.Fields']
        if python_fields is not None:
            python_fields = [convert_to_str(x)
                             for x in python_fields]

        # Read the MATLAB_fields Attribute if it was present.
        matlab_fields = attributes['MATLAB_fields']

        # If it is a Dataset, it can simply be read and then acted upon
        # (if it is an HDF5 Reference array, it will need to be read
        # recursively). If it is a Group, then it is a structured
        # ndarray like object that needs to be read field wise and
        # constructed.
        if isinstance(dsetgrp, h5py.Dataset):
            # Read the data.
            data = dsetgrp[...]

            # If it is a reference type, then we need to make an object
            # array that is its replicate, but with the objects they are
            # pointing to in their elements instead of just the
            # references.
            if h5py.check_dtype(ref=dsetgrp.dtype) is not None:
                data = read_object_array(f, data, options)
        else:
            # Starting with an empty dict, all that has to be done is
            # iterate through all the Datasets and Groups in dsetgrp
            # and add them to a dict with their name as the key. Since
            # we don't want an exception thrown by reading an element to
            # stop the whole reading process, the reading is wrapped in
            # a try block that just catches exceptions and then does
            # nothing about them (nothing needs to be done). We also
            # need to keep track of whether any of the fields are
            # Groups, aren't Reference arrays, or have attributes other
            # than H5PATH since that means that the fields are the
            # values (single element structured ndarray), as opposed to
            # Reference arrays to all the values (multi-element structed
            # ndarray). In Python 2, the field names need to be
            # converted to str from unicode when storing the fields in
            # struct_data.
            struct_data = dict()
            is_multi_element = True
            for k, fld in dsetgrp.items():
                # We must exclude group_for_references
                if fld.name == options.group_for_references:
                    continue
                if isinstance(fld, h5py.Group) \
                        or h5py.check_dtype(ref=fld.dtype) is None \
                        or len(set(fld.attrs.keys()) \
                        & ((set(self.python_attributes) \
                        | set(self.matlab_attributes))
                        - set(['H5PATH', 'MATLAB_empty',
                        'Python.Empty']))) != 0:
                    is_multi_element = False
                try:
                    struct_data[k] = read_data(f, dsetgrp, k,
                                               options)
                except:
                    pass

            # If it isn't multi element, we need to pack all the values
            # in struct_array inside of numpy.object_'s so that the code
            # after this that depends on this will work.
            if not is_multi_element:
                for k, v in struct_data.items():
                    obj = np.zeros((1,), dtype='object')
                    obj[0] = v
                    struct_data[k] = obj

            # The dtype for the structured ndarray needs to be
            # composed. This is done by going through each field (in the
            # proper order, if the fields were given, or any order if
            # not) and determine the dtype and shape of that field to
            # put in the list.

            if python_fields is not None or matlab_fields is not None:
                if python_fields is not None:
                    fields = python_fields
                else:
                    fields = [numpy_to_bytes(k).decode()
                              for k in matlab_fields]
                # Now, there may be fields available that were not
                # given, but still should be read. Keys that are not in
                # python_fields need to be added to the list.
                extra_fields = list(set(struct_data.keys())
                                    - set(fields))
                fields.extend(sorted(extra_fields))
            else:
                fields = sorted(list(struct_data.keys()))

            dt_whole = []
            for k in fields:
                # In Python 2, the field names for a structured ndarray
                # must be str as opposed to unicode, so k needs to be
                # converted in the Python 2 case.
                if sys.hexversion >= 0x03000000:
                    k_name = k
                else:
                    k_name = k.encode('UTF-8')

                # Read the value.
                v = struct_data[k]

                # If any of the elements are not Numpy types or if they
                # don't all have the exact same dtype and shape, then
                # this field will just be an object field.
                if v.size == 0 or type(v.flat[0]) \
                        not in self._numpy_types:
                    dt_whole.append((k_name, 'object'))
                    continue

                first = v.flatten()[0]
                dt = first.dtype
                sp = first.shape
                all_same = True
                for index, x in np.ndenumerate(v):
                    if not isinstance(x, tuple(self.types)) \
                            or dt != x.dtype or sp != x.shape:
                        all_same = False
                        break

                # If they are all the same, then dt and shape should be
                # used. Otherwise, it has to be object.
                if all_same:
                    dt_whole.append((k_name, dt, sp))
                else:
                    dt_whole.append((k_name, 'object'))

            # Make the structured ndarray with the constructed
            # dtype. The shape is simply the shape of the object arrays
            # of its fields, so we might as well use the shape of
            # v. Then, all the elements of every field need to be
            # assigned. Now, if dtype's itemsize is 0, a TypeError will
            # be thrown by numpy due to a bug in numpy. np.zeros (as
            # well as ones and empty) does not like to make arrays with
            # no bytes. A workaround is to make an empty array of some
            # other type and convert its dtype. The smallest one we can
            # make is an np.int8([]). Yes, one byte will be wasted, but
            # at least no errors will happen.
            dtwhole = np.dtype(dt_whole)
            if dtwhole.itemsize == 0:
                data = np.zeros(shape=v.shape,
                                dtype='int8').astype(dtwhole)
            else:
                data = np.zeros(shape=v.shape, dtype=dtwhole)
            for k, v in struct_data.items():
                # There is no sense iterating through the elements if
                # the shape is an empty shape.
                if all(data.shape) and all(v.shape):
                    for index, x in np.ndenumerate(v):
                        if sys.hexversion >= 0x03000000:
                            data[k][index] = x
                        else:
                            data[k.encode('UTF-8')][index] = x

        # If metadata is present, that can be used to do convert to the
        # desired/closest Python data types. If none is present, or not
        # enough of it, then no conversions can be done.
        if type_string is not None and underlying_type is not None and \
                shape is not None:
            # If the Attributes 'Python.Fields' and/or 'MATLAB_fields'
            # are present, the underlying type needs to be changed to
            # the proper dtype for the structure.
            if python_fields is not None or matlab_fields is not None:
                if python_fields is not None:
                    fields = python_fields
                else:
                    fields = [numpy_to_bytes(k).decode()
                              for k in matlab_fields]
                struct_dtype = list()
                for k in fields:
                    if sys.hexversion >= 0x03000000:
                        struct_dtype.append((k, 'object'))
                    else:
                        struct_dtype.append((k.encode('UTF-8'),
                                            'object'))
            else:
                struct_dtype = None

            # If it is empty ('Python.Empty' set to 1), then the shape
            # information is stored in data and we need to set data to
            # the empty array of the proper type (in underlying_type)
            # and the given shape. If we are going to transpose it
            # later, we need to transpose it now so that it still keeps
            # the right shape. Also, if it is a structure that we just
            # figured out the dtype for, that needs to be used.
            if python_empty == 1:
                if underlying_type.startswith('bytes'):
                    if underlying_type == 'bytes':
                        nchars = 1
                    else:
                        nchars = int(int(
                                     underlying_type[len('bytes'):])
                                     / 8)
                    data = np.zeros(tuple(shape),
                                    dtype='S' + str(nchars))
                elif underlying_type.startswith('str'):
                    if underlying_type == 'str':
                        nchars = 1
                    else:
                        nchars = int(int(
                                     underlying_type[len('str'):])
                                     / 32)
                    data = np.zeros(tuple(shape),
                                    dtype='U' + str(nchars))
                elif struct_dtype is not None:
                    data = np.zeros(tuple(shape),
                                    dtype=struct_dtype)
                else:
                    data = np.zeros(tuple(shape),
                                    dtype=underlying_type)
                if matlab_class is not None or \
                        options.reverse_dimension_order:
                    data = data.T

            # If it is a complex type, then it needs to be decoded
            # properly.
            if underlying_type.startswith('complex'):
                data = decode_complex(data)

            # If its underlying type is 'bool' but it is something else,
            # then it needs to be converted (means it was written with
            # the convert_bools_to_uint8 option).
            if underlying_type == 'bool' and data.dtype.name != 'bool':
                data = np.bool_(data)

            # If MATLAB attributes are present or the reverse dimension
            # order option was given, the dimension order needs to be
            # reversed. This needs to be done before any reshaping as
            # the shape was stored before any dimensional reordering.
            if matlab_class is not None or \
                    options.reverse_dimension_order:
                data = data.T

            # String types might have to be decoded depending on the
            # underlying type, and MATLAB class if given. They also need
            # to be properly decoded into strings of the right length if
            # it originally represented an array of strings (turned into
            # uints of some sort). The length in bits is contained in
            # the dtype name, which is the underlying_type.
            if underlying_type.startswith('bytes'):
                if underlying_type == 'bytes':
                    data = np.bytes_(b'')
                else:
                    data = convert_to_numpy_bytes(data, \
                        length=int(underlying_type[5:])//8)
            elif underlying_type.startswith('str') \
                    or matlab_class == 'char':
                if underlying_type == 'str':
                    data = np.unicode_('')
                elif underlying_type.startswith('str'):
                    data = convert_to_numpy_str(data, \
                        length=int(underlying_type[3:])//32)
                else:
                    data = convert_to_numpy_str(data)

            # If the shape of data and the shape attribute are
            # different but give the same number of elements, then data
            # needs to be reshaped.
            if tuple(shape) != data.shape \
                    and np.prod(shape) == np.prod(data.shape):
                data = data.reshape(tuple(shape))

            # If data is a structured ndarray and the type string says
            # it is a recarray, then turn it into one.
            if type_string == 'numpy.recarray':
                data = data.view(np.core.records.recarray)

            # Convert to scalar, matrix, chararray, or ndarray depending
            # on the container type. For an empty scalar string, it
            # needs to be manually set to '' and b'' or there will be
            # problems.
            if container == 'scalar':
                if underlying_type.startswith('bytes'):
                    if python_empty == 1:
                        data = np.bytes_(b'')
                    elif isinstance(data, np.ndarray):
                        data = data.flatten()[0]
                elif underlying_type.startswith('str'):
                    if python_empty == 1:
                        data = np.unicode_('')
                    elif isinstance(data, np.ndarray):
                        data = data.flatten()[0]
                else:
                    data = data.flatten()[0]
            elif container == 'matrix':
                data = np.asmatrix(data)
            elif container == 'chararray':
                data = data.view(np.chararray)
            elif container == 'ndarray':
                data = np.asarray(data)

        elif matlab_class in self.__MATLAB_classes_reverse:
            # MATLAB formatting information was given. The extraction
            # did most of the work except handling empties, array
            # dimension order, and string conversion.

            # If it is empty ('MATLAB_empty' set to 1), then the shape
            # information is stored in data and we need to set data to
            # the empty array of the proper type. If it is a MATLAB
            # struct, then the proper dtype has to be constructed from
            # the field names if present (the dtype of each individual
            # field is set to object).
            if matlab_empty == 1:
                if matlab_fields is None:
                    data = np.zeros(tuple(np.uint64(data)), \
                        dtype=self.__MATLAB_classes_reverse[ \
                        matlab_class])
                else:
                    dt_whole = list()
                    for k in matlab_fields:
                        if sys.hexversion >= 0x03000000:
                            dt_whole.append((numpy_to_bytes(k).decode(),
                                            'object'))
                        else:
                            dt_whole.append((numpy_to_bytes(k),
                                             'object'))
                    data = np.zeros(shape=tuple(np.uint64(data)),
                                    dtype=dt_whole)

            # The order of the dimensions must be switched from Fortran
            # order which MATLAB uses to C order which Python uses.
            data = data.T

            # Now, if the matlab class is 'single' or 'double', data
            # could possibly be a complex type which needs to be
            # properly decoded.
            if matlab_class in ['single', 'double']:
                data = decode_complex(data)

            # If it is a logical, then it must be converted to
            # numpy.bool8.
            if matlab_class == 'logical':
                data = np.bool_(data)

            # If it is a 'char' type, the proper conversion to
            # numpy.unicode needs to be done.
            if matlab_class == 'char':
                data = convert_to_numpy_str(data)

        # Done adjusting data, so it can be returned.
        return data


class PythonScalarMarshaller(NumpyScalarArrayMarshaller):
    def __init__(self):
        NumpyScalarArrayMarshaller.__init__(self)

        # In Python 3, there is only a single integer type int, which is
        # variable width. In Python 2, there is the fixed width int and
        # the variable width long. Python 2 needs to be able to save
        # with either, but Python 3 needs to map both to int, which can
        # be done by just putting the type int for its entry in types.
        if sys.hexversion >= 0x03000000:
            self.types = [bool, int, int, float, complex]
        else:
            self.types = [bool, int, long, float, complex]
        self.python_type_strings = ['bool', 'int', 'long', 'float',
                                    'complex']
        # As the parent class already has MATLAB strings handled, there
        # are no MATLAB classes that this marshaller should be used for.
        self.matlab_classes = []

    def write(self, f, grp, name, data, type_string, options):
        # data just needs to be converted to the appropriate numpy
        # type. If it is a Python 3.x int or Python 2.x long that is too
        # big to fit in a numpy.int64, we need to throw an not
        # implemented exception so it doesn't get packaged as an
        # object. It is converted explicitly to a numpy.int64. If it is
        # too big, there will be an OverflowError. Otherwise, data is
        # passed through np.array and then access [()] to get the scalar
        # back as a scalar numpy type. The proper type_string needs to
        # be grabbed now as the parent function will have a modified
        # form of data to guess from if not given the right one
        # explicitly.
        if sys.hexversion >= 0x03000000:
            tp = int
        else:
            tp = long
        if type(data) == tp:
            try:
                out = np.int64(data)
            except OverflowError:
                raise NotImplementedError('Int/long too big to fit '
                                          + 'into numpy.int64.')
        else:
            out = data
        NumpyScalarArrayMarshaller.write(self, f, grp, name,
                                         np.array(out)[()],
                                         self.get_type_string(data,
                                         type_string), options)

    def read(self, f, grp, name, options):
        # Use the parent class version to read it and do most of the
        # work.
        data = NumpyScalarArrayMarshaller.read(self, f, grp, name,
                                               options)

        # The type string determines how to convert it back to a Python
        # type (just look up the entry in types). As it might be
        # returned as an ndarray, we just need to use the item
        # method. Now, since int and long are unified in Python 3.x and
        # the size of int in Python 2.x is not always the same, if the
        # type_string is 'int', then we need to check to see if it can
        # fit into an int if we are in Python 2.x. If it will fit, it is
        # returned as an int. If it would not fit, it is returned as a
        # long.
        type_string = get_attribute_string(grp[name], 'Python.Type')
        if type_string in self.python_type_strings:
            tp = self.types[self.python_type_strings.index(
                            type_string)]
            sdata = data.item()
            if sys.hexversion >= 0x03000000 or tp != int:
                return tp(sdata)
            else:
                num = long(sdata)
                if num > sys.maxint or num < -(sys.maxint - 1):
                    return num
                else:
                    return int(num)
        else:
            # Must be some other type, so return it as is.
            return data


class PythonStringMarshaller(NumpyScalarArrayMarshaller):
    def __init__(self):
        NumpyScalarArrayMarshaller.__init__(self)
        # In Python 3, the unicode and bare bytes type strings are str
        # and bytes, but before Python 3, they were unicode and str
        # respectively. The Python 3 python_type_strings will be used,
        # though.
        if sys.hexversion >= 0x03000000:
            self.types = [str, bytes, bytearray]
        else:
            self.types = [unicode, str, bytearray]
        self.python_type_strings = ['str', 'bytes', 'bytearray']
        # As the parent class already has MATLAB strings handled, there
        # are no MATLAB classes that this marshaller should be used for.
        self.matlab_classes = []

    def write(self, f, grp, name, data, type_string, options):
        # data just needs to be converted to a numpy string of the
        # appropriate type (str to np.str_ and the others to np.bytes_).
        if (sys.hexversion >= 0x03000000 and isinstance(data, str)) \
                or (sys.hexversion < 0x03000000 \
                and isinstance(data, unicode)):
            cdata = np.unicode_(data)
        else:
            cdata = np.bytes_(data)

        # Now pass it to the parent version of this function to write
        # it. The proper type_string needs to be grabbed now as the
        # parent function will have a modified form of data to guess
        # from if not given the right one explicitly.
        NumpyScalarArrayMarshaller.write(self, f, grp, name, cdata,
                                         self.get_type_string(data,
                                         type_string), options)

    def read(self, f, grp, name, options):
        # Use the parent class version to read it and do most of the
        # work.
        data = NumpyScalarArrayMarshaller.read(self, f, grp, name,
                                               options)

        # The type string determines how to convert it back to a Python
        # type (just look up the entry in types). Otherwise, return it
        # as is.
        type_string = get_attribute_string(grp[name], 'Python.Type')
        if type_string == 'str':
            return convert_to_str(data)
        elif type_string == 'bytes':
            if sys.hexversion >= 0x03000000:
                return bytes(data)
            else:
                return str(data)
        elif type_string == 'bytearray':
            return bytearray(data)
        else:
            return data


class PythonNoneMarshaller(NumpyScalarArrayMarshaller):
    def __init__(self):
        NumpyScalarArrayMarshaller.__init__(self)
        self.types = [type(None)]
        self.python_type_strings = ['builtins.NoneType']
        # None corresponds to no MATLAB class.
        self.matlab_classes = []

    def write(self, f, grp, name, data, type_string, options):
        # Just going to use the parent function with an empty double
        # (two dimensional so that MATLAB will import it as a []) as the
        # data and the right type_string set (parent can't guess right
        # from the modified form).
        NumpyScalarArrayMarshaller.write(self, f, grp, name,
                                         np.float64([]),
                                         self.get_type_string(data,
                                         type_string), options)

    def read(self, f, grp, name, options):
        # There is only one value, so return it.
        return None


class PythonDictMarshaller(TypeMarshaller):
    def __init__(self):
        TypeMarshaller.__init__(self)
        self.python_attributes |= set(['Python.Fields'])
        self.matlab_attributes |= set(['MATLAB_class', 'MATLAB_fields'])
        self.types = [dict]
        self.python_type_strings = ['dict']
        self.__MATLAB_classes = {dict: 'struct'}
        # Set matlab_classes to empty since NumpyScalarArrayMarshaller
        # handles Groups by default now.
        self.matlab_classes = list()

    def write(self, f, grp, name, data, type_string, options):
        # Check for any field names that are not unicode since they
        # cannot be handled. Also check for null characters and /
        # characters since they can't be handled either. How it is
        # checked (what type it is) and the error message are different
        # for each Python version.

        if sys.hexversion >= 0x03000000:
            for fieldname in data:
                if not isinstance(fieldname, str):
                    raise NotImplementedError('Dictionaries with non-'
                                              + 'str keys are not '
                                              + 'supported: '
                                              + repr(fieldname))
                if '\x00' in fieldname or '/' in fieldname:
                    raise NotImplementedError('Dictionary keys with ' \
                        + "null characters ('\x00') and '/' are not " \
                        + 'supported.')
        else:
            for fieldname in data:
                if not isinstance(fieldname, unicode):
                    raise NotImplementedError('Dictionaries with non-'
                                              + 'unicode keys are not '
                                              + 'supported: '
                                              + repr(fieldname))
                if unicode('\x00') in fieldname \
                        or unicode('/') in fieldname:
                    raise NotImplementedError('Dictionary keys with ' \
                        + "null characters ('\x00') and '/' are not " \
                        + 'supported.')

        # If the group doesn't exist, it needs to be created. If it
        # already exists but is not a group, it needs to be deleted
        # before being created.

        if name not in grp:
            grp2 = grp.create_group(name)
        elif not isinstance(grp[name], h5py.Group):
            del grp[name]
            grp2 = grp.create_group(name)
        else:
            grp2 = grp[name]

        # Write the metadata.
        self.write_metadata(f, grp, name, data, type_string, options)

        # Delete any Datasets/Groups not corresponding to a field name
        # in data if that option is set.

        if options.delete_unused_variables:
            for field in set([i for i in grp2]).difference( \
                    set([i for i in data])):
                del grp2[field]

        # Go through all the elements of data and write them. The H5PATH
        # needs to be set as the path of grp2 on all of them if we are
        # doing MATLAB compatibility (otherwise, the attribute needs to
        # be deleted).
        grp2_name = grp2.name
        for k, v in data.items():
            write_data(f, grp2, k, v, None, options)
            if k in grp2:
                if options.matlab_compatible:
                    set_attribute_string(grp2[k], 'H5PATH', grp2_name)
                else:
                    del_attribute(grp2[k], 'H5PATH')

    def write_metadata(self, f, grp, name, data, type_string, options):
        # First, call the inherited version to do most of the work and
        # get the group.

        TypeMarshaller.write_metadata(self, f, grp, name, data,
                                      type_string, options)
        grp2 = grp[name]

        # Grab all the keys and sort the list.
        fields = sorted(list(data.keys()))

        # If we are storing python metadata, we need to set the
        # 'Python.Fields' Attribute to be all the keys.
        if options.store_python_metadata:
            set_attribute_string_array(grp2, 'Python.Fields',
                                       fields)

        # If we are making it MATLAB compatible and have h5py version
        # >= 2.3, then we can set the MATLAB_fields Attribute as long as
        # all keys are mappable to ASCII. Otherwise, the attribute
        # should be deleted. It is written as a vlen='S1' array of
        # bytes_ arrays of the individual characters.
        if options.matlab_compatible \
                and parse_version(_H5PY_VERSION) \
                >= parse_version('2.3'):
            try:
                dt = h5py.special_dtype(vlen=np.dtype('S1'))
                fs = np.empty(shape=(len(fields),), dtype=dt)
                for i, s in enumerate(fields):
                    fs[i] = np.array([c.encode('ascii') for c in s],
                                     dtype='S1')
            except UnicodeDecodeError:
                del_attribute(grp2, 'MATLAB_fields')
            else:
                set_attribute(grp2, 'MATLAB_fields', fs)
        else:
            del_attribute(grp2, 'MATLAB_fields')

        # If we are making it MATLAB compatible, the MATLAB_class
        # attribute needs to be set for the data type. If the type
        # cannot be found or if we are not doing MATLAB compatibility,
        # the attributes need to be deleted.

        tp = type(data)
        if options.matlab_compatible and tp in self.__MATLAB_classes:
            set_attribute_string(grp2, 'MATLAB_class',
                                 self.__MATLAB_classes[tp])
        else:
            del_attribute(grp2, 'MATLAB_class')

    def read(self, f, grp, name, options):
        # If name is not present or is not a Group, then we can't read
        # it and have to throw an error.
        grp2 = grp.get(name)
        if grp2 is None:
            raise NotImplementedError('No object with name ' + name
                                      + 'is present.')
        if not isinstance(grp2, h5py.Group):
            raise NotImplementedError(name + ' is not a Group.')

        # Starting with an empty dict, all that has to be done is
        # iterate through all the Datasets and Groups in grp[name] and
        # add them to the dict with their name as the key. Since we
        # don't want an exception thrown by reading an element to stop
        # the whole reading process, the reading is wrapped in a try
        # block that just catches exceptions and then does nothing about
        # them (nothing needs to be done).
        data = dict()
        for k, dsetgrp in grp2.items():
            # We must exclude group_for_references
            if dsetgrp.name == options.group_for_references:
                continue
            try:
                data[k] = read_data(f, grp2, k, options)
            except:
                pass
        return data


class PythonListMarshaller(NumpyScalarArrayMarshaller):
    def __init__(self):
        NumpyScalarArrayMarshaller.__init__(self)
        self.types = [list]
        self.python_type_strings = ['list']
        # As the parent class already has MATLAB strings handled, there
        # are no MATLAB classes that this marshaller should be used for.
        self.matlab_classes = []

    def write(self, f, grp, name, data, type_string, options):
        # data just needs to be converted to the appropriate numpy type
        # (pass it through np.object_ to get the and then pass it to the
        # parent version of this function. The proper type_string needs
        # to be grabbed now as the parent function will have a modified
        # form of data to guess from if not given the right one
        # explicitly.
        out = np.zeros(dtype='object', shape=(len(data), ))
        out[:] = data
        NumpyScalarArrayMarshaller.write(self, f, grp, name,
                                         out,
                                         self.get_type_string(data,
                                         type_string), options)

    def read(self, f, grp, name, options):
        # Use the parent class version to read it and do most of the
        # work.
        data = NumpyScalarArrayMarshaller.read(self, f, grp, name,
                                               options)

        # Passing it through list does all the work of making it a list
        # again.
        return list(data)


class PythonTupleSetDequeMarshaller(PythonListMarshaller):
    def __init__(self):
        PythonListMarshaller.__init__(self)
        self.types = [tuple, set, frozenset, collections.deque]
        self.python_type_strings = ['tuple', 'set', 'frozenset',
                                    'collections.deque']
        # As the parent class already has MATLAB strings handled, there
        # are no MATLAB classes that this marshaller should be used for.
        self.matlab_classes = []

    def write(self, f, grp, name, data, type_string, options):
        # data just needs to be converted to a list and then pass it to
        # the parent version of this function. The proper type_string
        # needs to be grabbed now as the parent function will have a
        # modified form of data to guess from if not given the right one
        # explicitly.
        PythonListMarshaller.write(self, f, grp, name, list(data),
                                  self.get_type_string(data,
                                  type_string), options)

    def read(self, f, grp, name, options):
        # Use the parent class version to read it and do most of the
        # work.
        data = PythonListMarshaller.read(self, f, grp, name,
                                        options)

        # The type string determines how to convert it back to a Python
        # type (just look up the entry in types).
        type_string = get_attribute_string(grp[name], 'Python.Type')
        if type_string in self.python_type_strings:
            tp = self.types[self.python_type_strings.index(
                            type_string)]
            return tp(data)
        else:
            # Must be some other type, so return it as is.
            return data
