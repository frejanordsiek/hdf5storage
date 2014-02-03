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
"""
This is the hdf5storage package, a Python package to read and write
python data types to HDF5 (Heirarchal Data Format) files beyond just
Numpy types.

Version 0.1


Examples
--------

Write and read back a ``dict`` of various types, not storing any type
information or MATLAB metadata.

>>> import numpy as np
>>> a = {'a': 2, 'b': 2.3, 'c': True, 'd': 'abc', 'e': b'defg',
         'f': (1-2.3j), 'g': None, 'h':{'aa': np.uint8(1),
         'bb': np.int16([1, 2, 3]),
         'cc': np.float32([[1, 2, 3, 4],[5, 6, 7, 8.2]]),
         'dd': np.complex128([[1], [2+3j], [0]]),
         'ee': np.bytes_('adfdafa'), 'ff': np.str_('aivne12'),
         'gg': {'123': 1}}}
>>> hdf5storage.write(data=a, name='/', filename='data.h5',
                      store_type_information=False,
                      matlab_compatible=False)
>>> hdf5storage.read(name='/', filename='data.h5')
{'a': array(2),
 'b': array(2.3),
 'c': array(True, dtype=bool),
 'd': array(b'abc',
      dtype='|S3'),
 'e': array(b'defg',
      dtype='|S4'),
 'f': array((1-2.3j)),
 'g': array([], dtype=float64),
 'h': {'aa': array(1, dtype=uint8),
 'bb': array([1, 2, 3], dtype=int16),
 'cc': array([[ 1.        ,  2.        ,  3.        ,  4.        ],
     [ 5.        ,  6.        ,  7.        ,  8.19999981]],
     dtype=float32),
 'dd': array([[ 1.+0.j],
     [ 2.+3.j],
     [ 0.+0.j]]),
 'ee': array(b'adfdafa',
     dtype='|S7'),
 'ff': array([ 97, 105, 118, 110, 101,  49,  50], dtype=uint32),
 'gg': {'123': array(1)}}}

Write and read back the same ``dict`` of various types, but now storing
type information but not MATLAB metadata.

>>> import numpy as np
>>> a = {'a': 2, 'b': 2.3, 'c': True, 'd': 'abc', 'e': b'defg',
         'f': (1-2.3j), 'g': None, 'h':{'aa': np.uint8(1),
         'bb': np.int16([1, 2, 3]),
         'cc': np.float32([[1, 2, 3, 4],[5, 6, 7, 8.2]]),
         'dd': np.complex128([[1], [2+3j], [0]]),
         'ee': np.bytes_('adfdafa'), 'ff': np.str_('aivne12'),
         'gg': {'123': 1}}}
>>> hdf5storage.write(data=a, name='/', filename='data_typeinfo.h5',
                      store_type_information=True,
                      matlab_compatible=False)
>>> hdf5storage.read(name='/', filename='data_typeinfo.h5')
{'a': 2,
 'b': 2.3,
 'c': True,
 'd': 'abc',
 'e': b'defg',
 'f': (1-2.3j),
 'g': None,
 'h': {'aa': 1,
  'bb': array([1, 2, 3], dtype=int16),
  'cc': array([[ 1.        ,  5.        ,  2.        ,  6.        ],
       [ 3.        ,  7.        ,  4.        ,  8.19999981]], dtype=float32),
  'dd': array([[ 1.+0.j],
       [ 2.+3.j],
       [ 0.+0.j]]),
  'ee': b'adfdafa',
  'ff': 'aivne12',
  'gg': {'123': 1}}}

Write and read back the same ``dict`` of various types, but now storing
MATLAB metadata (making it a MAT v7.3 file) but not type information.

>>> import numpy as np
>>> a = {'a': 2, 'b': 2.3, 'c': True, 'd': 'abc', 'e': b'defg',
         'f': (1-2.3j), 'g': None, 'h':{'aa': np.uint8(1),
         'bb': np.int16([1, 2, 3]),
         'cc': np.float32([[1, 2, 3, 4],[5, 6, 7, 8.2]]),
         'dd': np.complex128([[1], [2+3j], [0]]),
         'ee': np.bytes_('adfdafa'), 'ff': np.str_('aivne12'),
         'gg': {'123': 1}}}
>>> hdf5storage.write(data=a, name='/', filename='data.mat',
                      store_type_information=False,
                      matlab_compatible=True)
>>> hdf5storage.read(name='/', filename='data.mat')
{'a': array([[2]]),
 'b': array([[ 2.3]]),
 'c': array([[ True]], dtype=bool),
 'd': 'abc',
 'e': 'defg',
 'f': array([[ 1.-2.3j]]),
 'g': array([], dtype=float64),
 'h': {'aa': array([[1]], dtype=uint8),
  'bb': array([[1, 2, 3]], dtype=int16),
  'cc': array([[ 1.        ,  2.        ,  3.        ,  4.        ],
       [ 5.        ,  6.        ,  7.        ,  8.19999981]], dtype=float32),
  'dd': array([[ 1.+0.j],
       [ 2.+3.j],
       [ 0.+0.j]]),
  'ee': 'adfdafa',
  'ff': 'aivne12',
  'gg': {'123': array([[1]])}}}

Write and read back the same ``dict`` of various types, but now storing
both type information and MATLAB metadata (making it a MAT v7.3 file).

>>> import numpy as np
>>> a = {'a': 2, 'b': 2.3, 'c': True, 'd': 'abc', 'e': b'defg',
         'f': (1-2.3j), 'g': None, 'h':{'aa': np.uint8(1),
         'bb': np.int16([1, 2, 3]),
         'cc': np.float32([[1, 2, 3, 4],[5, 6, 7, 8.2]]),
         'dd': np.complex128([[1], [2+3j], [0]]),
         'ee': np.bytes_('adfdafa'), 'ff': np.str_('aivne12'),
         'gg': {'123': 1}}}
>>> hdf5storage.write(data=a, name='/', filename='data_typeinfo.mat',
                      store_type_information=True,
                      matlab_compatible=True)
>>> hdf5storage.read(name='/', filename='data_typeinfo.mat')
{'a': 2,
 'b': 2.3,
 'c': True,
 'd': 'abc',
 'e': b'defg',
 'f': (1-2.3j),
 'g': None,
 'h': {'aa': 1,
  'bb': array([1, 2, 3], dtype=int16),
  'cc': array([[ 1.        ,  2.        ,  3.        ,  4.        ],
       [ 5.        ,  6.        ,  7.        ,  8.19999981]], dtype=float32),
  'dd': array([[ 1.+0.j],
       [ 2.+3.j],
       [ 0.+0.j]]),
  'ee': b'adfdafa',
  'ff': 'aivne12',
  'gg': {'123': 1}}}

"""

