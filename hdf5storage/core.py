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
""" Module contains the high level read/write interface and code.

"""

import sys
import os
import posixpath
import copy
import inspect
import datetime
import numpy as np
import h5py

from hdf5storage.utilities import *

from hdf5storage.lowlevel import write_data, read_data
from hdf5storage import Marshallers


class Options(object):
    """ Set of options governing how data is read/written to/from disk.

    There are many ways that data can be transformed as it is read or
    written from a file, and many attributes can be used to describe the
    data depending on its format. The option with the most effect is the
    `MATLAB_compatible` option. It makes sure that the file is
    compatible with MATLAB's HDF5 based version 7.3 mat file format. It
    overrides several options to the values in the following table.

    =========================  ====================
    attribute                  value
    =========================  ====================
    delete_unused_variables    ``True``
    convert_scalars_to_arrays  ``True``
    convert_strings_to_utf16   ``True``
    reverse_dimension_order    ``True``
    store_shape_for_empty      ``True``
    complex_names              ``('real', 'imag')``
    =========================  ====================

    In addition to setting these options, a specially formatted block of
    bytes is put at the front of the file so that MATLAB can recognize
    its format.

    Parameters
    ----------
    store_type_information : bool, optional
        See Attributes.
    MATLAB_compatible : bool, optional
        See Attributes.
    delete_unused_variables:  : bool, optional
        See Attributes.
    convert_scalars_to_arrays : bool, optional
        See Attributes.
    convert_strings_to_utf16 : bool, optional
        See Attributes.
    reverse_dimension_order : bool, optional
        See Attributes.
    store_shape_for_empty : bool, optional
        See Attributes.
    complex_names : tuple of two str, optional
        See Attributes.

    Attributes
    ----------
    store_type_information : bool
    MATLAB_compatible : bool
    delete_unused_variables : bool
    convert_scalars_to_arrays : bool
    convert_strings_to_utf16 : bool
    reverse_dimension_order : bool
    store_shape_for_empty : bool
    complex_names : tuple of two str
    scalar_options : dict
        ``h5py.Group.create_dataset`` options for writing scalars.
    array_options : dict
        ``h5py.Group.create_dataset`` options for writing scalars.
    marshaller_collection : MarshallerCollection
        Collection of marshallers to disk.

    """
    def __init__(self, store_type_information=True,
                 MATLAB_compatible=True,
                 delete_unused_variables=False,
                 convert_scalars_to_arrays=False,
                 convert_strings_to_utf16=False,
                 reverse_dimension_order=False,
                 store_shape_for_empty=False,
                 complex_names=('r', 'i')):
        # Set the defaults.

        self._store_type_information = True
        self._delete_unused_variables = False
        self._convert_scalars_to_arrays = False
        self._convert_strings_to_utf16 = False
        self._reverse_dimension_order = False
        self._store_shape_for_empty = False
        self._complex_names = ('r', 'i')
        self._MATLAB_compatible = True

        # Apply all the given options using the setters, making sure to
        # do MATLAB_compatible last since it will override most of the
        # other ones.

        self.store_type_information = store_type_information
        self.delete_unused_variables = delete_unused_variables
        self.convert_scalars_to_arrays = convert_scalars_to_arrays
        self.convert_strings_to_utf16 = convert_strings_to_utf16
        self.reverse_dimension_order = reverse_dimension_order
        self.store_shape_for_empty = store_shape_for_empty
        self.complex_names = complex_names
        self.MATLAB_compatible = MATLAB_compatible

        # Set the h5py options to use for writing scalars and arrays to
        # blank for now.

        self.scalar_options = {}
        self.array_options = {}

        # Use the default collection of marshallers.

        self.marshaller_collection = MarshallerCollection()

    @property
    def store_type_information(self):
        """ Whether or not to store Python type information.

        bool

        If ``True`` (default), information on the Python type for each
        object written to disk is put in its attributes so that it can
        be read back into Python as the same type.

        """
        return self._store_type_information

    @store_type_information.setter
    def store_type_information(self, value):
        # Check that it is a bool, and then set it. This option does not
        # effect MATLAB compatibility
        if isinstance(value, bool):
            self._store_type_information = value

    @property
    def MATLAB_compatible(self):
        """ Whether or not to make the file compatible with MATLAB.

        bool

        If ``True`` (default), data is written to file in such a way
        that it compatible with MATLAB's version 7.3 mat file format
        which is HDF5 based. Setting it to ``True`` forces other options
        to hold the specific values in the table below.

        =========================  ====================
        attribute                  value
        =========================  ====================
        delete_unused_variables    ``True``
        convert_scalars_to_arrays  ``True``
        convert_strings_to_utf16   ``True``
        reverse_dimension_order    ``True``
        store_shape_for_empty      ``True``
        complex_names              ``('real', 'imag')``
        =========================  ====================

        In addition to setting these options, a specially formatted
        block of bytes is put at the front of the file so that MATLAB
        can recognize its format.

        """
        return self._MATLAB_compatible

    @MATLAB_compatible.setter
    def MATLAB_compatible(self, value):
        # If it is a bool, it can be set. If it is set to true, then
        # several other options need to be set appropriately.
        if isinstance(value, bool):
            self._MATLAB_compatible = value
            if value:
                self._delete_unused_variables = True
                self._convert_scalars_to_arrays = True
                self._convert_strings_to_utf16 = True
                self._reverse_dimension_order = True
                self._store_shape_for_empty = True
                self._complex_names = ('real', 'imag')

    @property
    def delete_unused_variables(self):
        """ Whether or not to delete file variables not written to.

        bool

        If ``True`` (defaults to ``False`` unless MATLAB compatibility
        is being done), variables in the file below where writing starts
        that are not written to are deleted.

        Must be ``True`` if doing MATLAB compatibility.

        """
        return self._delete_unused_variables

    @delete_unused_variables.setter
    def delete_unused_variables(self, value):
        # Check that it is a bool, and then set it. If it is false, we
        # are not doing MATLAB compatible formatting.
        if isinstance(value, bool):
            self._delete_unused_variables = value
        if not self._delete_unused_variables:
            self._MATLAB_compatible = False

    @property
    def convert_scalars_to_arrays(self):
        """ Whether or not to convert scalar types to 2D arrays.

        bool

        If ``True`` (defaults to ``False`` unless MATLAB compatibility
        is being done), all scalar types are converted to 2D arrays when
        written to file.

        Must be ``True`` if doing MATLAB compatibility. MATLAB can only
        import 2D and higher dimensional arrays.

        """
        return self._convert_scalars_to_arrays

    @convert_scalars_to_arrays.setter
    def convert_scalars_to_arrays(self, value):
        # Check that it is a bool, and then set it. If it is false, we
        # are not doing MATLAB compatible formatting.
        if isinstance(value, bool):
            self._convert_scalars_to_arrays = value
        if not self._convert_scalars_to_arrays:
            self._MATLAB_compatible = False

    @property
    def convert_strings_to_utf16(self):
        """ Whether or not to convert strings to UTF-16.

        bool

        If ``True`` (defaults to ``False`` unless MATLAB compatibility
        is being done), string types except for ``numpy.str_``
        (``str``, ``bytes``, and ``numpy.string_``) are converted to
        UTF-16 before being written to file.

        Must be ``True`` if doing MATLAB compatibility. MATLAB uses
        UTF-16 for its strings.

        See Also
        --------
        numpy.str_
        numpy.string_

        """
        return self._convert_strings_to_utf16

    @convert_strings_to_utf16.setter
    def convert_strings_to_utf16(self, value):
        # Check that it is a bool, and then set it. If it is false, we
        # are not doing MATLAB compatible formatting.
        if isinstance(value, bool):
            self._convert_strings_to_utf16 = value
        if not self._convert_strings_to_utf16:
            self._MATLAB_compatible = False

    @property
    def reverse_dimension_order(self):
        """ Whether or not to reverse the order of array dimensions.

        bool

        If ``True`` (defaults to ``False`` unless MATLAB compatibility
        is being done), the dimension order of ``numpy.ndarray`` and
        ``numpy.matrix`` are reversed. This switches them from C
        ordering to Fortran ordering. The switch of ordering is
        essentially a transpose.

        Must be ``True`` if doing MATLAB compatibility. MATLAB uses
        Fortran ordering.

        """
        return self._reverse_dimension_order

    @reverse_dimension_order.setter
    def reverse_dimension_order(self, value):
        # Check that it is a bool, and then set it. If it is false, we
        # are not doing MATLAB compatible formatting.
        if isinstance(value, bool):
            self._reverse_dimension_order = value
        if not self._reverse_dimension_order:
            self._MATLAB_compatible = False

    @property
    def store_shape_for_empty(self):
        """ Whether to write the shape if an object has no elements.

        bool

        If ``True`` (defaults to ``False`` unless MATLAB compatibility
        is being done), objects that have no elements (e.g. a
        0x0x2 array) will have their shape (an array of the number of
        elements along each axis) written to disk in place of nothing,
        which would otherwise be written.

        Must be ``True`` if doing MATLAB compatibility. For empty
        arrays, MATLAB requires that the shape array be written in its
        place along with the attribute 'MATLAB_empty' set to 1 to flag
        it.

        """
        return self._store_shape_for_empty

    @store_shape_for_empty.setter
    def store_shape_for_empty(self, value):
        # Check that it is a bool, and then set it. If it is false, we
        # are not doing MATLAB compatible formatting.
        if isinstance(value, bool):
            self._store_shape_for_empty = value
        if not self._store_shape_for_empty:
            self._MATLAB_compatible = False

    @property
    def complex_names(self):
        """ Names to use for the real and imaginary fields.

        tuple of two str

        ``(r, i)`` where `r` and `i` are two ``str``. When reading and
        writing complex numbers, the real part gets the name in `r` and
        the imaginary part gets the name in `i`. :py:mod:`h5py` uses
        ``('r', 'i')`` by default, unless MATLAB compatibility is being
        done in which case its default is ``('real', 'imag')``.

        Must be ``('real', 'imag')`` if doing MATLAB compatibility.

        """
        return self._complex_names

    @complex_names.setter
    def complex_names(self, value):
        # Check that it is a tuple of two strings, and then set it. If
        # it is something other than ('real', 'imag'), then we are not
        # doing MATLAB compatible formatting.
        if isinstance(value, tuple) and len(value) == 2 \
                and isinstance(value[0], str) \
                and isinstance(value[1], str):
            self._complex_names = value
        if self._complex_names != ('real', 'imag'):
            self._MATLAB_compatible = False


