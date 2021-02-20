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

""" Module for the classes to marshall Python types to/from file. """

import ast
import collections
import datetime
import importlib
import inspect
import warnings

import numpy as np
import h5py

from .pathesc import escape_path, unescape_path
from .utilities import does_dtype_have_a_zero_shape, \
    convert_numpy_str_to_uint16, convert_numpy_str_to_uint32, \
    convert_to_str, convert_to_numpy_str, convert_to_numpy_bytes, \
    decode_complex, encode_complex, convert_attribute_to_string, \
    convert_attribute_to_string_array, set_attribute_string, \
    set_attributes_all, del_attribute, convert_dtype_to_str
import hdf5storage.exceptions


class TypeMarshaller(object):
    """ Base class for marshallers of Python types.

    Base class providing the class interface for marshallers of Python
    types to/from disk. All marshallers must inherit from this
    class and override some of its methods and attributes. Just
    replicating its functionality is not enough. This includes several
    attributes that are needed in order for reading/writing methods to
    know if it is the appropriate marshaller to use and methods to
    actually do the reading and writing.

    Marshallers are supported for types whose modules/packages may not
    be present (only guaranteed modules/packages are the Python runtime,
    numpy, and h5py). Obviously, if such a type is run into for writing,
    the needed modules are there. However, if such a type is found in a
    file for reading, it still needs to be read regardless of whether
    the required modules are present or not. If the required modules are
    there, the data will be read accurately using the ``read``
    method. However, if one or more of the required modules are missing,
    the data will be read approximately/inaccurately using the
    ``read_approximate`` method is used, which must return an
    approximation of the data utilizing standard Python types or numpy
    types. A good example of a situation where this would be needed
    would be reading back a scipy sparse type when scipy is not present
    and thus it must be approximated (say, a conversion to a dense array
    or just the fields specifying it in a ``dict``). Note that for types
    not in the main Python runtime or numpy, their types in ``types``
    must be specified in ``str`` form including module. For example,
    ``collections.deque`` is ``'collections.deque'``.

    Whether the marshaller can read types accurately with ``read`` or
    approximately with ``read_approximate`` is determined by whether the
    parent modules in ``required_parent_modules`` is/are present or
    not. If ``read`` is called, all the modules in ``required_modules``
    will be loaded first (no additional latency). The ``read`` method
    must locally load the modules, though, in order to use them.

    Note that it may be convenient for a marshaller that handles types
    in the main Python runtime but in modules that are rather large to
    use specify their types as ``str`` in ``types`` and put the required
    modules in ``required_parent_modules`` to not load those modules
    unless they are necessary - lazy loading essentially.

    Subclasses should run this class's ``__init__()`` first
    thing, set all attributes except ``type_to_typestring`` and
    ``typestring_to_type`` appropriately, and then call
    ``update_type_lookups()`` to set the two previous
    attributes. Inheritance information is in the **Notes** section of
    each method. Generally, ``read``, ``write``, and ``write_metadata``
    need to be overridden and the different attributes set to the proper
    values. ``read_approximate`` needs to be overridden for marshallers
    meant to handle types not from the main Python runtime and not from
    numpy.

    For marshalling types that are containers of other data, one will
    need to use use the appropriate reading/writing methods of the
    ``utilities.LowLevelFile`` passsed in the call to each method.

    .. versionchanged:: 0.2
       All marshallers must now inherit from this class.

    .. versionchanged:: 0.2
       Attributes were added, ``read_approximate`` was added, call
       signatures of the methods, and the initialization procedure were
       changed.

    .. versionchanged:: 0.2
       Instead of the file and options being passed to each method, a
       ``utilities.LowLevelFile`` is now passed instead.

    Warning
    -------
    Marshallers for version 0.1.x of this package are not compatible
    with version 0.2.x.

    Attributes
    ----------
    required_parent_modules : tuple of str
        The parent modules required for reading types accurately.
    required_modules: tuple of str
        The modules required to be loaded for reading types accurately.
    python_attributes : set of str
        Attributes used to store type information.
    matlab_attributes : set of str
        Attributes used for MATLAB compatibility.
    types : tuple of types
        Types the marshaller can work on, which can be the actual
        classes themselves or their ``str`` representation such as
        ``'collections.deque'``.
    python_type_strings : tuple of str
        Type strings of readable types.
    matlab_classes : tuple of str
        Readable MATLAB classes.
    type_to_typestring: dict
        Lookup using the types in ``types`` as keys and the matching
        entries in ``python_type_strings`` as values. Set using
        ``update_type_lookups``.
    typestring_to_type: dict
        Lookup using the type strings in ``python_type_strings`` as keys
        and the matching entries in ``types`` as values. Set using
        ``update_type_lookups``.

    See Also
    --------
    hdf5storage.Options
    h5py.Dataset
    h5py.Group
    h5py.AttributeManager
    hdf5storage.utilities.LowLevelFile
    hdf5storage.utilities.LowLevelFile.read_data
    hdf5storage.utilities.LowLevelFile.write_data

    """
    def __init__(self):
        #: Parent modules required to accurately read types.
        #:
        #: tuple of str
        #:
        #: The names of the parent modules required to accurately
        #: read the types handled by this marshaller. This tuple is
        #: used to determine whether they can be read accurately, or
        #: innaccurately due to missing the needed modules. Modules in
        #: the main Python runtime and numpy do not need to be included
        #: (they are assumed to be present). The default is ``[]``.
        #:
        #: .. versionadded:: 0.2
        self.required_parent_modules = ()

        #: All required modules for reading the types accurately.
        #:
        #: tuple of str
        #:
        #: The modules (and submodules) that need to be loaded, in
        #: order, to be able to read the types handled by this
        #: marshaller accurately. All of the modules in
        #: ``required_parent_modules`` must be included. Modules in
        #: the main Python runtime and numpy do not need to be
        #: included (they are assumed to be present). The default is
        #: ``[]``.
        #:
        #: .. versionadded:: 0.2
        self.required_modules = ()

        #: Attributes used to store type information.
        #:
        #: set of str
        #:
        #: ``set`` of attribute names the marshaller uses when
        #: an ``Option.store_python_metadata`` is ``True``.
        self.python_attributes = set(('Python.Type', ))

        #: Attributes used for MATLAB compatibility.
        #:
        #: ``set`` of ``str``
        #:
        #: ``set`` of attribute names the marshaller uses when maintaing
        #: Matlab HDF5 based mat file compatibility
        #: (``Option.matlab_compatible`` is ``True``).
        self.matlab_attributes = set(('H5PATH', ))

        #: Tuple of Python types that can be marshalled.
        #:
        #: tuple of types or str
        #:
        #: ``tuple`` of the types that the marshaller can marshall. They
        #: must all be the actual types gotten from ``type(data)``
        #: or their ``str`` representation such as
        #: ``'collections.deque'``. Default value is ``[]``.
        self.types = ()

        #: Type strings of readable types.
        #:
        #: tuple of str
        #:
        #: ``tuple`` of the ``str`` that the marshaller would put in the
        #: HDF5 attribute 'Python.Type' to identify the Python type to be
        #: able to read it back correctly. Default value is ``[]``.
        self.python_type_strings = ()

        #: MATLAB class strings of readable types.
        #:
        #: tuple of str
        #:
        #: ``tuple`` of the MATLAB class ``str`` that the marshaller can
        #: read into Python objects. Default value is ``[]``.
        self.matlab_classes = ()

        #: Type to typestring lookup.
        #:
        #: dict
        #:
        #: Lookup using the types in ``types`` as keys and the matching
        #: entries in ``python_type_strings`` as values. Set using
        #: ``update_type_lookups``.
        #:
        #: .. versionadded:: 0.2
        self.type_to_typestring = dict()

        #: Typestring to type lookup.
        #:
        #: dict
        #:
        #: Lookup using the type strings in ``python_type_strings`` as
        #: keys and the matching entries in ``types`` as values. Set
        #: using ``update_type_lookups``.
        #:
        #: .. versionadded:: 0.2
        self.typestring_to_type = dict()

    def update_type_lookups(self):
        """ Update type and typestring lookup dicts.

        Must be called once the ``types`` and ``python_type_strings``
        attributes are set so that ``type_to_typestring`` and
        ``typestring_to_type`` are constructed.

        .. versionadded:: 0.2

        Notes
        -----
        Subclasses need to call this function explicitly.

        """
        self.type_to_typestring = dict(zip(self.types,
                                           self.python_type_strings))
        self.typestring_to_type = dict(zip(self.python_type_strings,
                                           self.types))

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
            if isinstance(data, np.dtype):
                tp = np.dtype
            else:
                tp = type(data)
            try:
                return self.type_to_typestring[tp]
            except KeyError:
                return self.type_to_typestring[tp.__module__ + '.'
                                               + tp.__name__]

    def write(self, f, grp, name, data, type_string):
        """ Writes an object's metadata to file.

        Writes the Python object 'data' to 'name' in h5py.Group 'grp'.

        .. versionchanged:: 0.2
           Arguements changed.

        .. versionchanged:: 0.2
           Added return value `obj`.

        Parameters
        ----------
        f : hdf5storage.utilities.LowLevelFile
            The file.
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

        Returns
        -------
        obj : h5py.Dataset or h5py.Group or None
            The base Dataset or Group having the name `name` in `grp`
            that was made, or ``None`` if nothing was written.

        Raises
        ------
        NotImplementedError
            If writing 'data' to file is currently not supported.
        hdf5storage.exceptions.TypeNotMatlabCompatibleError
            If writing a type not compatible with MATLAB and
            `options.action_for_matlab_incompatible` is set to
            ``'error'``.

        Notes
        -----
        Must be overridden in a subclass because a
        ``NotImplementedError`` is thrown immediately.

        See Also
        --------
        hdf5storage.utilities.LowLevelFile.write_data

        """
        raise NotImplementedError('Can''t write data type: '
                                  + str(type(data)))

    def write_metadata(self, f, dsetgrp, data, type_string,
                       attributes=None):
        """ Writes an object to file.

        Writes the metadata for a Python object `data` to file at `name`
        in h5py.Group `grp`. Metadata is written to HDF5
        Attributes. Existing Attributes that are not being used are
        deleted.

        .. versionchanged:: 0.2
           Arguements changed.

        Parameters
        ----------
        f : hdf5storage.utilities.LowLevelFile
            The file.
        dsetgrp : h5py.Dataset or h5py.Group
            The Dataset or Group object to add metadata to.
        data
            The object to write to file.
        type_string : str or None
            The type string for `data`. If it is ``None``, one will have
            to be gotten by ``get_type_string``.
        attributes : dict or None, optional
            The Attributes to set. The keys (``str``) are the names. The
            values are ``tuple`` of the Attribute kind and the value to
            set. Valid kinds are ``'string_array'``, ``'string'``, and
            ``'value'``. The values must correspond to what
            ``set_attribute_string_array``, ``set_attribute_string`` and
            ``set_attribute`` would take respectively. Default is
            no Attributes to set (``None``).

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

        See Also
        --------
        utilities.set_attributes_all

        """
        if attributes is None:
            attributes = dict()
        # Make sure we have a complete type_string.
        if f.options.store_python_metadata \
                and 'Python.Type' not in attributes:
            attributes['Python.Type'] = (
                'string', self.get_type_string(data, type_string))
        set_attributes_all(dsetgrp, attributes, discard_others=True)

    def read(self, f, dsetgrp, attributes):
        """ Read a Python object from file.

        Reads the data at `dsetgrp` and converts it to a Python object
        and returns it.

        This method is called if the modules in
        ``required_parent_modules`` can be found. Otherwise,
        ``read_approximate`` is used instead.

        .. versionchanged:: 0.2
           Arguements changed.

        Parameters
        ----------
        f : hdf5storage.utilities.LowLevelFile
            The file.
        dsetgrp : h5py.Dataset or h5py.Group
            The Dataset or Group object to read.
        attributes : collections.defaultdict
            All the Attributes of `dsetgrp` with their names as keys and
            their values as values.

        Raises
        ------
        NotImplementedError
            If reading the object from file is currently not supported.

        Returns
        -------
        data
            The Python object.

        Notes
        -----
        Must be overridden in a subclass because a
        ``NotImplementedError`` is thrown immediately.

        See Also
        --------
        read_approximate
        required_parent_modules
        required_modules
        hdf5storage.utilities.LowLevelFile.read_data

        """
        raise NotImplementedError('Can''t read data: ' + dsetgrp.name)

    def read_approximate(self, f, dsetgrp, attributes):
        """ Read a Python object approximately from file.

        Reads the data at `dsetgrp` and returns an approximation of it
        constructed from the types in the main Python runtime and
        numpy.

        This method is called if the modules in
        ``required_parent_modules`` cannot be found. Otherwise, ``read``
        is used instead.

        .. versionadded:: 0.2

        Parameters
        ----------
        f : hdf5storage.utilities.LowLevelFile
            The file.
        dsetgrp : h5py.Dataset or h5py.Group
            The Dataset or Group object to read.
        attributes : collections.defaultdict
            All the Attributes of `dsetgrp` with their names as keys and
            their values as values.

        Raises
        ------
        NotImplementedError
            If reading the object from file is currently not supported.

        Returns
        -------
        data
            The Python object.

        Notes
        -----
        Must be overridden in a subclass because a
        ``NotImplementedError`` is thrown immediately.

        See Also
        --------
        read
        required_parent_modules
        required_modules
        hdf5storage.utilities.LowLevelFile.read_data

        """
        raise NotImplementedError('Can''t read data: ' + dsetgrp.name)