__version__ = "0.1"

import sys
import os
import posixpath
import copy
import inspect
import datetime
import h5py

from . import lowlevel
from hdf5storage.lowlevel import Hdf5storageError, CantReadError
from . import Marshallers


class Options(object):
    """ Set of options governing how data is read/written to/from disk.

    There are many ways that data can be transformed as it is read or
    written from a file, and many attributes can be used to describe the
    data depending on its format. The option with the most effect is the
    `matlab_compatible` option. It makes sure that the file is
    compatible with MATLAB's HDF5 based version 7.3 mat file format. It
    overrides several options to the values in the following table.

    ============================  ====================
    attribute                     value
    ============================  ====================
    delete_unused_variables       ``True``
    convert_scalars_to_arrays     ``True``
    convert_numpy_bytes_to_utf16  ``True``
    convert_numpy_str_to_utf16    ``True``
    convert_bools_to_uint8        ``True``
    reverse_dimension_order       ``True``
    store_shape_for_empty         ``True``
    complex_names                 ``('real', 'imag')``
    group_for_references          ``'/#refs#'``
    ============================  ====================

    In addition to setting these options, a specially formatted block of
    bytes is put at the front of the file so that MATLAB can recognize
    its format.

    Parameters
    ----------
    store_type_information : bool, optional
        See Attributes.
    matlab_compatible : bool, optional
        See Attributes.
    delete_unused_variables:  : bool, optional
        See Attributes.
    convert_scalars_to_arrays : bool, optional
        See Attributes.
    convert_numpy_bytes_to_utf16 : bool, optional
        See Attributes.
    convert_numpy_str_to_utf16 : bool, optional
        See Attributes.
    convert_bools_to_uint8 : bool, optional
        See Attributes.
    reverse_dimension_order : bool, optional
        See Attributes.
    store_shape_for_empty : bool, optional
        See Attributes.
    complex_names : tuple of two str, optional
        See Attributes.
    group_for_references : str, optional
        See Attributes.
    oned_as : str, optional
        See Attributes.
    marshaller_collection : MarshallerCollection, optional
        See Attributes.

    Attributes
    ----------
    store_type_information : bool
    matlab_compatible : bool
    delete_unused_variables : bool
    convert_scalars_to_arrays : bool
    convert_numpy_bytes_to_utf16 : bool
    convert_numpy_str_to_utf16 : bool
    convert_bools_to_uint8 : bool
    reverse_dimension_order : bool
    store_shape_for_empty : bool
    complex_names : tuple of two str
    group_for_references : str
    oned_as : {'row', 'column'}
    scalar_options : dict
        ``h5py.Group.create_dataset`` options for writing scalars.
    array_options : dict
        ``h5py.Group.create_dataset`` options for writing scalars.
    marshaller_collection : MarshallerCollection
        Collection of marshallers to disk.

    """
    def __init__(self, store_type_information=True,
                 matlab_compatible=True,
                 delete_unused_variables=False,
                 convert_scalars_to_arrays=False,
                 convert_numpy_bytes_to_utf16=False,
                 convert_numpy_str_to_utf16=False,
                 convert_bools_to_uint8=False,
                 reverse_dimension_order=False,
                 store_shape_for_empty=False,
                 complex_names=('r', 'i'),
                 group_for_references="/#refs#",
                 oned_as='row',
                 marshaller_collection=None):
        # Set the defaults.

        self._store_type_information = True
        self._delete_unused_variables = False
        self._convert_scalars_to_arrays = False
        self._convert_numpy_bytes_to_utf16 = False
        self._convert_numpy_str_to_utf16 = False
        self._convert_bools_to_uint8 = False
        self._reverse_dimension_order = False
        self._store_shape_for_empty = False
        self._complex_names = ('r', 'i')
        self._group_for_references = "/#refs#"
        self._oned_as = 'row'
        self._matlab_compatible = True

        # Apply all the given options using the setters, making sure to
        # do matlab_compatible last since it will override most of the
        # other ones.

        self.store_type_information = store_type_information
        self.delete_unused_variables = delete_unused_variables
        self.convert_scalars_to_arrays = convert_scalars_to_arrays
        self.convert_numpy_bytes_to_utf16 = convert_numpy_bytes_to_utf16
        self.convert_numpy_str_to_utf16 = convert_numpy_str_to_utf16
        self.convert_bools_to_uint8 = convert_bools_to_uint8
        self.reverse_dimension_order = reverse_dimension_order
        self.store_shape_for_empty = store_shape_for_empty
        self.complex_names = complex_names
        self.group_for_references = group_for_references
        self.oned_as = oned_as
        self.matlab_compatible = matlab_compatible

        # Set the h5py options to use for writing scalars and arrays to
        # blank for now.

        self.scalar_options = {}
        self.array_options = {}

        # Use the given marshaller collection if it was
        # given. Otherwise, use the default.

        #: Collection of marshallers to disk.
        #:
        #: MarshallerCollection
        #:
        #: See Also
        #: --------
        #: MarshallerCollection
        self.marshaller_collection = marshaller_collection
        if not isinstance(marshaller_collection, MarshallerCollection):
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
    def matlab_compatible(self):
        """ Whether or not to make the file compatible with MATLAB.

        bool

        If ``True`` (default), data is written to file in such a way
        that it compatible with MATLAB's version 7.3 mat file format
        which is HDF5 based. Setting it to ``True`` forces other options
        to hold the specific values in the table below.

        ============================  ====================
        attribute                     value
        ============================  ====================
        delete_unused_variables       ``True``
        convert_scalars_to_arrays     ``True``
        convert_numpy_bytes_to_utf16  ``True``
        convert_numpy_str_to_utf16    ``True``
        convert_bools_to_uint8        ``True``
        reverse_dimension_order       ``True``
        store_shape_for_empty         ``True``
        complex_names                 ``('real', 'imag')``
        group_for_references          ``'/#refs#'``
        ============================  ====================

        In addition to setting these options, a specially formatted
        block of bytes is put at the front of the file so that MATLAB
        can recognize its format.

        """
        return self._matlab_compatible

    @matlab_compatible.setter
    def matlab_compatible(self, value):
        # If it is a bool, it can be set. If it is set to true, then
        # several other options need to be set appropriately.
        if isinstance(value, bool):
            self._matlab_compatible = value
            if value:
                self._delete_unused_variables = True
                self._convert_scalars_to_arrays = True
                self._convert_numpy_bytes_to_utf16 = True
                self._convert_numpy_str_to_utf16 = True
                self._convert_bools_to_uint8 = True
                self._reverse_dimension_order = True
                self._store_shape_for_empty = True
                self._complex_names = ('real', 'imag')
                self._group_for_references = "/#refs#"

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
            self._matlab_compatible = False

    @property
    def convert_scalars_to_arrays(self):
        """ Whether or not to convert scalar types to 2D arrays.

        bool

        If ``True`` (defaults to ``False`` unless MATLAB compatibility
        is being done), all scalar types are converted to 2D arrays when
        written to file. ``oned_as`` determines whether 1D arrays are
        turned into row or column vectors.

        Must be ``True`` if doing MATLAB compatibility. MATLAB can only
        import 2D and higher dimensional arrays.

        See Also
        --------
        oned_as

        """
        return self._convert_scalars_to_arrays

    @convert_scalars_to_arrays.setter
    def convert_scalars_to_arrays(self, value):
        # Check that it is a bool, and then set it. If it is false, we
        # are not doing MATLAB compatible formatting.
        if isinstance(value, bool):
            self._convert_scalars_to_arrays = value
        if not self._convert_scalars_to_arrays:
            self._matlab_compatible = False

    @property
    def convert_numpy_bytes_to_utf16(self):
        """ Whether or not to convert numpy.bytes_ to UTF-16.

        bool

        If ``True`` (defaults to ``False`` unless MATLAB compatibility
        is being done), ``numpy.bytes_`` and anything that is converted
        to them (``bytes``, and ``bytearray``) are converted to UTF-16
        before being written to file as ``numpy.uint16``.

        Must be ``True`` if doing MATLAB compatibility. MATLAB uses
        UTF-16 for its strings.

        See Also
        --------
        numpy.bytes_
        convert_numpy_str_to_utf16

        """
        return self._convert_numpy_bytes_to_utf16

    @convert_numpy_bytes_to_utf16.setter
    def convert_numpy_bytes_to_utf16(self, value):
        # Check that it is a bool, and then set it. If it is false, we
        # are not doing MATLAB compatible formatting.
        if isinstance(value, bool):
            self._convert_numpy_bytes_to_utf16 = value
        if not self._convert_numpy_bytes_to_utf16:
            self._matlab_compatible = False

    @property
    def convert_numpy_str_to_utf16(self):
        """ Whether or not to convert numpy.str_ to UTF-16.

        bool

        If ``True`` (defaults to ``False`` unless MATLAB compatibility
        is being done), ``numpy.str_`` and anything that is converted
        to them (``str``) will be converted to UTF-16 if possible before
        being written to file as ``numpy.uint16``. If doing so would
        lead to a loss of data (character can't be translated to
        UTF-16) or would change the shape of an array of ``numpy.str_``
        due to a character being converted into a pair 2-bytes, the
        conversion will not be made and the string will be stored in
        UTF-32 form as a ``numpy.uint32``.

        Must be ``True`` if doing MATLAB compatibility. MATLAB uses
        UTF-16 for its strings.

        See Also
        --------
        numpy.bytes_
        convert_numpy_str_to_utf16

        """
        return self._convert_numpy_str_to_utf16

    @convert_numpy_str_to_utf16.setter
    def convert_numpy_str_to_utf16(self, value):
        # Check that it is a bool, and then set it. If it is false, we
        # are not doing MATLAB compatible formatting.
        if isinstance(value, bool):
            self._convert_numpy_str_to_utf16 = value
        if not self._convert_numpy_str_to_utf16:
            self._matlab_compatible = False

    @property
    def convert_bools_to_uint8(self):
        """ Whether or not to convert bools to ``numpy.uint8``.

        bool

        If ``True`` (defaults to ``False`` unless MATLAB compatibility
        is being done), bool types are converted to ``numpy.uint8``
        before being written to file.

        Must be ``True`` if doing MATLAB compatibility. MATLAB doesn't
        use the enums that ``h5py`` wants to use by default and also
        uses uint8 intead of int8.

        """
        return self._convert_bools_to_uint8

    @convert_bools_to_uint8.setter
    def convert_bools_to_uint8(self, value):
        # Check that it is a bool, and then set it. If it is false, we
        # are not doing MATLAB compatible formatting.
        if isinstance(value, bool):
            self._convert_bools_to_uint8 = value
        if not self._convert_bools_to_uint8:
            self._matlab_compatible = False

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
            self._matlab_compatible = False

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
            self._matlab_compatible = False

    @property
    def complex_names(self):
        """ Names to use for the real and imaginary fields.

        tuple of two str

        ``(r, i)`` where `r` and `i` are two ``str``. When reading and
        writing complex numbers, the real part gets the name in `r` and
        the imaginary part gets the name in `i`. ``h5py`` uses
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
            self._matlab_compatible = False

    @property
    def group_for_references(self):
        """ Path for where to put objects pointed at by references.

        str

        The absolute POSIX path for the Group to place all data that is
        pointed to by another piece of data (needed for
        ``numpy.object_`` and similar types). This path is automatically
        excluded from its parent group when reading back a ``dict``.

        Must be ``'/#refs#`` if doing MATLAB compatibility.

        """
        return self._group_for_references

    @group_for_references.setter
    def group_for_references(self, value):
        # Check that it an str and a valid absolute POSIX path, and then
        # set it. If it is something other than "/#refs#", then we are
        # not doing MATLAB compatible formatting.
        if isinstance(value, str):
            pth = posixpath.normpath(value)
            if len(pth) > 1 and posixpath.isabs(pth):
                self._group_for_references = value
        if self._group_for_references != "/#refs#":
            self._matlab_compatible = False

    @property
    def oned_as(self):
        """ Vector that 1D arrays become when making everything >= 2D.

        {'row', 'column'}

        When the ``convert_scalars_to_arrays`` option is set (set
        implicitly by doing MATLAB compatibility), this option controls
        whether 1D arrays become row vectors or column vectors.

        See Also
        --------
        convert_scalars_to_arrays

        """
        return self._oned_as

    @oned_as.setter
    def oned_as(self, value):
        # Check that it is one of the valid values before setting it.
        if value in ('row', 'column'):
            self._oned_as = value


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
        # the python_type_string from it.

        self._type_strings = {type_string: m for key, m in
                              self._types.items() for type_string in
                              m.python_type_strings}

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
        hdf5storage.Marshallers.TypeMarshaller.python_type_strings

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
        hdf5storage.Marshallers.TypeMarshaller.python_type_strings

        """
        if matlab_class in self._matlab_classes:
            return copy.deepcopy(self._matlab_classes[matlab_class])
        else:
            return None