class MarshallerCollection(object):
    """ Represents, maintains, and retreives a set of marshallers.

    Maintains a list of marshallers used to marshal data types to and
    from HDF5 files. It includes the builtin marshallers from the
    ``hdf5storage.Marshallers`` module as well as any user supplied or
    added marshallers. While the builtin list cannot be changed; user
    ones can be added or removed. Also has functions to get the
    marshaller appropriate for ``type`` or type_string for a python data
    type.

    User marshallers must provide the same interface as
    ``hdf5storage.Marshallers.TypeMarshaller``, which is probably most
    easily done by inheriting from it.

    Parameters
    ----------
    marshallers : marshaller or list of marshallers, optional
        The user marshaller/s to add to the collection. Could also be a
        ``tuple``, ``set``, or ``frozenset`` of marshallers.

    See Also
    --------
    hdf5storage.Marshallers
    hdf5storage.Marshallers.TypeMarshaller

    """
    def __init__(self, marshallers=[]):
        # Two lists of marshallers need to be maintained: one for the
        # builtin ones in the Marshallers module, and another for user
        # supplied ones.

        # Grab all the marshallers in the Marshallers module (they are
        # the classes) by inspection.
        self._builtin_marshallers = [m() for key, m in dict(
                                     inspect.getmembers(Marshallers,
                                     inspect.isclass)).items()]
        self._user_marshallers = []

        # A list of all the marshallers will be needed along with
        # dictionaries to lookup up the marshaller to use for given
        # types, type string, or MATLAB class string (they are the
        # keys).
        self._marshallers = []
        self._types = dict()
        self._type_strings = dict()
        self._matlab_classes = dict()

        # Add any user given marshallers.
        self.add_marshaller(copy.deepcopy(marshallers))

    def _update_marshallers(self):
        """ Update the full marshaller list and other data structures.

        Makes a full list of both builtin and user marshallers and
        rebuilds internal data structures used for looking up which
        marshaller to use for reading/writing Python objects to/from
        file.

        """
        # Combine both sets of marshallers.
        self._marshallers = self._builtin_marshallers.copy()
        self._marshallers.extend(self._user_marshallers)

        # Construct the dictionary to look up the appropriate marshaller
        # by type.

        self._types = {tp: m for m in self._marshallers for tp in m.types}

        # The equivalent one to read data types given type strings needs
        # to be created from it. Basically, we have to make the key be
        # the cpython_type_string from it.

        self._type_strings = {type_string: m for key, m in
                              self._types.items() for type_string in
                              m.cpython_type_strings}

        # The equivalent one to read data types given MATLAB class
        # strings needs to be created from it. Basically, we have to
        # make the key be the matlab_class from it.

        self._matlab_classes = {matlab_class: m for key, m in
                                self._types.items() for matlab_class in
                                m.matlab_classes}

    def add_marshaller(self, marshallers):
        """ Add a marshaller/s to the user provided list.

        Adds a marshaller or a list of them to the user provided set of
        marshallers.

        Parameters
        ----------
        marshallers : marshaller or list of marshallers
            The user marshaller/s to add to the user provided
            collection. Could also be a ``tuple``, ``set``, or
            ``frozenset`` of marshallers.

        """
        if not isinstance(marshallers, (list, tuple, set, frozenset)):
            marshallers = [marshallers]
        for m in marshallers:
            if m not in self._user_marshallers:
                self._user_marshallers.append(m)
        self._update_marshallers()

    def remove_marshaller(self, marshallers):
        """ Removes a marshaller/s from the user provided list.

        Removes a marshaller or a list of them from the user provided set
        of marshallers.

        Parameters
        ----------
        marshallers : marshaller or list of marshallers
            The user marshaller/s to from the user provided collection.
            Could also be a ``tuple``, ``set``, or ``frozenset`` of
            marshallers.

        """
        if not isinstance(marshallers, (list, tuple, set, frozenset)):
            marshallers = [marshallers]
        for m in marshallers:
            if m in self._user_marshallers:
                self._user_marshallers.remove(m)
        self._update_marshallers()

    def clear_marshallers(self):
        """ Clears the list of user provided marshallers.

        Removes all user provided marshallers, but not the builtin ones
        from the ``hdf5storage.Marshallers`` module, from the list of
        marshallers used.

        """
        self._user_marshallers.clear()
        self._update_marshallers()

    def get_marshaller_for_type(self, tp):
        """ Gets the appropriate marshaller for a type.

        Retrieves the marshaller, if any, that can be used to read/write
        a Python object with type 'tp'.

        Parameters
        ----------
        tp : type
            Python object ``type``.

        Returns
        -------
        marshaller
            The marshaller that can read/write the type to
            file. ``None`` if no appropriate marshaller is found.

        See Also
        --------
        hdf5storage.Marshallers.TypeMarshaller.types

        """
        if tp in self._types:
            return copy.deepcopy(self._types[tp])
        else:
            return None

    def get_marshaller_for_type_string(self, type_string):
        """ Gets the appropriate marshaller for a type string.

        Retrieves the marshaller, if any, that can be used to read/write
        a Python object with the given type string.

        Parameters
        ----------
        type_string : str
            Type string for a Python object.

        Returns
        -------
        marshaller
            The marshaller that can read/write the type to
            file. ``None`` if no appropriate marshaller is found.

        See Also
        --------
        hdf5storage.Marshallers.TypeMarshaller.cpython_type_strings

        """
        if type_string in self._type_strings:
            return copy.deepcopy(self._type_strings[type_string])
        else:
            return None

    def get_marshaller_for_matlab_class(self, matlab_class):
        """ Gets the appropriate marshaller for a MATLAB class string.

        Retrieves the marshaller, if any, that can be used to read/write
        a Python object associated with the given MATLAB class string.

        Parameters
        ----------
        matlab_class : str
            MATLAB class string for a Python object.

        Returns
        -------
        marshaller
            The marshaller that can read/write the type to
            file. ``None`` if no appropriate marshaller is found.

        See Also
        --------
        hdf5storage.Marshallers.TypeMarshaller.cpython_type_strings

        """
        if matlab_class in self._matlab_classes:
            return copy.deepcopy(self._matlab_classes[matlab_class])
        else:
            return None