class NumpyScalarArrayMarshaller(TypeMarshaller):
    def __init__(self):
        TypeMarshaller.__init__(self)
        self.python_attributes |= set(
            ('Python.Shape', 'Python.Empty',
             'Python.numpy.UnderlyingType',
             'Python.numpy.Container',
             'Python.Fields'))
        self.matlab_attributes |= set(
            ('MATLAB_class', 'MATLAB_empty',
             'MATLAB_int_decode',
             'MATLAB_fields'))
        # As np.str_ is the unicode type string in Python 3 and the bare
        # bytes string in Python 2, we have to use np.unicode_ which is
        # or points to the unicode one in both versions.
        #
        # The numpy.matrix type is marked as pending deprecation, so we
        # must test for its presence explicitly. If it is no longer
        # around, we replace it with np.ndarray. We will set a flag on
        # whether it exists anymore or not.
        if hasattr(np, 'matrix') and inspect.isclass(np.matrix):
            matrix = np.matrix
            self._matrix_type_exists = True
        else:
            matrix = np.ndarray
            self._matrix_type_exists = False
        self.types = (np.ndarray, matrix,
                      np.chararray, np.core.records.recarray,
                      np.bool_, np.void,
                      np.uint8, np.uint16, np.uint32, np.uint64,
                      np.int8, np.int16, np.int32, np.int64,
                      np.float16, np.float32, np.float64,
                      np.complex64, np.complex128,
                      np.bytes_, np.unicode_, np.object_)
        self._numpy_types = self.types
        # Using Python 3 type strings.
        self.python_type_strings = ('numpy.ndarray', 'numpy.matrix',
                                    'numpy.chararray',
                                    'numpy.recarray',
                                    'numpy.bool_', 'numpy.void',
                                    'numpy.uint8', 'numpy.uint16',
                                    'numpy.uint32', 'numpy.uint64',
                                    'numpy.int8', 'numpy.int16',
                                    'numpy.int32', 'numpy.int64',
                                    'numpy.float16',
                                    'numpy.float32', 'numpy.float64',
                                    'numpy.complex64',
                                    'numpy.complex128',
                                    'numpy.bytes_', 'numpy.str_',
                                    'numpy.object_')

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
        self.matlab_classes = tuple(self.__MATLAB_classes.values())

        # Update the type lookups.
        self.update_type_lookups()

    def write(self, f, grp, name, data, type_string):
        # Start with an emtpy attributes.
        attributes = dict()
        # If we are doing matlab compatibility and the data type is not
        # one of those that is supported for matlab, skip writing the
        # data or throw an error if appropriate. structured ndarrays and
        # recarrays are compatible if the
        # structured_numpy_ndarray_as_struct option is set.
        if f.options.matlab_compatible \
                and not (data.dtype.type in self.__MATLAB_classes \
                or (data.dtype.fields is not None \
                and f.options.structured_numpy_ndarray_as_struct)):
            if f.options.action_for_matlab_incompatible == 'error':
                raise hdf5storage.exceptions.TypeNotMatlabCompatibleError(
                    'Data type ' + data.dtype.name
                    + ' not supported by MATLAB.')
            elif f.options.action_for_matlab_incompatible == 'discard':
                return None

        # Need to make a set of data that will be stored. It will start
        # out as a copy of data and then be steadily manipulated.

        data_to_store = data

        # recarrays must be converted to structured ndarrays in order
        # for h5py to be able to write them.
        if isinstance(data_to_store, np.core.records.recarray):
            data_to_store = data_to_store.view(np.ndarray)

        # Optionally convert bytes_ strings to UTF-16, if possible (all
        # are in the ASCII character set). This is done by simply
        # converting to uint16's and checking that each one's value is
        # less than 128 (in the ASCII character set). This will require
        # making them at least 1 dimensional. If it fails, they must be
        # stored as is.
        if data.dtype.type == np.bytes_ \
                and f.options.convert_numpy_bytes_to_utf16:
            if data_to_store.nbytes == 0:
                data_to_store = np.uint16([])
            else:
                new_data = np.uint16(np.atleast_1d(
                    data_to_store).view(np.ndarray).view(np.uint8))
                if np.all(new_data < 128):
                    data_to_store = new_data

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
            if f.options.convert_numpy_str_to_utf16:
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
                data_to_store = convert_numpy_str_to_uint32(
                    data_to_store)
            else:
                data_to_store = new_data

        # Convert scalars to arrays if that option is set. For 1d
        # arrays, an option determines whether they become row or column
        # vectors.

        if f.options.make_atleast_2d:
            new_data = np.atleast_2d(data_to_store)
            if len(data_to_store.shape) == 1 \
                    and f.options.oned_as == 'column':
                new_data = new_data.T
            data_to_store = new_data

        # Reverse the dimension order if that option is set.

        if f.options.reverse_dimension_order:
            data_to_store = data_to_store.T

        # Bools need to be converted to uint8 if the option is given.
        if data_to_store.dtype.name == 'bool' \
                and f.options.convert_bools_to_uint8:
            data_to_store = np.uint8(data_to_store)

        # If data is empty, we instead need to store the shape of the
        # array if the appropriate option is set.

        if f.options.store_shape_for_empty and (data.size == 0 \
                or ((data.dtype.type == np.bytes_ \
                or data.dtype.type == np.str_) \
                and data.nbytes == 0)):
            data_to_store = np.uint64(data_to_store.shape)

        # If it is a complex type, then it needs to be encoded to have
        # the proper complex field names.
        if np.iscomplexobj(data_to_store):
            data_to_store = encode_complex(data_to_store,
                                           f.options.complex_names)

        # If we are storing an object type and it isn't empty
        # (data_to_store is still an object), then we must recursively
        # write what each element points to and make an array of the
        # references to them.
        if data_to_store.dtype.name == 'object':
            data_to_store = f.write_object_array(data_to_store)

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
        # be written as a Group instead (dtypes have a useful hasobject
        # method). The same goes for if there is a null inside its
        # dtype.
        #
        # A flag, wrote_as_struct, is set depending on which path is
        # taken, which is then passed onto write_metadata.
        if data_to_store.dtype.fields is not None \
                and h5py.check_dtype(ref=data_to_store.dtype) \
                is not h5py.Reference \
                and not np.iscomplexobj(data) \
                and (f.options.structured_numpy_ndarray_as_struct \
                or (data_to_store.dtype.hasobject \
                or '\\x00' in str(data_to_store.dtype)) \
                or does_dtype_have_a_zero_shape(data_to_store.dtype)):
            wrote_as_struct = True
            # Grab the list of fields and properly escape them.
            field_names = [n for n in data_to_store.dtype.names]
            escaped_field_names = [escape_path(n) for n in field_names]

            # If the group doesn't exist, it needs to be created. If it
            # already exists but is not a group, it needs to be deleted
            # before being created.

            try:
                if not isinstance(grp[name], h5py.Group):
                    del grp[name]
            except:
                pass
            dsetgrp = grp.create_group(name)

            # Write the metadata, and set the MATLAB_class to 'struct'
            # explicitly.
            if f.options.matlab_compatible:
                attributes['MATLAB_class'] = ('value', 'struct')

            # Delete any Datasets/Groups not corresponding to a field
            # name in data if that option is set.

            if f.options.delete_unused_variables:
                for field in set([i for i in dsetgrp]).difference( \
                        set(escaped_field_names)):
                    del dsetgrp[field]

            # Go field by field making an object array (make an empty
            # object array and assign element wise) and write it inside
            # the Group. If it only has a single element, write that
            # single element extracted from it (will be a standard
            # Dataset as opposed to a HDF5 Reference array). The H5PATH
            # attribute needs to be set appropriately, while all other
            # attributes need to be deleted.
            if f.options.matlab_compatible:
                dsetgrpname = dsetgrp.name
            for i, field in enumerate(field_names):
                esc_field = escaped_field_names[i]
                new_data = np.zeros(shape=data_to_store.shape,
                                    dtype='object')
                for index, x in enumerate(data_to_store.flat):
                    new_data.flat[index] = x[field]

                # If we are supposed to reverse dimension order, it has
                # already been done, but write_data expects that it
                # hasn't, so it needs to be reversed again before
                # passing it on.
                if f.options.reverse_dimension_order:
                    new_data = new_data.T

                # If there is only a single element, write it extracted
                # (don't need to use a Reference array in this
                # case). Otherwise, write the whole thing.
                if np.prod(new_data.shape) == 1:
                    field_obj = f.write_data(dsetgrp, esc_field,
                                             new_data.flat[0], None)
                else:
                    field_obj = f.write_data(dsetgrp, esc_field,
                                             new_data, None)

                if field_obj is not None:
                    esc_attrs = dict()
                    if f.options.matlab_compatible:
                        esc_attrs['H5PATH'] = ('string', dsetgrpname)

                    # In the case that we wrote a Reference array (not a
                    # single element), then all other attributes need to
                    # be removed.
                    set_attributes_all(field_obj,
                                       esc_attrs,
                                       np.prod(new_data.shape) != 1)
        else:
            wrote_as_struct = False

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
            if is_scalar and f.options.compress \
                    and data_to_store.nbytes \
                    >= f.options.compress_size_threshold:
                filters['compression'] = \
                    f.options.compression_algorithm
                if filters['compression'] == 'gzip':
                    filters['compression_opts'] = \
                        f.options.gzip_compression_level
                filters['shuffle'] = f.options.shuffle_filter
                filters['fletcher32'] = \
                    f.options.compressed_fletcher32_filter
            else:
                filters['compression'] = None
                filters['shuffle'] = False
                filters['compression_opts'] = None
                if is_scalar:
                    filters['fletcher32'] = \
                        f.options.uncompressed_fletcher32_filter
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
            try:
                dsetgrp = grp[name]
                if not isinstance(dsetgrp, h5py.Dataset) \
                        or dsetgrp.dtype != data_to_store.dtype \
                        or dsetgrp.shape != data_to_store.shape \
                        or dsetgrp.compression \
                        != filters['compression'] \
                        or dsetgrp.shuffle != filters['shuffle'] \
                        or dsetgrp.fletcher32 \
                        != filters['fletcher32'] \
                        or dsetgrp.compression_opts != \
                        filters['compression_opts']:
                    del grp[name]
                    dsetgrp = grp.create_dataset(name,
                                                 data=data_to_store,
                                                 **filters)
                else:
                    dsetgrp[...] = data_to_store
            except:
                dsetgrp = grp.create_dataset(name, data=data_to_store,
                                             **filters)

        # Write the metadata using the inherited function (good enough).
        self.write_metadata(f, dsetgrp, data, type_string,
                            attributes=attributes,
                            wrote_as_struct=wrote_as_struct)
        return dsetgrp

    def write_metadata(self, f, dsetgrp, data, type_string,
                       attributes=None, wrote_as_struct=False):
        # wote_as_struct is used to pass whether data was written like a
        # matlab struct or not. If yes, then the field names must be put
        # in the metadata.

        if attributes is None:
            attributes = dict()
        # Write the underlying numpy type if we are storing python
        # information.

        # If we are storing python information; the shape, underlying
        # numpy type, and its type of container ('scalar', 'ndarray',
        # 'matrix', or 'chararray') need to be stored.

        if f.options.store_python_metadata:
            attributes['Python.Shape'] = ('value', np.uint64(data.shape))

            # Now, in Python 3, the dtype names for bare bytes and
            # unicode strings start with 'bytes' and 'str' respectively,
            # but in Python 2, they start with 'string' and 'unicode'
            # respectively. The Python 2 ones must be converted to the
            # Python 3 ones for writing.
            attributes['Python.numpy.UnderlyingType'] = (
                'string',
                data.dtype.name.replace('string', 'bytes').replace(
                    'unicode', 'str'))
            if self._matrix_type_exists and isinstance(data,
                                                       np.matrix):
                container = 'matrix'
            elif isinstance(data, np.chararray):
                container = 'chararray'
            elif isinstance(data, np.core.records.recarray):
                container = 'recarray'
            elif isinstance(data, np.ndarray):
                container = 'ndarray'
            else:
                container = 'scalar'
            attributes['Python.numpy.Container'] = ('string', container)

        # If it was written like a matlab struct, then we set the
        # 'Python.Fields' and 'MATLAB_fields' Attributes to the field
        # names if we are storing python metadata or doing matlab
        # compatibility and we are storing a structured ndarray as a
        # structure.
        has_obj = data.dtype.hasobject
        has_null = '\\x00' in str(data.dtype)
        if wrote_as_struct or (data.dtype.fields is not None \
                and (f.options.structured_numpy_ndarray_as_struct \
                or (has_obj or has_null) \
                or not all(data.shape) \
                or not all([all(data[n].shape) \
                for n in data.dtype.names]))):
            # Grab the list of fields and escape them.
            field_names = [escape_path(c) for c in data.dtype.names]

            # Write or delete 'Python.Fields' as appropriate.
            if f.options.store_python_metadata:
                attributes['Python.Fields'] = ('string_array',
                                               field_names)

            # If we are making it MATLAB compatible, then we can set the
            # MATLAB_fields Attribute as long as all keys are mappable
            # to ASCII. Otherwise, the attribute should be deleted. It
            # is written as a vlen='S1' array of bytes_ arrays of the
            # individual characters.
            if f.options.matlab_compatible:
                try:
                    dt = h5py.special_dtype(vlen=np.dtype('S1'))
                    fs = np.empty(shape=(len(field_names),), dtype=dt)
                    for i, s in enumerate(field_names):
                        fs[i] = np.array([c.encode('ascii')
                                          for c in s], dtype='S1')
                except UnicodeEncodeError:
                    pass
                else:
                    attributes['MATLAB_fields'] = ('value', fs)

        # If data is empty, we need to set the Python.Empty and
        # MATLAB_empty attributes to 1 if we are storing type info or
        # making it MATLAB compatible. Otherwise, no empty attribute is
        # set and existing ones must be deleted.

        if data.size == 0  or ((data.dtype.type == np.bytes_ \
                or data.dtype.type == np.str_)
                and data.nbytes == 0):
            if f.options.store_python_metadata:
                attributes['Python.Empty'] = ('value',
                                              np.uint8(1))
            if f.options.matlab_compatible:
                attributes['MATLAB_empty'] = ('value',
                                              np.uint8(1))

        # If we are making it MATLAB compatible, the MATLAB_class
        # attribute needs to be set looking up the data type (gotten
        # using np.dtype.type). If it is a string or bool type, then
        # the MATLAB_int_decode attribute must be set to the number of
        # bytes each element takes up (dtype.itemsize unless it is a
        # np.bytes_ in which case it is one). If the dtype has fields
        # and we are writing it as a structure, the class needs to be
        # overriddent to 'struct'. Otherwise, the attributes must be
        # deleted.

        tp = data.dtype.type
        if f.options.matlab_compatible:
            if data.dtype.fields is not None \
                    and f.options.structured_numpy_ndarray_as_struct:
                attributes['MATLAB_class'] = ('string', 'struct')
            elif tp in self.__MATLAB_classes:
                attributes['MATLAB_class'] = ('string',
                                              self.__MATLAB_classes[tp])
                if tp in (np.bytes_, np.str_, np.bool_):
                    if dsetgrp.dtype.type == np.bytes_:
                        attributes['MATLAB_int_decode'] = ('value', 1)
                    else:
                        attributes['MATLAB_int_decode'] = (
                            'value', np.int64(dsetgrp.dtype.itemsize))

        # Now call the parent class's version to do the actual setting
        # of Attributes.
        TypeMarshaller.write_metadata(self, f, dsetgrp, data,
                                      type_string,
                                      attributes=attributes)

    def read(self, f, dsetgrp, attributes):
        dset = dsetgrp

        # Get the different attributes this marshaller uses.

        type_string = convert_attribute_to_string(
            attributes['Python.Type'])
        underlying_type = convert_attribute_to_string(
            attributes['Python.numpy.UnderlyingType'])
        shape = attributes['Python.Shape']
        container = convert_attribute_to_string(
            attributes['Python.numpy.Container'])
        python_empty = attributes['Python.Empty']
        python_fields = convert_attribute_to_string_array(
            attributes['Python.Fields'])

        matlab_class = convert_attribute_to_string(
            attributes['MATLAB_class'])
        matlab_empty = attributes['MATLAB_empty']

        # We can actually read the MATLAB_fields Attribute if it is
        # present.
        matlab_fields = attributes['MATLAB_fields']

        # If it is a Dataset, it can simply be read and then acted upon
        # (if it is an HDF5 Reference array, it will need to be read
        # recursively). If it is a Group, then it is a structured
        # ndarray like object that needs to be read field wise and
        # constructed.
        if isinstance(dset, h5py.Dataset):
            # Read the data.
            data = dset[...]

            # If it is a reference type, then we need to make an object
            # array that is its replicate, but with the objects they are
            # pointing to in their elements instead of just the
            # references.
            if h5py.check_dtype(ref=dset.dtype) is not None:
                data = f.read_object_array(data)
        else:
            # Starting with an empty dict, all that has to be done is
            # iterate through all the Datasets and Groups in dset
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
            for k in dset:
                # Unescape the name.
                unescaped_k = unescape_path(k)
                # We must exclude group_for_references
                if dset[k].name == f.options.group_for_references:
                    continue
                fld = dset[k]
                if isinstance(fld, h5py.Group) \
                        or h5py.check_dtype(ref=fld.dtype) is None \
                        or len(set(fld.attrs) \
                        & ((set(self.python_attributes) \
                        | set(self.matlab_attributes))
                        - set(['H5PATH', 'MATLAB_empty',
                        'Python.Empty']))) != 0:
                    is_multi_element = False
                try:
                    struct_data[unescaped_k] = f.read_data(dset, k)
                except:
                    pass

            if matlab_class == 'struct' and f.options.structs_as_dicts:
                return struct_data

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
                    fields = [unescape_path(k) for k in python_fields]
                else:
                    fields = [unescape_path(k.tobytes().decode())
                              for k in matlab_fields]
                # Now, there may be fields available that were not
                # given, but still should be read. Keys that are not in
                # python_fields need to be added to the list.
                extra_fields = list(set(struct_data)
                                    - set(fields))
                fields.extend(sorted(extra_fields))
            else:
                fields = sorted(struct_data)

            dt_whole = []
            for k in fields:
                # Read the value.
                v = struct_data[k]

                # If any of the elements are not Numpy types or if they
                # don't all have the exact same dtype and shape, then
                # this field will just be an object field.
                if v.size == 0 or type(v.flat[0]) \
                        not in self._numpy_types:
                    dt_whole.append((k, 'object'))
                    continue

                first = v.flat[0]
                dt = first.dtype
                sp = first.shape
                all_same = True
                try:
                    for x in v.flat:
                        if dt != x.dtype or sp != x.shape:
                            all_same = False
                            break
                except:
                    all_same = False

                # If they are all the same, then dt and shape should be
                # used. Otherwise, it has to be object.
                if all_same:
                    dt_whole.append((k, dt, sp))
                else:
                    dt_whole.append((k, 'object'))

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
                        data[k][index] = x

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
                    fields = [unescape_path(k) for k in python_fields]
                else:
                    fields = [k.tobytes().decode()
                              for k in matlab_fields]
                struct_dtype = list()
                for k in fields:
                    struct_dtype.append((k, 'object'))
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
                            underlying_type[len('str'):]) / 32)
                    data = np.zeros(tuple(shape),
                                    dtype='U' + str(nchars))
                elif struct_dtype is not None:
                    data = np.zeros(tuple(shape),
                                    dtype=struct_dtype)
                else:
                    data = np.zeros(tuple(shape),
                                    dtype=underlying_type)
                if matlab_class is not None or \
                        f.options.reverse_dimension_order:
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
                    f.options.reverse_dimension_order:
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
                    data = convert_to_numpy_bytes(
                        data, length=int(underlying_type[5:]) // 8)
            elif underlying_type.startswith('str') \
                    or matlab_class == 'char':
                if underlying_type == 'str':
                    data = np.unicode_('')
                elif underlying_type.startswith('str'):
                    data = convert_to_numpy_str(
                        data, length=int(underlying_type[3:]) // 32)
                else:
                    data = convert_to_numpy_str(data)

            # If the shape of data and the shape attribute are
            # different but give the same number of elements, then data
            # needs to be reshaped.
            if tuple(shape) != data.shape \
                    and np.prod(shape) == np.prod(data.shape):
                data.shape = tuple(shape)

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
                        data = data.flat[0]
                elif underlying_type.startswith('str'):
                    if python_empty == 1:
                        data = np.unicode_('')
                    elif isinstance(data, np.ndarray):
                        data = data.flat[0]
                else:
                    data = data.flat[0]
            elif container == 'ndarray' or (
                    not self._matrix_type_exists
                    and container == 'matrix'):
                data = np.asarray(data)
            elif container == 'chararray':
                data = data.view(np.chararray)
            elif container == 'matrix':
                # We need to ignore deprecation warnings for the matrix
                # type now that it is pending deprecation.
                with warnings.catch_warnings():
                    warnings.simplefilter(
                        'ignore', (PendingDeprecationWarning,
                                   DeprecationWarning))
                    data = np.asmatrix(data)

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
                    data = np.zeros(
                        tuple(np.uint64(data)),
                        dtype=self.__MATLAB_classes_reverse[
                            matlab_class])
                else:
                    dt_whole = list()
                    for k in matlab_fields:
                        uk = unescape_path(k.tobytes())
                        dt_whole.append((uk, 'object'))
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
            # numpy.unicode needs to be done unless it is currently a
            # numpy.bytes_ in which case it will be preserved.
            if matlab_class == 'char':
                if data.dtype.type != np.bytes_:
                    data = convert_to_numpy_str(data)

        # Done adjusting data, so it can be returned.
        return data


class NumpyDtypeMarshaller(NumpyScalarArrayMarshaller):
    def __init__(self):
        NumpyScalarArrayMarshaller.__init__(self)
        self.types = (np.dtype, )
        self.python_type_strings = ('numpy.dtype', )
        # As the parent class already has MATLAB strings handled, there
        # are no MATLAB classes that this marshaller should be used for.
        self.matlab_classes = ()

        # Update the type lookups.
        self.update_type_lookups()

    def write(self, f, grp, name, data, type_string):
        # Pass it to the parent version of this function to write
        # it. The proper type_string needs to be grabbed now as the
        # parent function will have a modified form of data to guess
        # from if not given the right one explicitly.
        #
        # As for the conversion, we just use convert_dtype_to_str to
        # convert it.
        return NumpyScalarArrayMarshaller.write(
            self, f, grp, name,
            np.bytes_(convert_dtype_to_str(data), 'utf-8'),
            'numpy.dtype')

    def read(self, f, dsetgrp, attributes):
        # Use the parent class version to read it and do most of the
        # work, convert to str, evaluate the literal (using
        # ast.literal_eval instead of the dangerous eval), and passing
        # to the constructor of dtype.
        data = convert_to_str(NumpyScalarArrayMarshaller.read(
            self, f, dsetgrp, attributes))
        return np.dtype(ast.literal_eval(data))


class PythonScalarMarshaller(NumpyScalarArrayMarshaller):
    def __init__(self):
        NumpyScalarArrayMarshaller.__init__(self)

        # In Python 3, there is only a single integer type int, which is
        # variable width. In Python 2, there is the fixed width int and
        # the variable width long. Python 2 with the 0.1.x version of
        # this library would save with either, but Python 3 needs to map
        # both to int, which can be done by just putting the type int
        # for its entry in types.
        self.types = [bool, int, int, float, complex]
        self.python_type_strings = ['bool', 'int', 'long', 'float',
                                    'complex']
        # As the parent class already has MATLAB strings handled, there
        # are no MATLAB classes that this marshaller should be used for.
        self.matlab_classes = []

        # Update the type lookups.
        self.update_type_lookups()

    def write(self, f, grp, name, data, type_string):
        # data just needs to be converted to the appropriate numpy
        # type. If it is a Python 3.x int that is too big to fit in a
        # numpy.int64, it is converted to the string representation of
        # the integer and then converted to a numpy.bytes_. If it isn't
        # too big and is a long, it needs to be converted to an int64 or
        # else when it is converted to a numpy.int64, its dtype.type
        # won't be equal to numpy.int64 for some reason (if it is a
        # Python 3.x int, packing it into int does nothing). Otherwise,
        # data is passed through np.array and then access [()] to get
        # the scalar back as a scalar numpy type. After all conversions,
        # it is then passed to the parent version of this function. The
        # proper type_string needs to be grabbed now as the parent
        # function will have a modified form of data to guess from if
        # not given the right one explicitly.
        if type(data) == int:
            try:
                out = np.int64(data)
            except OverflowError:
                out = np.bytes_(data)
        else:
            out = np.array(data)[()]
        return NumpyScalarArrayMarshaller.write(
            self, f, grp, name, out,
            self.get_type_string(data, type_string))

    def read(self, f, dsetgrp, attributes):
        # Use the parent class version to read it and do most of the
        # work.
        data = NumpyScalarArrayMarshaller.read(self, f, dsetgrp,
                                               attributes)

        # The type string determines how to convert it back to a Python
        # type (just look up the entry in types). As it might be
        # returned as an ndarray, we need to use its item method.
        type_string = convert_attribute_to_string(
            attributes['Python.Type'])
        if type_string in self.typestring_to_type:
            tp = self.typestring_to_type[type_string]
            return tp(data.item())
        else:
            # Must be some other type, so return it as is.
            return data


class PythonStringMarshaller(NumpyScalarArrayMarshaller):
    def __init__(self):
        NumpyScalarArrayMarshaller.__init__(self)
        self.types = (str, bytes, bytearray)
        self.python_type_strings = ('str', 'bytes', 'bytearray')
        # As the parent class already has MATLAB strings handled, there
        # are no MATLAB classes that this marshaller should be used for.
        self.matlab_classes = ()

        # Update the type lookups.
        self.update_type_lookups()

    def write(self, f, grp, name, data, type_string):
        # data just needs to be converted to a numpy string of the
        # appropriate type (str to np.str_ and the others to np.bytes_).
        if isinstance(data, str):
            cdata = np.unicode_(data)
        else:
            cdata = np.bytes_(data)

        # Now pass it to the parent version of this function to write
        # it. The proper type_string needs to be grabbed now as the
        # parent function will have a modified form of data to guess
        # from if not given the right one explicitly.
        return NumpyScalarArrayMarshaller.write(
            self, f, grp, name, cdata,
            self.get_type_string(data, type_string))

    def read(self, f, dsetgrp, attributes):
        # Use the parent class version to read it and do most of the
        # work.
        data = NumpyScalarArrayMarshaller.read(self, f, dsetgrp,
                                               attributes)

        # The type string determines how to convert it back to a Python
        # type (just look up the entry in types). Otherwise, return it
        # as is.
        type_string = convert_attribute_to_string(
            attributes['Python.Type'])
        if type_string == 'str':
            return convert_to_str(data)
        elif type_string == 'bytes':
            return bytes(data)
        elif type_string == 'bytearray':
            return bytearray(data)
        else:
            return data


class PythonNoneEllipsisNotImplementedMarshaller(
        NumpyScalarArrayMarshaller):
    def __init__(self):
        NumpyScalarArrayMarshaller.__init__(self)
        self.types = (type(None), type(...), type(NotImplemented))
        self.python_type_strings = ('builtins.NoneType',
                                    'builtins.ellipsis',
                                    'builtins.NotImplementedType')
        # None corresponds to no MATLAB class.
        self.matlab_classes = ()
        # Update the type lookups.
        self.update_type_lookups()

    def write(self, f, grp, name, data, type_string):
        # Just going to use the parent function with an empty double
        # (two dimensional so that MATLAB will import it as a []) as the
        # data and the right type_string set (parent can't guess right
        # from the modified form).
        return NumpyScalarArrayMarshaller.write(
            self, f, grp, name, np.float64([]),
            self.get_type_string(data, type_string))

    def read(self, f, dsetgrp, attributes):
        # The type string can be used to look up the type, which can be
        # called to produce an instance.
        type_string = convert_attribute_to_string(
            attributes['Python.Type'])
        return self.typestring_to_type[type_string]()


class PythonDictMarshaller(TypeMarshaller):
    def __init__(self):
        TypeMarshaller.__init__(self)
        self.python_attributes |= set(('Python.Fields',
                                       'Python.dict.StoredAs',
                                       'Python.dict.keys_values_names',
                                       'Python.dict.key_str_types'))
        self.matlab_attributes |= set(('MATLAB_class', 'MATLAB_fields'))
        self.types = (dict, collections.OrderedDict)

        self.python_type_strings = ('dict', 'collections.OrderedDict')
        self.__MATLAB_classes = {dict: 'struct',
                                 collections.OrderedDict: 'struct'}
        # Set matlab_classes to empty since NumpyScalarArrayMarshaller
        # handles Groups by default now.
        self.matlab_classes = ()
        # Update the type lookups.
        self.update_type_lookups()

    def write(self, f, grp, name, data, type_string):
        # Check to see if any fields are not string like, or if they are
        # string like, if they cannot be converted to unicode and not
        # have characters that can't be handled. If the fields are
        # string like, a list of all of them converted to str along with
        # what they originally were needs to be generated.
        tps = {str: b't',
               bytes: b'b',
               np.unicode_: b'U',
               np.bytes_: b'S'}

        any_non_valid_str_keys = False
        keys_as_str = []
        key_str_types = []
        for field in data:
            if type(field) not in tps:
                any_non_valid_str_keys = True
                break
            try:
                field_str = escape_path(convert_to_str(field))
                keys_as_str.append(field_str)
                key_str_types.append(tps[type(field)])
            except:
                any_non_valid_str_keys = True
                break

        # If the group doesn't exist, it needs to be created. If it
        # already exists but is not a group, it needs to be deleted
        # before being created.

        try:
            grp2 = grp[name]
            if not isinstance(grp[name], h5py.Group):
                del grp[name]
                grp2 = grp.create_group(name)
        except:
            grp2 = grp.create_group(name)

        # Write the metadata.
        self.write_metadata(
            f, grp2, data, type_string,
            any_non_valid_str_keys=any_non_valid_str_keys,
            keys_as_str=keys_as_str,
            key_str_types=b''.join(key_str_types))

        # Set the names (Datasets) and values (Datasets) to store the
        # data in. These will be the individual fields and their names
        # if storing individually. If storing as values and keys, this
        # will be done as the keys and values in bulk as tuples.
        if any_non_valid_str_keys:
            names = (f.options.dict_like_keys_name,
                     f.options.dict_like_values_name)
            values = (tuple(data), tuple(data.values()))
        else:
            names = tuple(keys_as_str)
            values = tuple(data.values())

        # Delete any Datasets/Groups not in names if that option is set
        # or if we are not storing the keys and values individually

        if any_non_valid_str_keys or f.options.delete_unused_variables:
            for field in set([i for i in grp2]).difference(set(names)):
                del grp2[field]

        # Go through all the names and values and write them. The H5PATH
        # needs to be set as the path of grp2 on all of them if we are
        # doing MATLAB compatibility (otherwise, the attribute needs to
        # be deleted).
        if f.options.matlab_compatible:
            grp2name = grp2.name
        for i, k in enumerate(names):
            obj = f.write_data(grp2, k, values[i], None)
            if obj is not None:
                if f.options.matlab_compatible:
                    set_attribute_string(obj, 'H5PATH', grp2name)
                else:
                    del_attribute(obj, 'H5PATH')
        # Done
        return grp2

    def write_metadata(self, f, dsetgrp, data, type_string,
                       attributes=None,
                       any_non_valid_str_keys=None,
                       keys_as_str=None,
                       key_str_types=None):
        if attributes is None:
            attributes = dict()
        # Two keyword arguments were added beyond what the base class
        # requires. These are used to pass whether there were any keys
        # that were valid string types and if they were all valid string
        # types, their type characters.

        # Grab all the keys in whatever order is given (OrderedDict will
        # be in the order they were entered and dict will be sorted).
        fields = tuple(keys_as_str)

        # If we are storing python metadata, we need to set the
        # 'Python.dict.StoredAs' and 'Python.Fields' Attributes
        # appropriately. 'Python.Fields' is only used if the fields are
        # being stored individually.
        if f.options.store_python_metadata:
            if any_non_valid_str_keys is True:
                attributes['Python.dict.StoredAs'] = ('string',
                                                      'keys_values')
                attributes['Python.dict.keys_values_names'] = (
                    'string_array',
                    [f.options.dict_like_keys_name,
                    f.options.dict_like_values_name])
            else:
                attributes['Python.dict.StoredAs'] = ('string',
                                                      'individually')
                attributes['Python.Fields'] = ('string_array', fields)
                attributes['Python.dict.key_str_types'] = (
                    'string', convert_to_str(key_str_types))

        # If we are making it MATLAB compatible, then we can set the
        # MATLAB_fields Attribute as long as all keys are mappable to
        # ASCII. Otherwise, the attribute should be deleted. It is
        # written as a vlen='S1' array of bytes_ arrays of the
        # individual characters.
        if f.options.matlab_compatible \
                and any_non_valid_str_keys is False:
            try:
                dt = h5py.special_dtype(vlen=np.dtype('S1'))
                fs = np.empty(shape=(len(fields),), dtype=dt)
                for i, s in enumerate(fields):
                    fs[i] = np.array([c.encode('ascii') for c in s],
                                     dtype='S1')
            except UnicodeDecodeError:
                pass
            except UnicodeEncodeError:
                pass
            else:
                attributes['MATLAB_fields'] = ('value', fs)

        # If we are making it MATLAB compatible, the MATLAB_class
        # attribute needs to be set for the data type. If the type
        # cannot be found or if we are not doing MATLAB compatibility,
        # the attributes need to be deleted.

        tp = type(data)
        if f.options.matlab_compatible and tp in self.__MATLAB_classes:
            attributes['MATLAB_class'] = ('string',
                                          self.__MATLAB_classes[tp])

        # Now call the parent class's version to do the actual setting
        # of Attributes.
        TypeMarshaller.write_metadata(self, f, dsetgrp, data,
                                      type_string,
                                      attributes=attributes)

    def read(self, f, dsetgrp, attributes):
        grp2 = dsetgrp
        # If name is not present or is not a Group, then we can't read
        # it and have to throw an error.
        if not isinstance(grp2, h5py.Group):
            raise NotImplementedError('Not a Group.')

        # Get the different attributes this marshaller uses.

        type_string = convert_attribute_to_string(
            attributes['Python.Type'])
        python_fields = convert_attribute_to_string_array(
            attributes['Python.Fields'])

        stored_as = convert_attribute_to_string(
            attributes['Python.dict.StoredAs'])
        keys_values_names = convert_attribute_to_string_array(
            attributes['Python.dict.keys_values_names'])
        if keys_values_names is None:
            keys_values_names = (f.options.dict_like_keys_name,
                                 f.options.dict_like_values_name)
        key_str_types = convert_attribute_to_string(
            attributes['Python.dict.key_str_types'])

        # We can actually read the MATLAB_fields Attribute if it is present.
        matlab_fields = attributes['MATLAB_fields']

        # How the dict like is read depends on how it is stored as. The
        # dict like's items will be constructed. If it is stored as
        # keys_values, then it is just a matter of reading them and
        # generating the items directly from them. Otherwise, each field
        # needs to be read individually.
        if stored_as == 'keys_values' \
                and escape_path(keys_values_names[0]) in grp2 \
                and escape_path(keys_values_names[1]) in grp2:
            d = tuple([f.read_data(grp2, escape_path(k))
                       for k in keys_values_names])
            items = zip(*d)
        else:
            # Construct the fields to grab and their proper order
            # (important for OrderedDict) from python_fields,
            # matlab_fields, and then any other Groups in the Group, and
            # in that order with duplicates removed. All field names
            # must be turned into str.
            fields = []
            if python_fields is not None:
                fields.extend(python_fields)
            if matlab_fields is not None:
                for s in [k.tobytes().decode()
                          for k in matlab_fields]:
                    if s not in fields:
                        fields.append(s)
            for k in grp2:
                if k not in fields:
                    fields.append(k)

            # Read the keys and values one by one putting them into
            # items. Since we don't want an exception thrown by reading
            # an element to stop the whole reading process, the reading
            # is wrapped in a try block that just catches exceptions and
            # then does nothing about them (nothing needs to be
            # done). Field names optionally need to be converted to
            # their original string types.
            tp_convert = {'t': lambda x: x,
                          'b':
                          lambda x: bytes(convert_to_numpy_bytes(x)),
                          'S': convert_to_numpy_bytes,
                          'U': convert_to_numpy_str}
            items = []
            for i, k in enumerate(fields):
                try:
                    uk = unescape_path(k)
                    # We must exclude group_for_references
                    if grp2[k].name \
                            == f.options.group_for_references:
                        continue
                    v = f.read_data(grp2, k)

                    # Now, if python_fields and key_str_types are both
                    # present and we haven't gotten past the
                    # python_fields, we need to convert the field name
                    # to the right type of string, specified in
                    # key_str_types.
                    if python_fields is not None \
                            and key_str_types is not None \
                            and i < len(key_str_types) \
                            and len(python_fields) == len(key_str_types):
                        k_conv = tp_convert[key_str_types[i]](uk)
                    else:
                        k_conv = uk
                    items.append((k_conv, v))
                except:
                    pass

        # Construct a dict like from the items. If it is supposed to
        # be an OrderedDict, it should be that. Otherwise, it will be a
        # dict (inheriting classes are responsible for converting it).
        if type_string == 'collections.OrderedDict':
            tp = collections.OrderedDict
        else:
            tp = dict
        return tp(items)


class PythonCounterMarshaller(PythonDictMarshaller):
    def __init__(self):
        PythonDictMarshaller.__init__(self)
        self.types = (collections.Counter, )
        self.python_type_strings = ('collections.Counter', )
        # As the parent class already has MATLAB strings handled, there
        # are no MATLAB classes that this marshaller should be used for.
        self.matlab_classes = ()
        # Update the type lookups.
        self.update_type_lookups()

    def read(self, f, dsetgrp, attributes):
        # Use the parent class version to read it and do most of the
        # work.
        data = PythonDictMarshaller.read(self, f, dsetgrp, attributes)
        # The type string determines how to convert it back to a Python
        # type, which is just passing the data dict into its constructor.
        type_string = convert_attribute_to_string(
            attributes['Python.Type'])
        if type_string in self.typestring_to_type:
            tp = self.typestring_to_type[type_string]
            return tp(data)
        else:
            # Must be some other type, so return it as is.
            return data


class PythonSliceRangeMarshaller(PythonDictMarshaller):
    def __init__(self):
        PythonDictMarshaller.__init__(self)
        self.types = (slice, range)
        self.python_type_strings = ('slice', 'range')
        # As the parent class already has MATLAB strings handled, there
        # are no MATLAB classes that this marshaller should be used for.
        self.matlab_classes = ()
        # Update the type lookups.
        self.update_type_lookups()

    def write(self, f, grp, name, data, type_string):
        # data just needs to be converted to a dict and then pass it to
        # the parent version of this function. The proper type_string
        # needs to be grabbed now as the parent function will have a
        # modified form of data to guess from if not given the right one
        # explicitly.
        return PythonDictMarshaller.write(
            self, f, grp, name,
            {'start': data.start, 'stop': data.stop, 'step': data.step},
            self.get_type_string(data, type_string))

    def read(self, f, dsetgrp, attributes):
        # Use the parent class version to read it and do most of the
        # work.
        data = PythonDictMarshaller.read(self, f, dsetgrp, attributes)
        # The type string determines how to convert it back to a Python
        # type (just look up the entry in types).
        type_string = convert_attribute_to_string(
            attributes['Python.Type'])
        if type_string in self.typestring_to_type:
            tp = self.typestring_to_type[type_string]
            return tp(data['start'], data['stop'], data['step'])
        else:
            # Must be some other type, so return it as is.
            return data


class PythonDatetimeObjsMarshaller(PythonDictMarshaller):
    def __init__(self):
        PythonDictMarshaller.__init__(self)
        # We will not import fractions right away and instead let the
        # rest of the API import it if needed. That way it is not
        # imported unless needed since none of the rest of this package
        # uses it.
        self.types = (datetime.timedelta, datetime.timezone,
                      datetime.date, datetime.time,
                      datetime.datetime)
        self.python_type_strings = ('datetime.timedelta',
                                    'datetime.timezone',
                                    'datetime.date',
                                    'datetime.time',
                                    'datetime.datetime')
        # As the parent class already has MATLAB strings handled, there
        # are no MATLAB classes that this marshaller should be used for.
        self.matlab_classes = ()
        # Update the type lookups.
        self.update_type_lookups()

    def write(self, f, grp, name, data, type_string):
        # data just needs to be converted to a dict and then pass it to
        # the parent version of this function. We build a dict of the
        # keyword arguments to pass to the constructors to rebuild the
        # types. For all but timezone, it is just a matter of reading
        # the right attributes and using their names as the
        # keys. timezone, unfortunately, does not have attributes for
        # the two arguments. While the offset can be gotten reliably,
        # the name cannot (if name is set to None, then calling tzname
        # will cause a name to be generated based on the offset).
        attrs = {datetime.timedelta: ('days', 'seconds',
                                      'microseconds'),
                 datetime.date: ('year', 'month', 'day'),
                 datetime.time: ('hour', 'minute', 'second',
                                 'microsecond', 'tzinfo'),
                 datetime.datetime: ('year', 'month', 'day',
                                     'hour', 'minute', 'second',
                                     'microsecond', 'tzinfo')}
        if type(data) in attrs:
            cdata = {k: getattr(data, k) for k in attrs[type(data)]}
        elif type(data) == datetime.timezone:
            parts = data.__reduce__()[1]
            if len(parts) == 1:
                cdata = {'offset': parts[0]}
            else:
                cdata = {'offset': parts[0],
                         'name': parts[1]}
        return PythonDictMarshaller.write(
            self, f, grp, name, cdata,
            self.get_type_string(data, type_string))

    def read(self, f, dsetgrp, attributes):
        # Use the parent class version to read it and do most of the
        # work to get the dict of the arguments to pass to the
        # constructor.
        data = PythonDictMarshaller.read(self, f, dsetgrp, attributes)
        # The type string determines how to convert it back to a Python
        # type (just look up the entry in types).
        type_string = convert_attribute_to_string(
            attributes['Python.Type'])
        if type_string in self.typestring_to_type:
            tp = self.typestring_to_type[type_string]
            return tp(**data)
        else:
            # Must be some other type, so return it as is.
            return data


class PythonFractionMarshaller(PythonDictMarshaller):
    def __init__(self):
        PythonDictMarshaller.__init__(self)
        # We will not import fractions right away and instead let the
        # rest of the API import it if needed. That way it is not
        # imported unless needed since none of the rest of this package
        # uses it.
        self.required_parent_modules = ('fractions', )
        self.required_modules = ('fractions', )
        self.types = ('fractions.Fraction', )
        self.python_type_strings = ('fractions.Fraction', )
        # As the parent class already has MATLAB strings handled, there
        # are no MATLAB classes that this marshaller should be used for.
        self.matlab_classes = ()
        # Update the type lookups.
        self.update_type_lookups()

    def write(self, f, grp, name, data, type_string):
        # data just needs to be converted to a dict and then pass it to
        # the parent version of this function. The proper type_string
        # needs to be grabbed now as the parent function will have a
        # modified form of data to guess from if not given the right one
        # explicitly.
        return PythonDictMarshaller.write(
            self, f, grp, name,
            {'numerator': data.numerator,
             'denominator': data.denominator},
            self.get_type_string(data, type_string))

    def read(self, f, dsetgrp, attributes):
        # Use the parent class version to read it and do most of the
        # work, and then pass the result through the contructor of
        # Fraction.
        data = PythonDictMarshaller.read(self, f, dsetgrp, attributes)
        return importlib.import_module('fractions').Fraction(**data)

    def read_approximate(self, f, dsetgrp, attributes):
        # Use the parent class version to read it and then there is
        # nothing we can do about it except return it since this is a
        # reasonable approximation.
        return PythonDictMarshaller.read(self, f, dsetgrp, attributes)


class PythonListMarshaller(NumpyScalarArrayMarshaller):
    def __init__(self):
        NumpyScalarArrayMarshaller.__init__(self)
        self.types = (list, )
        self.python_type_strings = ('list', )
        # As the parent class already has MATLAB strings handled, there
        # are no MATLAB classes that this marshaller should be used for.
        self.matlab_classes = ()
        # Update the type lookups.
        self.update_type_lookups()

    def write(self, f, grp, name, data, type_string):
        # data just needs to be converted to the appropriate numpy type
        # (pass it through np.object_ to get the and then pass it to the
        # parent version of this function. The proper type_string needs
        # to be grabbed now as the parent function will have a modified
        # form of data to guess from if not given the right one
        # explicitly.
        out = np.zeros(dtype='object', shape=(len(data), ))
        out[:] = data
        return NumpyScalarArrayMarshaller.write(
            self, f, grp, name, out,
            self.get_type_string(data, type_string))

    def read(self, f, dsetgrp, attributes):
        # Use the parent class version to read it and do most of the
        # work.
        data = NumpyScalarArrayMarshaller.read(self, f, dsetgrp,
                                               attributes)

        # Passing it through list does all the work of making it a list
        # again.
        return list(data)


class PythonTupleSetDequeMarshaller(PythonListMarshaller):
    def __init__(self):
        PythonListMarshaller.__init__(self)
        self.types = (tuple, set, frozenset, collections.deque)
        self.python_type_strings = ('tuple', 'set', 'frozenset',
                                    'collections.deque')
        # As the parent class already has MATLAB strings handled, there
        # are no MATLAB classes that this marshaller should be used for.
        self.matlab_classes = ()
        # Update the type lookups.
        self.update_type_lookups()

    def write(self, f, grp, name, data, type_string):
        # data just needs to be converted to a list and then pass it to
        # the parent version of this function. The proper type_string
        # needs to be grabbed now as the parent function will have a
        # modified form of data to guess from if not given the right one
        # explicitly.
        return PythonListMarshaller.write(
            self, f, grp, name, list(data),
            self.get_type_string(data, type_string))

    def read(self, f, dsetgrp, attributes):
        # Use the parent class version to read it and do most of the
        # work.
        data = PythonListMarshaller.read(self, f, dsetgrp, attributes)

        # The type string determines how to convert it back to a Python
        # type (just look up the entry in types).
        type_string = convert_attribute_to_string(
            attributes['Python.Type'])
        if type_string in self.typestring_to_type:
            tp = self.typestring_to_type[type_string]
            return tp(data)
        else:
            # Must be some other type, so return it as is.
            return data


class PythonChainMapMarshaller(PythonListMarshaller):
    def __init__(self):
        PythonListMarshaller.__init__(self)
        self.types = (collections.ChainMap, )
        self.python_type_strings = ('collections.ChainMap', )
        # As the parent class already has MATLAB strings handled, there
        # are no MATLAB classes that this marshaller should be used for.
        self.matlab_classes = ()
        # Update the type lookups.
        self.update_type_lookups()

    def write(self, f, grp, name, data, type_string):
        # We just pass the maps attribute along. The proper type_string
        # needs to be grabbed now as the parent function will have a
        # modified form of data to guess from if not given the right one
        # explicitly.
        return PythonListMarshaller.write(
            self, f, grp, name, data.maps,
            self.get_type_string(data, type_string))

    def read(self, f, dsetgrp, attributes):
        # Use the parent class version to read it and do most of the
        # work.
        data = PythonListMarshaller.read(self, f, dsetgrp, attributes)

        # Passing it through ChainMap does all the work of making it a
        # ChainMap again.
        return collections.ChainMap(*data)