def write(data, name='/', filename='data.h5', truncate_existing=False,
          truncate_invalid_matlab=False, options=None, **keywords):
    """ Writes data into an HDF5 file (high level).

    High level function to store a Python type (`data`) to a specified
    name (`name`) in an HDF5 file. The name is specified as a POSIX
    style path where the directory name is the Group to put it in and
    the basename is the name to write it to.

    There are various options that can be used to influence how the data
    is written. They can be passed as an already constructed ``Options``
    into `options` or as additional keywords that will be used to make
    one by ``options = Options(**keywords)``.

    Two very important options are ``store_type_information`` and
    ``matlab_compatible``, which are ``bool``. The first makes it so
    that enough metadata (HDF5 Attributes) are written that `data` can
    be read back accurately without it (or its contents if it is a
    container type) ending up different types, transposed in the case of
    numpy arrays, etc. The latter makes it so that the appropriate
    metadata is written, string and bool and complex types are converted
    properly, and numpy arrays are transposed; which is needed to make
    sure that MATLAB can import `data` correctly (the HDF5 header is
    also set so MATLAB will recognize it).

    Parameters
    ----------
    data : any
        The data to write.
    name : str, optional
        The name to write `data` to. Must be a POSIX style path where
         the directory name is the Group to put it in and the basename
         is the name to write it to.
    filename : str, optional
        The name of the HDF5 file to write `data` to.
    truncate_existing : bool, optional
        Whether to truncate the file if it already exists before writing
        to it.
    truncate_invalid_matlab : bool, optional
        Whether to truncate a file if matlab_compatibility is being
        done and the file doesn't have the proper header (userblock in
        HDF5 terms) setup for MATLAB metadata to be placed.
    options : Options, optional
        The options to use when writing. Is mutually exclusive with any
        additional keyword arguments given (set to ``None`` or don't
        provide to use them).
    **keywords :
        If `options` was not provided or was ``None``, these are used as
        arguments to make a ``Options``.

    Raises
    ------
    NotImplementedError
        If writing `data` is not supported.

    See Also
    --------
    read
    Options
    lowlevel.write_data : Low level version

    """
    # Pack the different options into an Options class if an Options was
    # not given.
    if not isinstance(options, Options):
        options = Options(**keywords)

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

    f = None
    try:

        # If the file doesn't already exist or the option is set to
        # truncate it if it does, just open it truncating whatever is
        # there. Otherwise, open it for read/write access without
        # truncating. Now, if we are doing matlab compatibility and it
        # doesn't have a big enough userblock (for metadata for MATLAB
        # to be able to tell it is a valid .mat file) and the
        # truncate_invalid_matlab is set, then it needs to be closed and
        # re-opened with truncation. Whenever we create the file from
        # scratch, even if matlab compatibility isn't being done, a
        # sufficiently sized userblock is going to be allocated
        # (smallest size is 512) for future use (after all, someone
        # might want to turn it to a .mat file later and need it and it
        # is only 512 bytes).

        if truncate_existing or not os.path.isfile(filename):
            f = h5py.File(filename, mode='w', userblock_size=512)
        else:
            f = h5py.File(filename)
            if options.matlab_compatible and truncate_invalid_matlab \
                    and f.userblock_size < 128:
                f.close()
                f = h5py.File(filename, mode='w', userblock_size=512)

        # Need to make sure groupname is a valid group in f and grab its
        # handle to pass on to the low level function.

        if groupname not in f:
            grp = f.require_group(groupname)
        else:
            grp = f[groupname]

        # Hand off to the low level function.
        lowlevel.write_data(f, grp, targetname, data,
                            None, options)
    except:
        print("Unexpected error:", sys.exc_info()[0])
        raise
    finally:
        if isinstance(f, h5py.File):
            userblock_size = f.userblock_size
            f.close()

    # If we are doing MATLAB formatting and there is a sufficiently
    # large userblock, write the new userblock. The same sort of error
    # handling is used.

    if options.matlab_compatible and userblock_size >= 128:
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
            raise
        finally:
            fd.close()


