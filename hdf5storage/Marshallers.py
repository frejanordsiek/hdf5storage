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

""" Module for the classes to marshall Python types to/from file.

"""

import posixpath
import collections

import numpy as np
import h5py

from hdf5storage.utilities import *
from hdf5storage.lowlevel import write_data, read_data


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
        #: an ``Option.store_type_information`` is ``True``.
        self.python_attributes = {'Python.Type'}

        #: Attributes used for MATLAB compatibility.
        #:
        #: ``set`` of ``str``
        #:
        #: ``set`` of attribute names the marshaller uses when maintaing
        #: Matlab HDF5 based mat file compatibility
        #: (``Option.matlab_compatible`` is ``True``).
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

        if options.store_type_information:
            set_attribute_string(grp[name], 'Python.Type', type_string)

        # If we are not storing type information or doing MATLAB
        # compatibility, then attributes not in the python and/or
        # MATLAB lists need to be removed.

        attributes_used = set()

        if options.store_type_information:
            attributes_used |= self.python_attributes

        if options.matlab_compatible:
            attributes_used |= self.matlab_attributes

        for attribute in (set(grp[name].attrs.keys()) - attributes_used):
            del_attribute(grp[name], attribute)

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
        self.python_attributes |= {'Python.Shape', 'Python.Empty',
                                   'Python.numpy.UnderlyingType',
                                   'Python.numpy.Container'}
        self.matlab_attributes |= {'MATLAB_class', 'MATLAB_empty',
                                   'MATLAB_int_decode'}
        self.types = [np.ndarray, np.matrix,
                      np.bool_,
                      np.uint8, np.uint16, np.uint32, np.uint64,
                      np.int8, np.int16, np.int32, np.int64,
                      np.float16, np.float32, np.float64,
                      np.complex64, np.complex128,
                      np.bytes_, np.str_, np.object_]
        self.python_type_strings = ['numpy.ndarray', 'numpy.matrix',
                                    'numpy.bool_',
                                    'numpy.uint8', 'numpy.uint16',
                                    'numpy.uint32', 'numpy.uint64',
                                    'numpy.int8', 'numpy.int16',
                                    'numpy.int32', 'numpy.int64',
                                    'numpy.float16', 'numpy.float32',
                                    'numpy.float64',
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
                                 np.str_: 'char',
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
                                         'char': np.str_,
                                         'cell': np.object_}


        # Set matlab_classes to the supported classes (the values).
        self.matlab_classes = list(self.__MATLAB_classes.values())

    def write(self, f, grp, name, data, type_string, options):
        # Need to make a set of data that will be stored. It will start
        # out as a copy of data and then be steadily manipulated.

        data_to_store = data.copy()

        # Optionally convert ASCII strings to UTF-16. This is done by
        # simply converting to uint16's. This will require making them
        # at least 1 dimensinal.

        if data.dtype.type == np.bytes_ \
                and options.convert_numpy_bytes_to_utf16:
            if data_to_store.nbytes == 0:
                data_to_store = np.uint16([])
            else:
                data_to_store = np.uint16(np.atleast_1d( \
                    data_to_store).view(np.uint8))

        # As of 2013-12-13, h5py cannot write numpy.str_ (UTF-32
        # encoding) types. If the option is set to try to convert them
        # to UTF-16, then an attempt at the conversion is made. If no
        # conversion is to be done, the conversion throws an exception
        # (a UTF-32 character had no UTF-16 equivalent), or a UTF-32
        # character gets turned into a UTF-16 doublet (the increase in
        # the number of columns will be by a factor more than the length
        # of the strings); then it will be simply converted to uint32's
        # byte for byte instead.

        if data.dtype.type == np.str_:
            new_data = None
            if options.convert_numpy_str_to_utf16:
                try:
                    new_data = convert_numpy_str_to_uint16( \
                        data_to_store)
                except:
                    pass
            if new_data is None or (type(data_to_store) == np.str_ \
                    and len(data_to_store) == len(new_data)) \
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

        if options.convert_scalars_to_arrays:
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
            ref_dtype = h5py.special_dtype(ref=h5py.Reference)
            data_refs = data_to_store.copy()

            # Go through all the elements of data and write them,
            # gabbing their references and putting them in
            # data_refs. They will be put in group_for_references, which
            # is also what the H5PATH needs to be set to if we are doing
            # MATLAB compatibility (otherwise, the attribute needs to be
            # deleted).

            if options.group_for_references not in f:
                f.create_group(options.group_for_references)

            grp2 = f[options.group_for_references]

            if not isinstance(grp2, h5py.Group):
                del f[options.group_for_references]
                grp2 = f[options.group_for_references]

            for index, x in np.ndenumerate(data_to_store):
                data_refs[index] = None
                name_for_ref = next_unused_name_in_group(grp2, 16)
                write_data(f, grp2, name_for_ref, x, None, options)
                data_refs[index] = grp2[name_for_ref].ref
                if options.matlab_compatible:
                    set_attribute_string(grp2[name_for_ref],
                                         'H5PATH', grp2.name)
                else:
                    del_attribute(grp2[name_for_ref], 'H5PATH')

            # Now, the dtype needs to be changed to the reference type
            # and the whole thing copied over to data_to_store.
            data_to_store = data_refs.astype(dtype=ref_dtype)

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

        # If we are storing type information; the shape, underlying
        # numpy type, and its type of container ('scalar', 'ndarray', or
        # 'matrix') need to be stored.

        if options.store_type_information:
            set_attribute(grp[name], 'Python.Shape',
                          np.uint64(data.shape))
            set_attribute_string(grp[name],
                                 'Python.numpy.UnderlyingType',
                                 data.dtype.name)
            if isinstance(data, np.matrix):
                container = 'matrix'
            elif isinstance(data, np.ndarray):
                container = 'ndarray'
            else:
                container = 'scalar'
            set_attribute_string(grp[name], 'Python.numpy.Container',
                                 container)

        # If data is empty, we need to set the Python.Empty and
        # MATLAB_empty attributes to 1 if we are storing type info or
        # making it MATLAB compatible. Otherwise, no empty attribute is
        # set and existing ones must be deleted.

        if data.size == 0  or ((data.dtype.type == np.bytes_ \
                or data.dtype.type == np.str_)
                and data.nbytes == 0):
            if options.store_type_information:
                set_attribute(grp[name], 'Python.Empty',
                                          np.uint8(1))
            else:
                del_attribute(grp[name], 'Python.Empty')
            if options.matlab_compatible:
                set_attribute(grp[name], 'MATLAB_empty',
                                          np.uint8(1))
            else:
                del_attribute(grp[name], 'MATLAB_empty')
        else:
            del_attribute(grp[name], 'Python.Empty')
            del_attribute(grp[name], 'MATLAB_empty')

        # If we are making it MATLAB compatible, the MATLAB_class
        # attribute needs to be set looking up the data type (gotten
        # using np.dtype.type). If it is a string or bool type, then
        # the MATLAB_int_decode attribute must be set to the number of
        # bytes each element takes up (dtype.itemsize). Otherwise,
        # the attributes must be deleted.

        if options.matlab_compatible:
            tp = data.dtype.type
            if tp in self.__MATLAB_classes:
                set_attribute_string(grp[name], 'MATLAB_class',
                                     self.__MATLAB_classes[tp])
            else:
                set_attribute_string(grp[name], 'MATLAB_class', '')

            if tp in (np.bytes_, np.str_, np.bool_):
                set_attribute(grp[name], 'MATLAB_int_decode', np.int64(
                              grp[name].dtype.itemsize))
            else:
                del_attribute(grp[name], 'MATLAB_int_decode')

    def read(self, f, grp, name, options):
        # If name is not present or is not a Dataset, then we can't read
        # it and have to throw an error.
        if name not in grp or not isinstance(grp[name], h5py.Dataset):
            raise NotImplementedError('No Dataset ' + name +
                                      ' is present.')

        # Grab the data's datatype and dtype.
        datatype = grp[name].id.get_type()
        h5_dt = datatype.dtype

        # Get the different attributes this marshaller uses.

        type_string = get_attribute_string(grp[name], 'Python.Type')
        underlying_type = get_attribute_string(grp[name], \
            'Python.numpy.UnderlyingType')
        shape = get_attribute(grp[name], 'Python.Shape')
        container = get_attribute_string(grp[name], \
            'Python.numpy.Container')
        python_empty = get_attribute(grp[name], 'Python.Empty')

        matlab_class = get_attribute_string(grp[name], 'MATLAB_class')
        matlab_empty = get_attribute(grp[name], 'MATLAB_empty')

        # Read the data and get its dtype. Figuring it out and doing any
        # conversions can be done later.
        data = grp[name][...]
        dt = data.dtype

        # If it is a reference type, then we need to make an object
        # array that is its replicate, but with the objects they are
        # pointing to in their elements instead of just the references.
        if h5py.check_dtype(ref=grp[name].dtype) is not None:
            data_derefed = data.copy().astype(np.dtype('object'))

            # Go through all the elements of data and read them using
            # their references, and the putting the output in
            # data_derefed. If they can't be read, None is put in.

            for index, x in np.ndenumerate(data):
                data_derefed[index] = None
                try:
                    data_derefed[index] = read_data(f, f[x].parent, \
                        posixpath.basename(f[x].name), options)
                except:
                    raise

            # Now all that needs to be done is copy back to data.
            data = data_derefed.copy()

        # If metadata is present, that can be used to do convert to the
        # desired/closest Python data types. If none is present, or not
        # enough of it, then no conversions can be done.

        if type_string is not None and underlying_type is not None and \
                shape is not None:
            # If it is empty ('Python.Empty' set to 1), then the shape
            # information is stored in data and we need to set data to
            # the empty array of the proper type (in underlying_type)
            # and the given shape. If we are going to transpose it
            # later, we need to transpose it now so that it still keeps
            # the right shape.
            if python_empty == 1:
                if underlying_type.startswith('bytes'):
                    data = np.zeros(tuple(shape), dtype='S1')
                elif underlying_type.startswith('str'):
                    data = np.zeros(tuple(shape), dtype='U1')
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
                    data = decode_to_numpy_bytes(data, \
                        length=int(underlying_type[5:])//8)
            elif underlying_type.startswith('str') \
                    or matlab_class == 'char':
                if underlying_type == 'str':
                    data = np.str_('')
                elif underlying_type.startswith('str'):
                    data = decode_to_numpy_str(data, \
                        length=int(underlying_type[3:])//32)
                else:
                    data = decode_to_numpy_str(data)

            # If the shape of data and the shape attribute are
            # different but give the same number of elements, then data
            # needs to be reshaped.
            if tuple(shape) != data.shape \
                    and np.prod(shape) == np.prod(data.shape):
                data = data.reshape(tuple(shape))

            # Convert to scalar, matrix, or ndarray depending on the
            # container type. For an empty scalar string, it needs to be
            # manually set to '' and b'' or there will be problems.
            if container == 'scalar':
                if underlying_type.startswith('bytes'):
                    if python_empty == 1:
                        data = np.bytes_(b'')
                    elif isinstance(data, np.ndarray):
                        data = data.flatten()[0]
                elif underlying_type.startswith('str'):
                    if python_empty == 1:
                        data = np.bytes_(b'')
                    elif isinstance(data, np.ndarray):
                        data = data.flatten()[0]
                else:
                    data = data.flatten()[0]
            elif container == 'matrix':
                data = np.asmatrix(data)
            elif container == 'ndarray':
                data = np.asarray(data)

        elif matlab_class in self.__MATLAB_classes_reverse:
            # MATLAB formatting information was given. The extraction
            # did most of the work except handling empties, array
            # dimension order, and string conversion.

            # If it is empty ('MATLAB_empty' set to 1), then the shape
            # information is stored in data and we need to set data to
            # the empty array of the proper type.
            if matlab_empty == 1:
                data = np.zeros(tuple(np.uint64(data)), \
                    dtype=self.__MATLAB_classes_reverse[matlab_class])

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
                data = decode_to_numpy_str(data)

        # Done adjusting data, so it can be returned.
        return data


class PythonScalarMarshaller(NumpyScalarArrayMarshaller):
    def __init__(self):
        NumpyScalarArrayMarshaller.__init__(self)
        self.types = [bool, int, float, complex]
        self.python_type_strings = ['bool', 'int', 'float', 'complex']
        # As the parent class already has MATLAB strings handled, there
        # are no MATLAB classes that this marshaller should be used for.
        self.matlab_classes = []

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

    def read(self, f, grp, name, options):
        # Use the parent class version to read it and do most of the
        # work.
        data = NumpyScalarArrayMarshaller.read(self, f, grp, name,
                                               options)

        # The type string determines how to convert it back to a Python
        # type (just look up the entry in types). As it might be
        # returned as an ndarray, it needs to be run through
        # np.asscalar.
        type_string = get_attribute_string(grp[name], 'Python.Type')
        if type_string in self.python_type_strings:
            tp = self.types[self.python_type_strings.index(
                            type_string)]
            return tp(np.asscalar(data))
        else:
            # Must be some other type, so return it as is.
            return data


class PythonStringMarshaller(NumpyScalarArrayMarshaller):
    def __init__(self):
        NumpyScalarArrayMarshaller.__init__(self)
        self.types = [str, bytes, bytearray]
        self.python_type_strings = ['str', 'bytes', 'bytearray']
        # As the parent class already has MATLAB strings handled, there
        # are no MATLAB classes that this marshaller should be used for.
        self.matlab_classes = []

    def write(self, f, grp, name, data, type_string, options):
        # data just needs to be converted to a numpy string.
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
            if isinstance(data, np.ndarray):
                return data.tostring().decode()
            else:
                return data.decode()
        elif type_string == 'bytes':
            return bytes(data)
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
        self.python_attributes |= {'Python.Empty'}
        self.matlab_attributes |= {'MATLAB_class', 'MATLAB_empty'}
        self.types = [dict]
        self.python_type_strings = ['dict']
        self.__MATLAB_classes = {dict: 'struct'}
        # Set matlab_classes to the supported classes (the values).
        self.matlab_classes = list(self.__MATLAB_classes.values())

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

        # Go through all the elements of data and write them. The H5PATH
        # needs to be set as the path of grp2 on all of them if we are
        # doing MATLAB compatibility (otherwise, the attribute needs to
        # be deleted).
        for k, v in data.items():
            write_data(f, grp2, k, v, None, options)
            if options.matlab_compatible:
                set_attribute_string(grp2[k], 'H5PATH', grp2.name)
            else:
                del_attribute(grp2[k], 'H5PATH')

    def write_metadata(self, f, grp, name, data, type_string, options):
        # First, call the inherited version to do most of the work.

        TypeMarshaller.write_metadata(self, f, grp, name, data,
                                      type_string, options)

        # If data is empty and we are supposed to store shape info for
        # empty data, we need to set the Python.Empty and MATLAB_empty
        # attributes to 1 if we are storing type info or making it
        # MATLAB compatible. Otherwise, no empty attribute is set and
        # existing ones must be deleted.

        if options.store_shape_for_empty and len(data) == 0:
            if options.store_type_information:
                set_attribute(grp[name], 'Python.Empty',
                                          np.uint8(1))
            else:
                del_attribute(grp[name], 'Python.Empty')
            if options.matlab_compatible:
                set_attribute(grp[name], 'MATLAB_empty',
                                          np.uint8(1))
            else:
                del_attribute(grp[name], 'MATLAB_empty')
        else:
            del_attribute(grp[name], 'Python.Empty')
            del_attribute(grp[name], 'MATLAB_empty')

        # If we are making it MATLAB compatible, the MATLAB_class
        # attribute needs to be set for the data type. If the type
        # cannot be found or if we are not doing MATLAB compatibility,
        # the attributes need to be deleted.

        tp = type(data)
        if options.matlab_compatible and tp in self.types \
                and self.types.index(tp) in self.__MATLAB_classes:
            set_attribute_string(grp[name], 'MATLAB_class', \
                self.__MATLAB_classes[self.types.index(tp)])
        else:
            del_attribute(grp[name], 'MATLAB_class')

        # Write an array of all the fields to the attribute that lists
        # them.
        #
        # NOTE: Can't make it do a variable length set of strings like
        # MATLAB likes. However, not including them seems to cause no
        # problem.
        #
        # set_attribute_string_array(grp[name], \
        #     'MATLAB_fields', [k for k in data])

    def read(self, f, grp, name, options):
        # If name is not present or is not a Group, then we can't read
        # it and have to throw an error.
        if name not in grp or not isinstance(grp[name], h5py.Group):
            raise NotImplementedError('No Group ' + name +
                                      ' is present.')

        # Starting with an empty dict, all that has to be done is
        # iterate through all the Datasets and Groups in grp[name] and
        # add them to the dict with their name as the key. Since we
        # don't want an exception thrown by reading an element to stop
        # the whole reading process, the reading is wrapped in a try
        # block that just catches exceptions and then does nothing about
        # them (nothing needs to be done).
        data = dict()
        for k in grp[name]:
            # We must exclude group_for_references
            if grp[name][k].name == options.group_for_references:
                continue
            try:
                data[k] = read_data(f, grp[name], k, options)
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
        NumpyScalarArrayMarshaller.write(self, f, grp, name,
                                         np.object_(data),
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