def write(filename='data.h5', name='/data', data=None,
          store_type_information=True, MATLAB_compatible=True,
          delete_unused_variables=False,
          convert_scalars_to_arrays=False,
          reverse_dimension_order=False,
          convert_strings_to_utf16=False,
          store_shape_for_empty=False,
          complex_names=('r', 'i')):
    # Pack the different options into an Options class. The easiest way
    # to do this is to get all the arguments (locals() gets them since
    # they are the only symbols in the local table at this point) and
    # remove filename, name, and data.

    args = locals().copy()
    del args['filename']
    del args['name']
    del args['data']

    options = Options(**args)

    # Reset the list of MATLAB_fields attributes to set.

    _MATLAB_fields_pairs = []

    # Remove double slashes and a non-root trailing slash.

    name = posixpath.normpath(name)

    # Extract the group name and the target name (will be a dataset if
    # data can be mapped to it, but will end up being made into a group
    # otherwise. As HDF5 files use posix path, conventions, posixpath
    # will do everything.
    groupname = posixpath.dirname(name)
    targetname = posixpath.basename(name)

    # If groupname got turned into blank, then it is just root.
    if groupname == '':
        groupname = '/'

    # If targetname got turned blank, then it is the current directory.
    if targetname == '':
        targetname = '.'

    # Open the hdf5 file and start writing the data (and making the
    # group groupname at the same time if it doesn't exist). This is all
    # wrapped in a try block, so that the file can be closed if any
    # errors happen (the error is re-raised).

    try:

        # If the file already exists, we just open it. If it doesn't
        # exist yet and we are doing any MATLAB formatting, we need to
        # allocate a 512 byte user block (need metadata for MATLAB to
        # tell it is a valid .mat file). The user_block size is also
        # grabbed right before closing, so that if there is a userblock
        # and we are doing MATLAB formatting, we know to set it.

        if os.path.isfile(filename) or not options.MATLAB_compatible:
            f = h5py.File(filename)
        else:
            f = h5py.File(filename, mode='w', userblock_size=512)

        if groupname not in f:
            grp = f.require_group(groupname)
        else:
            grp = f[groupname]

        write_data(f, grp, targetname, data,
                   None, options)
    except:
        print("Unexpected error:", sys.exc_info()[0])
        raise
    finally:
        userblock_size = f.userblock_size
        f.close()

    # If we are doing MATLAB formatting and there is a sufficiently
    # large userblock, write the new userblock. The same sort of error
    # handling is used.

    if options.MATLAB_compatible and userblock_size >= 128:
        # Get the time.
        now = datetime.datetime.now()

        # Construct the leading string. The MATLAB one looks like
        #
        # s = 'MATLAB 7.3 MAT-file, Platform: GLNXA64, Created on: ' \
        #     + now.strftime('%a %b %d %H:%M:%S %Y') \
        #     + ' HDF5 schema 1.00 .'
        #
        # Platform is going to be changed to CPython version

        v = sys.version_info

        s = 'MATLAB 7.3 MAT-file, Platform: CPython ' \
            + '{0}.{1}.{2}'.format(v.major, v.minor, v.micro) \
            + ', Created on: ' \
            + now.strftime('%a %b %d %H:%M:%S %Y') \
            + ' HDF5 schema 1.00 .'

        # Make the bytearray while padding with spaces up to 128-12
        # (the minus 12 is there since the last 12 bytes are special.

        b = bytearray(s + (128-12-len(s))*' ', encoding='utf-8')

        # Add 8 nulls (0) and the magic number (or something) that
        # MATLAB uses.

        b.extend(bytearray.fromhex('00000000 00000000 0002494D'))

        # Now, write it to the beginning of the file.

        try:
            fd = open(filename, 'r+b')
            fd.write(b)
        except:
            print("Unexpected error:", sys.exc_info()[0])
            raise
        finally:
            fd.close()


# Set an empty list of path-string_array pairs to set the
# MATLAB_fields attributes on all the things that correspond to MATLAB
# structures.

_MATLAB_fields_pairs = []
