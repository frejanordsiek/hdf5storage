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

import numpy as np
import h5py

from hdf5storage.utilities import *
from hdf5storage.lowlevel import write_data


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
    method.

    Attributes
    ----------
    cpython_attributes : set of str
        Attributes used to store type information.
    matlab_attributes : set of str
        Attributes used for MATLAB compatibility.
    types : list of types
        Types the marshaller can work on.
    cpython_type_strings : list of str
        Type strings of readable types.
    makes_datasets : bool
        At least one type marshalled as Dataset.
    makes_groups : bool
        At least one type marshalled as Group.

    See Also
    --------
    hdf5storage.core.Options
    h5py.Dataset
    h5py.Group
    h5py.AttributeManager

    """
    def __init__(self):
        #: Attributes used to store type information.
        #:
        #: set of str
        #:
        #: ``set`` of attribute names the marshaller uses when
        #: an ``Option.store_type_information`` is ``True``.
        self.cpython_attributes = {'CPython.Type'}

        #: Attributes used for MATLAB compatibility.
        #:
        #: ``set`` of ``str``
        #:
        #: ``set`` of attribute names the marshaller uses when maintaing
        #: Matlab HDF5 based mat file compatibility
        #: (``Option.MATLAB_compatible`` is ``True``).
        self.matlab_attributes = {'H5PATH'}

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
        #: HDF5 attribute 'CPython.Type' to identify the Python type to be
        #: able to read it back correctly. Default value is ``[]``.
        self.cpython_type_strings = []

        #: At least one type marshalled as Dataset.
        #:
        #: bool
        #:
        #: Whether or not at least one of the types that this marshaller
        #: works with get put into HDF5 Datasets. Default value is
        #: ``False``.
        self.makes_datasets = False

        #: At least one type marshalled as Group.
        #:
        #: bool
        #:
        #: Whether or not at least one of the types that this marshaller
        #: works with get put into HDF5 Groups. Default value is
        #: ``False``.
        self.makes_groups = False

    def get_type_string(self, data, type_string):
        """ Gets type string.

        Finds the type string for 'data' contained in
        ``cpython_type_strings`` using its ``type``. Non-``None``
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
            return self.cpython_type_strings[i]

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
            The type string for 'data'. If it is ``None``, one will have
            to be gotten by ``get_type_string``.
        options : hdf5storage.core.Options
            hdf5storage options object.

        Raises
        ------
        NotImplementedError
            If writing 'data' to file is currently not supported.

        Notes
        -----
        Must be overridden in a subclass because a
        ``NotImplementedError`` is thrown immediately.

        """
        raise NotImplementedError('Can''t write data type: '
                                  + str(type(data)))

    def write_metadata(self, f, grp, name, data, type_string, options):
        """ Writes an object to file.

        Writes the metadata for a Python object 'data' to file at 'name'
        in h5py.Group 'grp'. Metadata is written to HDF5
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
            The type string for 'data'. If it is ``None``, one will have
            to be gotten by ``get_type_string``.
        options : hdf5storage.core.Options
            hdf5storage options object.

        Notes
        -----
        The attribute 'CPython.Type' is set to the type string. All H5PY
        Attributes not in ``cpython_attributes`` and/or
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

        if options.store_type_information:
            set_attribute_string(grp[name], 'CPython.Type', type_string)

        # If we are not storing type information or doing MATLAB
        # compatibility, then attributes not in the cpython and/or
        # MATLAB lists need to be removed.

        attributes_used = set()

        if options.store_type_information:
            attributes_used |= self.cpython_attributes

        if options.MATLAB_compatible:
            attributes_used |= self.matlab_attributes

        for attribute in (set(grp[name].attrs.keys()) - attributes_used):
            del_attribute(grp[name], attribute)

    def can_read(self, f, grp, name, options):
        """ Whether the marshaller can read the object from file.

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

        Returns
        -------
        bool
            Whether this marshaller can read the object from file or
            not.

        Notes
        -----
        Unless replaced in a subclass, it is always ``False``.

        """
        return False

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

        """
        raise NotImplementedError('Can''t read data: ' + name)


class NumpyScalarArrayMarshaller(TypeMarshaller):
    def __init__(self):
        TypeMarshaller.__init__(self)
        self.cpython_attributes |= {'CPython.Shape', 'CPython.Empty',
                                    'CPython.numpy.UnderlyingType'}
        self.matlab_attributes |= {'MATLAB_class', 'MATLAB_empty',
                                   'MATLAB_int_decode'}
        self.types = [np.ndarray, np.matrix,
                      np.bool8,
                      np.uint8, np.uint16, np.uint32, np.uint64,
                      np.int8, np.int16, np.int32, np.int64,
                      np.float16, np.float32, np.float64, np.float128,
                      np.complex64, np.complex128, np.complex256,
                      np.string_, np.unicode]
        self.cpython_type_strings = ['numpy.ndarray', 'numpy.matrix',
                                     'numpy.bool8',
                                     'numpy.uint8', 'numpy.uint16',
                                     'numpy.uint32', 'numpy.uint64',
                                     'numpy.int8', 'numpy.int16',
                                     'numpy.int32', 'numpy.int64',
                                     'numpy.float16', 'numpy.float32',
                                     'numpy.float64', 'numpy.float128',
                                     'numpy.complex64',
                                     'numpy.complex128',
                                     'numpy.complex256',
                                     'numpy.string_', 'numpy.unicode']

        # If we are storing in MATLAB format, we will need to be able to
        # set the MATLAB_class attribute. The different numpy types just
        # need to be properly mapped to the right strings. Some types do
        # not have a string since MATLAB does not support them.

        self.__MATLAB_classes = {np.bool8: 'logical', np.uint8: 'uint8',
                                 np.uint16: 'uint16',
                                 np.uint32: 'uint32',
                                 np.uint64: 'uint64', np.int8: 'int8',
                                 np.int16: 'int16', np.int32: 'int32',
                                 np.int64: 'int64', np.float32: 'single',
                                 np.float64: 'double',
                                 np.complex64: 'single',
                                 np.complex128: 'double',
                                 np.string_: 'char',
                                 np.unicode: 'char'}


    def write(self, f, grp, name, data, type_string, options):
        # Need to make a set of data that will be stored. It will start
        # out as a copy of data and then be steadily manipulated.

        data_to_store = data.copy()

        # Optionally convert ASCII strings to UTF-16. This is done by
        # simply converting to uint16's. This will require making them
        # at least 1 dimensinal.

        if options.convert_strings_to_utf16 and not (data.size == 0 \
                and options.store_shape_for_empty) \
                and data.dtype.type == np.string_:
            data_to_store = np.uint16(np.atleast_1d( \
                            data_to_store).view(np.uint8))

        # As of 2013-12-13, h5py cannot write numpy.unicode (UTF-32
        # encoding) types. If it is just a numpy.unicode object, we can
        # force it to UTF-16 or just write it as uint32's. If it is an
        # array, forcing it to UTF-16 is a bad idea because characters
        # are not always 2 bytes long in UTF-16. So, converting them to
        # uint32 makes the most sense.

        if data.dtype.type == np.unicode and not (data.size == 0 \
                and options.store_shape_for_empty):
            data_to_store = np.atleast_1d(data_to_store).view(np.uint32)

        # Convert scalars to arrays if that option is set.

        if options.convert_scalars_to_arrays:
            data_to_store = np.atleast_2d(data_to_store)

        # If data is empty, we instead need to store the shape of the
        # array if the appropriate option is set.

        if options.store_shape_for_empty and data.size == 0:
            data_to_store = np.uint64(data.shape)
            if options.convert_scalars_to_arrays:
                data_to_store = np.atleast_2d(data_to_store)

        # Reverse the dimension order if that option is set.

        if options.reverse_dimension_order:
            data_to_store = data_to_store.T

        # The data must first be written. If name is not present yet,
        # then it must be created. If it is present, but not a Dataset,
        # has the wrong dtype, or is the wrong shape; then it must be
        # deleted and then written. Otherwise, it is just overwritten in
        # place (note, this will not change any filters or chunking
        # settings, but will keep the file from growing needlessly).

        if name not in grp:
            grp.create_dataset(name, data=data_to_store,
                               **options.array_options)
        elif not isinstance(grp[name], h5py.Dataset) \
                or grp[name].dtype != data_to_store.dtype \
                or grp[name].shape != data_to_store.shape:
            del grp[name]
            grp.create_dataset(name, data=data_to_store,
                               **options.array_options)
        else:
            grp[name][...] = data_to_store

        # Write the metadata using the inherited function (good enough).

        self.write_metadata(f, grp, name, data, type_string, options)


    def write_metadata(self, f, grp, name, data, type_string, options):
        # First, call the inherited version to do most of the work.

        TypeMarshaller.write_metadata(self, f, grp, name, data,
                                      type_string, options)

        # Write the underlying numpy type if we are storing type
        # information.

        if options.store_type_information:
            set_attribute_string(grp[name],
                                 'CPython.numpy.UnderlyingType',
                                 data.dtype.name)

        # If we are storing type information, the shape needs to be
        # stored in CPython.Shape.

        if options.store_type_information:
            set_attribute(grp[name], 'CPython.Shape',
                          np.uint64(data.shape))

        # If data is empty and we are supposed to store shape info for
        # empty data, we need to set the CPython.Empty and MATLAB_empty
        # attributes to 1 if we are storing type info or making it
        # MATLAB compatible. Otherwise, no empty attribute is set and
        # existing ones must be deleted.

        if options.store_shape_for_empty and data.size == 0:
            if options.store_type_information:
                set_attribute(grp[name], 'CPython.Empty',
                                          np.uint8(1))
            else:
                del_attribute(grp[name], 'CPython.Empty')
            if options.MATLAB_compatible:
                set_attribute(grp[name], 'MATLAB_empty',
                                          np.uint8(1))
            else:
                del_attribute(grp[name], 'MATLAB_empty')
        else:
            del_attribute(grp[name], 'CPython.Empty')
            del_attribute(grp[name], 'MATLAB_empty')

        # If we are making it MATLAB compatible, the MATLAB_class
        # attribute needs to be set looking up the data type (gotten
        # using np.dtype.type) and if it is a string type, then the
        # MATLAB_int_decode attribute must be set properly. Otherwise,
        # the attributes must be deleted.

        if options.MATLAB_compatible:
            tp = data.dtype.type
            if tp in self.__MATLAB_classes:
                set_attribute_string(grp[name], 'MATLAB_class',
                                     self.__MATLAB_classes[tp])
            else:
                set_attribute_string(grp[name], 'MATLAB_class', '')

            if tp in (np.string_, np.unicode):
                set_attribute(grp[name], 'MATLAB_int_decode', np.int64(
                              {np.string_: 2, np.unicode: 4}[tp]))
            else:
                del_attribute(grp[name], 'MATLAB_int_decode')


class PythonScalarMarshaller(NumpyScalarArrayMarshaller):
    def __init__(self):
        NumpyScalarArrayMarshaller.__init__(self)
        self.types = [bool, int, float, complex]
        self.cpython_type_strings = ['bool', 'int', 'float', 'complex']

    def write(self, f, grp, name, data, type_string, options):
        # data just needs to be converted to the appropriate numpy type
        # (pass it through np.array and then access [()] to get the
        # scalar back as a scalar numpy type) and then pass it to the
        # parent version of this function. The proper type_string needs
        # to be grabbed now as the parent function will have a modified
        # form of data to guess from if not given the right one
        # explicitly.
        NumpyScalarArrayMarshaller.write(self, f, grp, name,
                                         np.array(data)[()],
                                         self.get_type_string(data,
                                         type_string), options)


class PythonStringMarshaller(NumpyScalarArrayMarshaller):
    def __init__(self):
        NumpyScalarArrayMarshaller.__init__(self)
        self.types = [str, bytes, bytearray]
        self.cpython_type_strings = ['str', 'bytes', 'bytearray']

    def write(self, f, grp, name, data, type_string, options):
        # data just needs to be converted to a numpy string, unless it
        # is a bytearray in which case it needs to be converted to a
        # uint8 array.

        if isinstance(data,bytearray):
            cdata = np.uint8(data)
        else:
            cdata = np.string_(data)

        # Now pass it to the parent version of this function to write
        # it. The proper type_string needs to be grabbed now as the
        # parent function will have a modified form of data to guess
        # from if not given the right one explicitly.
        NumpyScalarArrayMarshaller.write(self, f, grp, name, cdata,
                                         self.get_type_string(data,
                                         type_string), options)


class PythonNoneMarshaller(NumpyScalarArrayMarshaller):
    def __init__(self):
        NumpyScalarArrayMarshaller.__init__(self)
        self.types = [type(None)]
        self.cpython_type_strings = ['builtins.NoneType']
    def write(self, f, grp, name, data, type_string, options):
        # Just going to use the parent function with an empty double
        # (two dimensional so that MATLAB will import it as a []) as the
        # data and the right type_string set (parent can't guess right
        # from the modified form).
        NumpyScalarArrayMarshaller.write(self, f, grp, name,
                                         np.ndarray(shape=(0,0),
                                         dtype='float64'),
                                         self.get_type_string(data,
                                         type_string), options)

class PythonDictMarshaller(TypeMarshaller):
    def __init__(self):
        TypeMarshaller.__init__(self)
        self.cpython_attributes |= {'CPython.Empty'}
        self.matlab_attributes |= {'MATLAB_class', 'MATLAB_empty'}
        self.types = [dict]
        self.cpython_type_strings = ['dict']
        self.__MATLAB_classes = ['struct']

    def write(self, f, grp, name, data, type_string, options):
        # If the group doesn't exist, it needs to be created. If it
        # already exists but is not a group, it needs to be deleted
        # before being created.

        if name not in grp:
            grp.create_group(name)
        elif not isinstance(grp[name], h5py.Group):
            del grp[name]
            grp.create_group(name)

        grp2 = grp[name]

        # Write the metadata.
        self.write_metadata(f, grp, name, data, type_string, options)

        # Delete any Datasets/Groups not corresponding to a field name
        # in data if that option is set.

        if options.delete_unused_variables:
            for field in {i for i in grp2}.difference({i for i in data}):
                del grp2[field]

        # Check for any field names that are not strings since they
        # cannot be handled.

        for fieldname in data:
            if not isinstance(fieldname, str):
                raise NotImplementedError('Dictionaries with non-string'
                                          + ' keys are not supported: '
                                          + repr(fieldname))

        # Return a tuple holding the group to store in, all the elements
        # of data, and their values to the calling function so that it
        # can recurse over all the elements.

        return ([grp2], [(n, v) for n, v in data.items()])

    def write_metadata(self, f, grp, name, data, type_string, options):
        # First, call the inherited version to do most of the work.

        TypeMarshaller.write_metadata(self, f, grp, name, data,
                                      type_string, options)

        # If data is empty and we are supposed to store shape info for
        # empty data, we need to set the CPython.Empty and MATLAB_empty
        # attributes to 1 if we are storing type info or making it
        # MATLAB compatible. Otherwise, no empty attribute is set and
        # existing ones must be deleted.

        if options.store_shape_for_empty and len(data) == 0:
            if options.store_type_information:
                set_attribute(grp[name], 'CPython.Empty',
                                          np.uint8(1))
            else:
                del_attribute(grp[name], 'CPython.Empty')
            if options.MATLAB_compatible:
                set_attribute(grp[name], 'MATLAB_empty',
                                          np.uint8(1))
            else:
                del_attribute(grp[name], 'MATLAB_empty')
        else:
            del_attribute(grp[name], 'CPython.Empty')
            del_attribute(grp[name], 'MATLAB_empty')

        # If we are making it MATLAB compatible, the MATLAB_class
        # attribute needs to be set for the data type. Also, all the
        # field names need to be stored in the attribute MATLAB_fields.
        # If the type cannot be found, an error needs to be thrown. If
        # we are not doing MATLAB compatibility, the attributes need to
        # be deleted.

        if options.MATLAB_compatible:
            tp = type(data)
            if tp in self.types:
                set_attribute_string(grp[name], \
                            'MATLAB_class', self.__MATLAB_classes[ \
                            self.types.index(tp)])
            else:
                raise NotImplementedError('Can''t write data type: '
                                          + str(tp))

            # Write an array of all the fields to the attribute that
            # lists them.

            # NOTE: Can't make it do a variable length set of strings
            # like MATLAB likes. However, not including them seems to
            # cause no problem.

            # set_attribute_string_array(grp[name], \
            #     'MATLAB_fields', [k for k in data])