def read(name='/', filename='data.h5',
         options=None, **keywords):
    """ Reads data from an HDF5 file (high level).

    High level function to read data from an HDF5 file located at `name`
    into Python types. The name is specified as a POSIX style path where
    the data to read is located.

    There are various options that can be used to influence how the data
    is read. They can be passed as an already constructed ``Options``
    into `options` or as additional keywords that will be used to make
    one by ``options = Options(**keywords)``.

    Parameters
    ----------
    name : str, optional
        The name to read data from. Must be a POSIX style path where
         the directory name is the Group to put it in and the basename
         is the name to write it to.
    filename : str, optional
        The name of the HDF5 file to read data from.
    options : Options, optional
        The options to use when reading. Is mutually exclusive with any
        additional keyword arguments given (set to ``None`` or don't
        provide to use them).
    **keywords :
        If `options` was not provided or was ``None``, these are used as
        arguments to make a ``Options``.

    Raises
    ------
    CantReadError
        If reading the data can't be done.

    See Also
    --------
    write
    Options
    lowlevel.read_data : Low level version.
    """
    # Pack the different options into an Options class if an Options was
    # not given.
    if not isinstance(options, Options):
        options = Options(**keywords)

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

    # Open the hdf5 file and start reading the data. This is all wrapped
    # in a try block, so that the file can be closed if any errors
    # happen (the error is re-raised).
    try:
        f = None
        f = h5py.File(filename, mode='r')

        # Check that the containing group is in f and is indeed a
        # group. If it isn't an error needs to be thrown.
        if groupname not in f \
                or not isinstance(f[groupname], h5py.Group):
            raise CantReadError('Could not find containing Group '
                                + groupname + '.')

        # Hand off everything to the low level reader.
        data = lowlevel.read_data(f, f[groupname], targetname, options)
    except:
        raise
    finally:
        if f is not None:
            f.close()

    return data
