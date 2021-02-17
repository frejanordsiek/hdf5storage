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

""" Module to read and write python types to/from HDF5.

This is the hdf5storage package, a Python package to read and write
python data types to HDF5 (Heirarchal Data Format) files beyond just
Numpy types.

Version 0.2

"""

__version__ = "0.2"

import collections.abc
import copy
import datetime
import importlib
import inspect
import itertools
import os
import pkgutil
import posixpath
import sys
import threading

import h5py

from . import pathesc
from . import plugins
from . import utilities
from . import Marshallers


class Options(object):
    """ Set of options governing how data is read/written to/from disk.

    There are many ways that data can be transformed as it is read or
    written from a file, and many attributes can be used to describe the
    data depending on its format. The option with the most effect is the
    `matlab_compatible` option. It makes sure that the file is
    compatible with MATLAB's HDF5 based version 7.3 mat file format. It
    overrides several options to the values in the following table.

    ==================================  ====================
    attribute                           value
    ==================================  ====================
    delete_unused_variables             ``True``
    structured_numpy_ndarray_as_struct  ``True``
    make_atleast_2d                     ``True``
    convert_numpy_bytes_to_utf16        ``True``
    convert_numpy_str_to_utf16          ``True``
    convert_bools_to_uint8              ``True``
    reverse_dimension_order             ``True``
    store_shape_for_empty               ``True``
    complex_names                       ``('real', 'imag')``
    group_for_references                ``'/#refs#'``
    compression_algorithm               ``'gzip'``
    ==================================  ====================

    In addition to setting these options, a specially formatted block of
    bytes is put at the front of the file so that MATLAB can recognize
    its format.

    Parameters
    ----------
    store_python_metadata : bool, optional
        See Attributes.
    matlab_compatible : bool, optional
        See Attributes.
    action_for_matlab_incompatible : str, optional
        See Attributes. Only valid values are 'ignore', 'discard', and
        'error'.
    delete_unused_variables : bool, optional
        See Attributes.
    structured_numpy_ndarray_as_struct : bool, optional
        See Attributes.
    make_atleast_2d : bool, optional
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
    dict_like_keys_name : str, optional
        See Attributes.
    dict_like_values_name : str, optional
        See Attributes.
    compress : bool, optional
        See Attributes.
    compress_size_threshold : int, optional
        See Attributes.
    compression_algorithm : str, optional
        See Attributes.
    gzip_compression_level : int, optional
        See Attributes.
    shuffle_filter : bool, optional
        See Attributes.
    compressed_fletcher32_filter : bool, optional
        See Attributes.
    uncompressed_fletcher32_filter : bool, optional
        See Attributes.
    marshaller_collection : MarshallerCollection, optional
        See Attributes.
    **keywords :
        Additional keyword arguments. They are ignored. They are allowed
        to be given to be more compatible with future versions of this
        package where more options will be added.

    Attributes
    ----------
    store_python_metadata : bool
    matlab_compatible : bool
    action_for_matlab_incompatible : str
    delete_unused_variables : bool
    structured_numpy_ndarray_as_struct : bool
    make_atleast_2d : bool
    convert_numpy_bytes_to_utf16 : bool
    convert_numpy_str_to_utf16 : bool
    convert_bools_to_uint8 : bool
    reverse_dimension_order : bool
    store_shape_for_empty : bool
    complex_names : tuple of two str
    group_for_references : str
    oned_as : {'row', 'column'}
    dict_like_keys_name : str
    dict_like_values_name : str
    compress : bool
    compress_size_threshold : int
    compression_algorithm : {'gzip', 'lzf', 'szip'}
    gzip_compression_level : int
    shuffle_filter : bool
    compressed_fletcher32_filter : bool
    uncompressed_fletcher32_filter : bool
    marshaller_collection : MarshallerCollection
        Collection of marshallers to disk.

    """
    def __init__(self, store_python_metadata=True,
                 matlab_compatible=True,
                 action_for_matlab_incompatible='error',
                 delete_unused_variables=False,
                 structured_numpy_ndarray_as_struct=False,
                 make_atleast_2d=False,
                 convert_numpy_bytes_to_utf16=False,
                 convert_numpy_str_to_utf16=False,
                 convert_bools_to_uint8=False,
                 reverse_dimension_order=False,
                 structs_as_dicts=False,
                 store_shape_for_empty=False,
                 complex_names=('r', 'i'),
                 group_for_references="/#refs#",
                 oned_as='row',
                 dict_like_keys_name='keys',
                 dict_like_values_name='values',
                 compress=True,
                 compress_size_threshold=16*1024,
                 compression_algorithm='gzip',
                 gzip_compression_level=7,
                 shuffle_filter=True,
                 compressed_fletcher32_filter=True,
                 uncompressed_fletcher32_filter=False,
                 marshaller_collection=None,
                 **keywords):
        # Set the defaults.

        self._store_python_metadata = True
        self._action_for_matlab_incompatible = 'error'
        self._delete_unused_variables = False
        self._structured_numpy_ndarray_as_struct = False
        self._make_atleast_2d = False
        self._convert_numpy_bytes_to_utf16 = False
        self._convert_numpy_str_to_utf16 = False
        self._convert_bools_to_uint8 = False
        self._reverse_dimension_order = False
        self._structs_as_dicts = False
        self._store_shape_for_empty = False
        self._complex_names = ('r', 'i')
        self._group_for_references = "/#refs#"
        self._oned_as = 'row'
        self._dict_like_keys_name = 'keys'
        self._dict_like_values_name = 'values'
        self._compress = True
        self._compress_size_threshold = 16*1024
        self._compression_algorithm = 'gzip'
        self._gzip_compression_level = 7
        self._shuffle_filter = True
        self._compressed_fletcher32_filter = True
        self._uncompressed_fletcher32_filter = False
        self._matlab_compatible = True

        # Apply all the given options using the setters, making sure to
        # do matlab_compatible last since it will override most of the
        # other ones.

        self.store_python_metadata = store_python_metadata
        self.action_for_matlab_incompatible = \
            action_for_matlab_incompatible
        self.delete_unused_variables = delete_unused_variables
        self.structured_numpy_ndarray_as_struct = \
            structured_numpy_ndarray_as_struct
        self.make_atleast_2d = make_atleast_2d
        self.convert_numpy_bytes_to_utf16 = convert_numpy_bytes_to_utf16
        self.convert_numpy_str_to_utf16 = convert_numpy_str_to_utf16
        self.convert_bools_to_uint8 = convert_bools_to_uint8
        self.reverse_dimension_order = reverse_dimension_order
        self.structs_as_dicts = structs_as_dicts
        self.store_shape_for_empty = store_shape_for_empty
        self.complex_names = complex_names
        self.group_for_references = group_for_references
        self.oned_as = oned_as
        self.dict_like_keys_name = dict_like_keys_name
        self.dict_like_values_name = dict_like_values_name
        self.compress = compress
        self.compress_size_threshold = compress_size_threshold
        self.compression_algorithm = compression_algorithm
        self.gzip_compression_level = gzip_compression_level
        self.shuffle_filter = shuffle_filter
        self.compressed_fletcher32_filter = compressed_fletcher32_filter
        self.uncompressed_fletcher32_filter = \
            uncompressed_fletcher32_filter
        self.matlab_compatible = matlab_compatible

        # Use the given marshaller collection if it was
        # given. Otherwise, use the default.
        if isinstance(marshaller_collection, MarshallerCollection):
            self._marshaller_collection = marshaller_collection
        else:
            self._marshaller_collection = \
                get_default_MarshallerCollection()

    @property
    def marshaller_collection(self):
        """ The MarshallerCollection to use.

        MarshallerCollection

        The ``MarshallerCollection`` (collection of marshallers to disk)
        to use. The default is to use the default one from
        ``get_default_MarshallerCollection``.

        Warning
        -------
        This property does **NOT** return a copy.

        See Also
        --------
        MarshallerCollection
        get_default_MarshallerCollection
        make_new_default_MarshallerCollection

        """
        return self._marshaller_collection

    @marshaller_collection.setter
    def marshaller_collection(self, value):
        # Check that it is a MarshallerCollection, and then set it. This
        # option does not effect MATLAB compatibility
        if isinstance(value, MarshallerCollection):
            self._marshaller_collection = value


    @property
    def store_python_metadata(self):
        """ Whether or not to store Python metadata.

        bool

        If ``True`` (default), information on the Python type for each
        object written to disk is put in its attributes so that it can
        be read back into Python as the same type.

        """
        return self._store_python_metadata

    @store_python_metadata.setter
    def store_python_metadata(self, value):
        # Check that it is a bool, and then set it. This option does not
        # effect MATLAB compatibility
        if isinstance(value, bool):
            self._store_python_metadata = value

    @property
    def matlab_compatible(self):
        """ Whether or not to make the file compatible with MATLAB.

        bool

        If ``True`` (default), data is written to file in such a way
        that it compatible with MATLAB's version 7.3 mat file format
        which is HDF5 based. Setting it to ``True`` forces other options
        to hold the specific values in the table below.

        ==================================  ====================
        attribute                           value
        ==================================  ====================
        delete_unused_variables             ``True``
        structured_numpy_ndarray_as_struct  ``True``
        make_atleast_2d                     ``True``
        convert_numpy_bytes_to_utf16        ``True``
        convert_numpy_str_to_utf16          ``True``
        convert_bools_to_uint8              ``True``
        reverse_dimension_order             ``True``
        store_shape_for_empty               ``True``
        complex_names                       ``('real', 'imag')``
        group_for_references                ``'/#refs#'``
        compression_algorithm               ``'gzip'``
        ==================================  ====================

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
                self._structured_numpy_ndarray_as_struct = True
                self._make_atleast_2d = True
                self._convert_numpy_bytes_to_utf16 = True
                self._convert_numpy_str_to_utf16 = True
                self._convert_bools_to_uint8 = True
                self._reverse_dimension_order = True
                self._store_shape_for_empty = True
                self._complex_names = ('real', 'imag')
                self._group_for_references = "/#refs#"
                self._compression_algorithm = 'gzip'

    @property
    def action_for_matlab_incompatible(self):
        """ The action to do when writing non-MATLAB compatible data.

        {'ignore', 'discard', 'error'}

        The action to perform when doing MATLAB compatibility but a type
        being written is not MATLAB compatible. The actions are to write
        the data anyways ('ignore'), don't write the incompatible data
        ('discard'), or throw a ``TypeNotMatlabCompatibleError``
        exception. The default is 'error'.

        See Also
        --------
        matlab_compatible
        exceptions.TypeNotMatlabCompatibleError

        """
        return self._action_for_matlab_incompatible

    @action_for_matlab_incompatible.setter
    def action_for_matlab_incompatible(self, value):
        # Check that it is one of the allowed values, and then set
        # it. This option does not effect MATLAB compatibility.
        if value in ('ignore', 'discard', 'error'):
            self._action_for_matlab_incompatible = value

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
    def structured_numpy_ndarray_as_struct(self):
        """ Whether or not to convert structured ndarrays to structs.

        bool

        If ``True`` (defaults to ``False`` unless MATLAB compatibility
        is being done), all ``numpy.ndarray`` with fields (compound
        dtypes) are written as HDF5 Groups with the fields as Datasets
        (correspond to struct arrays in MATLAB).

        Must be ``True`` if doing MATLAB compatibility. MATLAB cannot
        handle the compound types made by writing these types.

        """
        return self._structured_numpy_ndarray_as_struct

    @structured_numpy_ndarray_as_struct.setter
    def structured_numpy_ndarray_as_struct(self, value):
        # Check that it is a bool, and then set it. If it is false, we
        # are not doing MATLAB compatible formatting.
        if isinstance(value, bool):
            self._structured_numpy_ndarray_as_struct = value
        if not self._structured_numpy_ndarray_as_struct:
            self._matlab_compatible = False

    @property
    def make_atleast_2d(self):
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
        return self._make_atleast_2d

    @make_atleast_2d.setter
    def make_atleast_2d(self, value):
        # Check that it is a bool, and then set it. If it is false, we
        # are not doing MATLAB compatible formatting.
        if isinstance(value, bool):
            self._make_atleast_2d = value
        if not self._make_atleast_2d:
            self._matlab_compatible = False

    @property
    def convert_numpy_bytes_to_utf16(self):
        """ Whether or not to convert ``numpy.bytes_`` to UTF-16.

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
        """ Whether or not to convert ``numpy.unicode_`` to UTF-16.

        bool

        If ``True`` (defaults to ``False`` unless MATLAB compatibility
        is being done), ``numpy.unicode_`` and anything that is
        converted to them (``str``) will be converted to UTF-16 if
        possible before being written to file as ``numpy.uint16``. If
        doing so would lead to a loss of data (character can't be
        translated to UTF-16) or would change the shape of an array of
        ``numpy.unicode_`` due to a character being converted into a
        pair of 2-bytes, the conversion will not be made and the string
        will be stored in UTF-32 form as a ``numpy.uint32``.

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
    def structs_as_dicts(self):
        """ Whether Matlab structs should be read as dicts.

        bool

        Setting this to ``True`` can be helpful if your structures contain
        very large arrays such that their dtypes, if converted to
        ``np.ndarray``, would exceed the 2GB maximum allowed by
        `NumPy <https://github.com/numpy/numpy/issues/6235>`_.

        """
        return self._structs_as_dicts

    @structs_as_dicts.setter
    def structs_as_dicts(self, value):
        if isinstance(value, bool):
            self._structs_as_dicts = value

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

        Must already be escaped.

        See Also
        --------
        pathesc.escape_path

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

        When the ``make_atleast_2d`` option is set (set implicitly by
        doing MATLAB compatibility), this option controls whether 1D
        arrays become row vectors or column vectors.

        See Also
        --------
        make_atleast_2d

        """
        return self._oned_as

    @oned_as.setter
    def oned_as(self, value):
        # Check that it is one of the valid values before setting it.
        if value in ('row', 'column'):
            self._oned_as = value

    @property
    def dict_like_keys_name(self):
        """ The Dataset name for the keys of dict like objects.

        str

        When a ``dict`` like object has at least one key that isn't an
        ``str`` or is an ``str`` with invalid characters, the objects
        are stored as an array of keys and an array of values. This
        option sets the name of the Dataset for the keys.

        .. versionadded:: 0.2

        See Also
        --------
        dict_like_values_name

        """
        return self._dict_like_keys_name

    @dict_like_keys_name.setter
    def dict_like_keys_name(self, value):
        # Check that it is an str before setting it.
        if isinstance(value, str):
            self._dict_like_keys_name = value

    @property
    def dict_like_values_name(self):
        """ The Dataset name for the values of dict like objects.

        str

        When a ``dict`` like object has at least one key that isn't an
        ``str`` or is an ``str`` with invalid characters, the objects
        are stored as an array of keys and an array of values. This
        option sets the name of the Dataset for the values.

        .. versionadded:: 0.2

        See Also
        --------
        dict_like_keys_name

        """
        return self._dict_like_values_name

    @dict_like_values_name.setter
    def dict_like_values_name(self, value):
        # Check that it is an str before setting it.
        if isinstance(value, str):
            self._dict_like_values_name = value

    @property
    def compress(self):
        """ Whether to compress large python objects (datasets).

        bool

        If ``True``, python objects (datasets) larger than
        ``compress_size_threshold`` will be compressed.

        See Also
        --------
        compress_size_threshold
        compression_algorithm
        shuffle_filter
        compressed_fletcher32_filter

        """
        return self._compress

    @compress.setter
    def compress(self, value):
        # Check that it is a bool, and then set it.
        if isinstance(value, bool):
            self._compress = value

    @property
    def compress_size_threshold(self):
        """ Minimum size of a python object before it is compressed.

        int

        Minimum size in bytes a python object must be for it to be
        compressed if ``compress`` is set. Must be non-negative.

        See Also
        --------
        compress

        """
        return self._compress_size_threshold

    @compress_size_threshold.setter
    def compress_size_threshold(self, value):
        # Check that it is a non-negative integer, and then set it.
        if isinstance(value, int) and value >= 0:
            self._compress_size_threshold = value

    @property
    def compression_algorithm(self):
        """ Algorithm to use for compression.

        {'gzip', 'lzf', 'szip'}

        Compression algorithm to use When the ``compress`` option is set
        and a python object is larger than ``compress_size_threshold``.
        ``'gzip'`` is the only MATLAB compatible option.

        ``'gzip'`` is also known as the Deflate algorithm, which is the
        default compression algorithm of ZIP files and is a common
        compression algorithm used on tarballs. It is the most
        compatible option. It has good compression and is reasonably
        fast. Its compression level is set with the
        ``gzip_compression_level`` option, which is an integer between 0
        and 9 inclusive.

        ``'lzf'`` is a very fast but low to moderate compression
        algorithm. It is less commonly used than gzip/Deflate, but
        doesn't have any patent or license issues.

        ``'szip'`` is a compression algorithm that has some patents and
        license restrictions. It is not always available.

        See Also
        --------
        compress
        compress_size_threshold
        h5py.Group.create_dataset
        http://www.hdfgroup.org/doc_resource/SZIP/Commercial_szip.html

        """
        return self._compression_algorithm

    @compression_algorithm.setter
    def compression_algorithm(self, value):
        # Check that it is one of the valid values before setting it. If
        # it is something other than 'gzip', then we are not doing
        # MATLAB compatible formatting.
        if value in ('gzip', 'lzf', 'szip'):
            self._compression_algorithm = value
        if self._compression_algorithm != 'gzip':
            self._matlab_compatible = False

    @property
    def gzip_compression_level(self):
        """ The compression level to use when doing the gzip algorithm.

        int

        Compression level to use when data is being compressed with the
        ``'gzip'`` algorithm. Must be an integer between 0 and 9
        inclusive. Lower values are faster while higher values give
        better compression.

        See Also
        --------
        compress
        compression_algorithm

        """
        return self._gzip_compression_level

    @gzip_compression_level.setter
    def gzip_compression_level(self, value):
        # Check that it is an integer between 0 and 9.
        if isinstance(value, int) and value >= 0 and value <= 9:
            self._gzip_compression_level = value

    @property
    def shuffle_filter(self):
        """ Whether to use the shuffle filter on compressed python objects.

        bool

        If ``True``, python objects (datasets) that are compressed are
        run through the shuffle filter, which reversibly rearranges the
        data to improve compression.

        See Also
        --------
        compress
        h5py.Group.create_dataset

        """
        return self._shuffle_filter

    @shuffle_filter.setter
    def shuffle_filter(self, value):
        # Check that it is a bool, and then set it.
        if isinstance(value, bool):
            self._shuffle_filter = value

    @property
    def compressed_fletcher32_filter(self):
        """ Whether to use the fletcher32 filter on compressed python objects.

        bool

        If ``True``, python objects (datasets) that are compressed are
        run through the fletcher32 filter, which stores a checksum with
        each chunk so that data corruption can be more easily detected.

        See Also
        --------
        compress
        shuffle_filter
        uncompressed_flether32_filter
        h5py.Group.create_dataset

        """
        return self._compressed_fletcher32_filter

    @compressed_fletcher32_filter.setter
    def compressed_fletcher32_filter(self, value):
        # Check that it is a bool, and then set it.
        if isinstance(value, bool):
            self._compressed_fletcher32_filter = value

    @property
    def uncompressed_fletcher32_filter(self):
        """ Whether to use the fletcher32 filter on uncompressed non-scalar python objects.

        bool

        If ``True``, python objects (datasets) that are **NOT**
        compressed and are not scalars (when converted to a Numpy type,
        their shape is not an empty ``tuple``) are run through the
        fletcher32 filter, which stores a checksum with each chunk so
        that data corruption can be more easily detected. This forces
        all uncompressed data to be chuncked regardless of how small and
        can increase file sizes.

        See Also
        --------
        compress
        shuffle_filter
        compressed_flether32_filter
        h5py.Group.create_dataset

        """
        return self._uncompressed_fletcher32_filter

    @uncompressed_fletcher32_filter.setter
    def uncompressed_fletcher32_filter(self, value):
        # Check that it is a bool, and then set it.
        if isinstance(value, bool):
            self._uncompressed_fletcher32_filter = value


class MarshallerCollection(object):
    """ Represents, maintains, and retreives a set of marshallers.

    Maintains a list of marshallers used to marshal data types to and
    from HDF5 files. It includes the builtin marshallers from the
    ``hdf5storage.Marshallers`` module, optionally any marshallers from
    installed third party plugins, as well as any user supplied or
    added marshallers. While the builtin list cannot be changed; user
    ones can be added or removed. Also has functions to get the
    marshaller appropriate for the ``type`` or type_string for a python
    data type.

    User marshallers must inherit from
    ``hdf5storage.Marshallers.TypeMarshaller`` and provide its
    interface.

    The priority with which marshallers are chosen (builtin, plugin, or
    user) can be set using the `priority` option. Within marshallers
    from third party plugins, those supporting the higher Marshaller API
    versions take priority over those supporting lower versions.

    .. versionchanged:: 0.2
       All marshallers must now inherit from
       ``hdf5storage.Marshallers.TypeMarshaller``.

    .. versionadded:: 0.2
       Marshallers can be loaded from third party plugins that declare
       the ``'hdf5storage.marshallers.plugins'`` entry point.

    .. versionchanged:: 0.2
       The order of marshaller priority (builtin, plugin, or user) can
       be changed. The default is now builtin, plugin, user whereas
       previously the default was user, builtin.

    Parameters
    ----------
    load_plugins : bool, optional
        Whether to load marshallers from the third party plugins or
        not. Default is ``False``.
    lazy_loading : bool, optional
        Whether to attempt to load the required modules for each
        marshaller right away when added/given or to only do so when
        required (when marshaller is needed). Default is ``True``.
    priority : Sequence, optional
        3-element Sequence specifying the priority ordering (first has
        highest priority). The three elements must be ``'builtin'`` for
        the builtin marshallers included in this package, ``'plugin'``
        for marshallers provided by other python packages via plugin,
        and ``'user'`` for marshallers provided to this class
        explicityly during creation. The default priority order is
        builtin, plugin, user.
    marshallers : marshaller or Iterable of marshallers, optional
        The user marshaller/s to add to the collection. Must inherit
        from ``hdf5storage.Marshallers.TypeMarshaller``.

    Attributes
    ----------
    priority : tuple of str

    Raises
    ------
    TypeError
        If one of the arguments is the wrong type.
    ValueError
        If one of the arguments has an invalid value.

    See Also
    --------
    hdf5storage.Marshallers
    hdf5storage.Marshallers.TypeMarshaller

    """
    def __init__(self, load_plugins=False, lazy_loading=True,
                 priority=('builtin', 'plugin', 'user'),
                 marshallers=[]):
        if not isinstance(load_plugins, bool):
            raise TypeError('load_plugins must be bool.')
        if not isinstance(lazy_loading, bool):
            raise TypeError('lazy_loading must be bool.')
        if not isinstance(priority, collections.abc.Sequence):
            raise TypeError('priority must be a Sequence.')
        if sorted(priority) != sorted(('builtin', 'plugin', 'user')):
            raise ValueError('priority has a missing or invalid '
                             'element.')
        self._load_plugins = load_plugins
        self._lazy_loading = lazy_loading
        self._priority = tuple(priority)

        # Two lists of marshallers need to be maintained: one for the
        # builtin ones in the Marshallers module, and another for user
        # supplied ones.

        # Grab all the marshallers in the Marshallers module (they are
        # the classes that inherit from TypeMarshaller) by inspection.
        self._builtin_marshallers = [
            m()
            for key, m in dict(inspect.getmembers(
                    Marshallers,
                    lambda x: inspect.isclass(x)
                    and Marshallers.TypeMarshaller
                    in inspect.getmro(x))).items()]

        # If loading marshallers from plugins, grab all the entry points
        # by version and then go through them in version order, load the
        # entry points, call them to get the marshallers, and check that
        # they inherit from TypeMarshaller before adding them to the
        # list of marshallers.
        self._plugin_marshallers = []
        if load_plugins:
            plgs = plugins.find_thirdparty_marshaller_plugins()
            for ver in plugins.supported_marshaller_api_versions():
                for module, p in plgs[ver].items():
                    try:
                        fun = p.load()
                        # Check that it is a routine before getting the
                        # marshallers.
                        if not callable(fun):
                            continue
                        ms = [m for m in fun(__version__)
                              if isinstance(m,
                                            Marshallers.TypeMarshaller)]
                        self._plugin_marshallers.extend(ms)
                    except:
                        pass

        # Start with an initially empty list of user marshallers. The
        # ones given as an argument will be added using the adding
        # function.
        self._user_marshallers = []

        # A list of all the marshallers will be needed along with
        # dictionaries to lookup up the marshaller to use for given
        # types, type string, or MATLAB class string (they are the
        # keys). Additional lists will be used to keep track of whether
        # the required parent modules for each marshaller are present or
        # not and whether the required modules are imported or not.
        self._marshallers = []
        self._has_required_modules = []
        self._imported_required_modules = []
        self._types = dict()
        self._type_strings = dict()
        self._matlab_classes = dict()

        # Add any user given marshallers.
        self.add_marshaller(marshallers)

    @property
    def priority(self):
        """ The priority order when choosing the marshaller to use.

        tuple of str

        3-element ``tuple`` specifying the priority ordering (first has
        highest priority). The three elements are ``'builtin'`` for the
        builtin marshallers included in this package, ``'plugin'`` for
        marshallers provided by other python packages via plugin, and
        ``'user'`` for marshallers provided to this class explicityly
        during creation.

        """
        return self._priority

    def _update_marshallers(self):
        """ Update the full marshaller list and other data structures.

        Makes a full list of both builtin and user marshallers and
        rebuilds internal data structures used for looking up which
        marshaller to use for reading/writing Python objects to/from
        file.

        Also checks for whether the required modules are present or not,
        loading the required modules (if not doing lazy loading), and
        whether the required modules are imported already or not.

        """
        # Combine all sets of marshallers.
        self._marshallers = []
        for v in self._priority:
            if v == 'builtin':
                self._marshallers.extend(self._builtin_marshallers)
            elif v == 'plugin':
                self._marshallers.extend(self._plugin_marshallers)
            elif v == 'user':
                self._marshallers.extend(self._user_marshallers)
            else:
                raise ValueError('priority attribute has an illegal '
                                 'element value.')

        # Determine whether the required modules are present, do module
        # loading, and determine whether the required modules are
        # imported.
        self._has_required_modules = len(self._marshallers) * [False]
        self._imported_required_modules = \
            len(self._marshallers) * [False]

        for i, m in enumerate(self._marshallers):
            # Check if the required modules are here.
            try:
                for name in m.required_parent_modules:
                    if name not in sys.modules \
                            and pkgutil.find_loader(name) is None:
                        raise ImportError('module not present')
            except ImportError:
                self._has_required_modules[i] = False
            except:
                raise
            else:
                self._has_required_modules[i] = True

            # Modules obviously can't be fully loaded if not all are
            # present.
            if not self._has_required_modules[i]:
                self._imported_required_modules[i] = False
                continue

            # Check if all modules are loaded or not, and load them if
            # not doing lazy loading.
            try:
                for name in m.required_modules:
                    if name not in sys.modules:
                        raise ImportError('module not loaded yet.')
            except ImportError:
                if self._lazy_loading:
                    self._imported_required_modules[i] = False
                else:
                    success = self._import_marshaller_modules(m)
                    self._has_required_modules[i] = success
                    self._imported_required_modules[i] = success
            except:
                raise
            else:
                self._imported_required_modules[i] = True

        # Construct the dictionary to look up the appropriate marshaller
        # by type, the equivalent one to read data types given type
        # strings needs to be created from it (basically, we have to
        # make the key be the python_type_string from it), and the
        # equivalent one to read data types given MATLAB class strings
        # needs to be created from it (basically, we have to make the
        # key be the matlab_class from it).
        #
        # Marshallers earlier in the list have priority (means that the
        # builtins have the highest). Since the types can be specified
        # as strings as well, duplicates will be checked for by running
        # each type through str if it isn't str.
        types_as_str = set()
        self._types = dict()
        self._type_strings = dict()
        self._matlab_classes = dict()
        for i, m in enumerate(self._marshallers):
            # types.
            for tp in m.types:
                if isinstance(tp, str):
                    tp_as_str = tp
                else:
                    tp_as_str = tp.__module__ + '.' + tp.__name__
                if tp_as_str not in types_as_str:
                    self._types[tp_as_str] = i
                    types_as_str.add(tp_as_str)
            # type strings
            for type_string in m.python_type_strings:
                if type_string not in self._type_strings:
                    self._type_strings[type_string] = i
            # matlab classes.
            for matlab_class in m.matlab_classes:
                if matlab_class not in self._matlab_classes:
                    self._matlab_classes[matlab_class] = i

    def _import_marshaller_modules(self, m):
        """ Imports the modules required by the marshaller.

        Parameters
        ----------
        m : marshaller
            The marshaller to load the modules for.

        Returns
        -------
        success : bool
            Whether the modules `m` requires could be imported
            successfully or not.

        """
        try:
            for name in m.required_modules:
                if name not in sys.modules:
                    importlib.import_module(name)
        except ImportError:
            return False
        except:
            raise
        else:
            return True

    def add_marshaller(self, marshallers):
        """ Add a marshaller/s to the user provided list.

        Adds a marshaller or an Iterable of them to the user provided
        set of marshallers.

        .. versionchanged:: 0.2
           All marshallers must now inherit from
           ``hdf5storage.Marshallers.TypeMarshaller``.

        Parameters
        ----------
        marshallers : marshaller or Iterable
            The user marshaller/s to add to the user provided
            collection. Must inherit from
            ``hdf5storage.Marshallers.TypeMarshaller``.

        Raises
        ------
        TypeError
            If one of `marshallers` is the wrong type.

        See Also
        --------
        hdf5storage.Marshallers.TypeMarshaller

        """
        if not isinstance(marshallers, collections.abc.Iterable):
            marshallers = [marshallers]
        for m in marshallers:
            if not isinstance(m, Marshallers.TypeMarshaller):
                raise TypeError('Each marshaller must inherit from '
                                'hdf5storage.Marshallers.'
                                'TypeMarshaller.')
            if m not in self._user_marshallers:
                self._user_marshallers.append(m)
        self._update_marshallers()

    def remove_marshaller(self, marshallers):
        """ Removes a marshaller/s from the user provided list.

        Removes a marshaller or an Iterable of them from the user
        provided set of marshallers.

        Parameters
        ----------
        marshallers : marshaller or Iterable
            The user marshaller/s to from the user provided collection.

        """
        if not isinstance(marshallers, collections.abc.Iterable):
            marshallers = [marshallers]
        for m in marshallers:
            if m in self._user_marshallers:
                self._user_marshallers.remove(m)
        self._update_marshallers()

    def clear_marshallers(self):
        """ Clears the list of user provided marshallers.

        Removes all user provided marshallers, but not the builtin ones
        from the ``hdf5storage.Marshallers`` module or those from
        plugins, from the list of marshallers used.

        """
        self._user_marshallers.clear()
        self._update_marshallers()

    def get_marshaller_for_type(self, tp):
        """ Gets the appropriate marshaller for a type.

        Retrieves the marshaller, if any, that can be used to read/write
        a Python object with type 'tp'. The modules it requires, if
        available, will be loaded.

        Parameters
        ----------
        tp : type or str
            Python object ``type`` (which would be the class reference)
            or its string representation like ``'collections.deque'``.

        Returns
        -------
        marshaller : marshaller or None
            The marshaller that can read/write the type to
            file. ``None`` if no appropriate marshaller is found.
        has_required_modules : bool
            Whether the required modules for reading the type are
            present or not.

        See Also
        --------
        hdf5storage.Marshallers.TypeMarshaller.types

        """
        if not isinstance(tp, str):
            tp = tp.__module__ + '.' + tp.__name__
        if tp in self._types:
            index = self._types[tp]
        else:
            return None, False
        m = self._marshallers[index]
        if self._imported_required_modules[index]:
            return m, True
        if not self._has_required_modules[index]:
            return m, False
        success = self._import_marshaller_modules(m)
        self._has_required_modules[index] = success
        self._imported_required_modules[index] = success
        return m, success

    def get_marshaller_for_type_string(self, type_string):
        """ Gets the appropriate marshaller for a type string.

        Retrieves the marshaller, if any, that can be used to read/write
        a Python object with the given type string. The modules it
        requires, if available, will be loaded.

        Parameters
        ----------
        type_string : str
            Type string for a Python object.

        Returns
        -------
        marshaller : marshaller or None
            The marshaller that can read/write the type to
            file. ``None`` if no appropriate marshaller is found.
        has_required_modules : bool
            Whether the required modules for reading the type are
            present or not.

        See Also
        --------
        hdf5storage.Marshallers.TypeMarshaller.python_type_strings

        """
        if type_string in self._type_strings:
            index = self._type_strings[type_string]
            m = self._marshallers[index]
            if self._imported_required_modules[index]:
                return m, True
            if not self._has_required_modules[index]:
                return m, False
            success = self._import_marshaller_modules(m)
            self._has_required_modules[index] = success
            self._imported_required_modules[index] = success
            return m, success
        else:
            return None, False

    def get_marshaller_for_matlab_class(self, matlab_class):
        """ Gets the appropriate marshaller for a MATLAB class string.

        Retrieves the marshaller, if any, that can be used to read/write
        a Python object associated with the given MATLAB class
        string. The modules it requires, if available, will be loaded.

        Parameters
        ----------
        matlab_class : str
            MATLAB class string for a Python object.

        Returns
        -------
        marshaller : marshaller or None
            The marshaller that can read/write the type to
            file. ``None`` if no appropriate marshaller is found.
        has_required_modules : bool
            Whether the required modules for reading the type are
            present or not.

        See Also
        --------
        hdf5storage.Marshallers.TypeMarshaller.python_type_strings

        """
        if matlab_class in self._matlab_classes:
            index = self._matlab_classes[matlab_class]
            m = self._marshallers[index]
            if self._imported_required_modules[index]:
                return m, True
            if not self._has_required_modules[index]:
                return m, False
            success = self._import_marshaller_modules(m)
            self._has_required_modules[index] = success
            self._imported_required_modules[index] = success
            return m, success
        else:
            return None, False


class File(collections.abc.MutableMapping):
    """ Wrapper that allows writing and reading data from an HDF5 file.

    Opens an HDF5 file for reading (and optionally writing) Python
    objects from/to. The ``close`` method must be called to close the
    file. This class supports context handling with the ``with``
    statement.

    Python objects are read and written from/to paths. Paths can be
    given directly as POSIX style ``str`` or ``bytes``, as
    ``pathlib.PurePath``, or the separated path can be given as an
    iterable of ``str``, ``bytes``, and ``pathlib.PurePath``. Each part
    of a separated path is escaped using
    ``pathesc.escape_path``. Otherwise, the path is assumed to be
    already escaped. Escaping is done so that targets with a part that
    starts with one or more periods, contain slashes, and/or contain
    nulls can be used without causing the wrong Group to be looked in or
    the wrong target to be looked at. It essentially allows one to make
    a Dataset named ``'..'`` or ``'a/a'`` instead of moving around in
    the Dataset hierarchy.

    There are various options that can be used to influence how the data
    is read and written. They can be passed as an already constructed
    ``Options`` into `options` or as additional keywords that will be
    used to make one by ``options = Options(**keywords)``.

    Two very important options are ``store_python_metadata`` and
    ``matlab_compatible``, which are ``bool``. The first makes it so
    that enough metadata (HDF5 Attributes) are written that data can be
    read back accurately without it (or its contents if it is a
    container type) ending up different types, transposed in the case of
    numpy arrays, etc. The latter makes it so that the appropriate
    metadata is written, string and bool and complex types are converted
    properly, and numpy arrays are transposed; which is needed to make
    sure that MATLAB can import data correctly (the HDF5 header is also
    set so MATLAB will recognize it).

    This class is a MutableMapping, meaning that it supports many of the
    operations allowed on ``dict``, including operations that modify
    it.

    Example
    -------

       >>> import hdf5storage
       >>> with hdf5storage.File('data.h5', writable=True) as f:
       >>>     f.write(4, '/a')
       >>>     a = f.read('/a')
       >>> a
       4

    Note
    ----
    This class is threadsafe to the ``threading`` module, but not the
    ``multiprocessing`` module.

    Warning
    -------
    The passed ``Options`` object is shallow copied, meaning that
    changes to the original will not affect an instance of this class
    with the exception of changes within the ``marshaller_collection``
    option which is not deep copied. The ``marshallers_collection``
    option should not bechanged while a method of an instance of this
    class is running.

    Parameters
    ----------
    filename : str, optional
        The path to the HDF5 file to open. The default is ``'data.h5'``.
    writable : bool, optional
        Whether the writing should be allowed or not. The default is
        ``False`` (readonly).
    truncate_existing : bool, optional
        If `writable` is ``True``, whether to truncate the file if it
        already exists before writing to it.
    truncate_invalid_matlab : bool, optional
        If `writable` is ``True``, whether to truncate a file if
        matlab_compatibility is being done and the file doesn't have the
        proper header (userblock in HDF5 terms) setup for MATLAB
        metadata to be placed.
    options : Options or None, optional
        The options to use when reading and/or writing. Is mutually
        exclusive with any additional keyword arguments given (set to
        ``None`` or don't provide the argument at all to use them).
    **keywords :
        If `options` was not provided or was ``None``, these are used as
        arguments to make a ``Options``.

    Raises
    ------
    TypeError
        If an argument has an invalid type.
    ValueError
        If an argument has an invalid value.
    IOError
        If the file cannot be opened or some other file operation
        failed.

    Attributes
    ----------
    closed : bool
        Whether the file is closed or not.

    See Also
    --------
    pathesc.escape_path
    collections.abc.Collection

    """

    def __init__(self, filename='data.h5', writable=False,
                 truncate_existing=False, truncate_invalid_matlab=False,
                 options=None, **keywords):
        # Before we do anything else, we need to make the attributes for
        # the file handle, the options, and a lock. This way, these
        # attributes are available in __del__ even if there is an
        # exception in the constructor.
        self._file = None
        self._options = None
        self._lock = threading.Lock()
        # Check the types of the arguments.
        if not isinstance(filename, str):
            raise TypeError('filename must be str.')
        if not isinstance(writable, bool):
            raise TypeError('writable must be bool.')
        if not isinstance(truncate_existing, bool):
            raise TypeError('truncate_existing must be bool.')
        if not isinstance(truncate_invalid_matlab, bool):
            raise TypeError('truncate_invalid_matlab must be bool.')
        # Make the Options if we weren't given it, and shallow copy it
        # if it was given.
        if options is None:
            options = Options(**keywords)
        elif not isinstance(options, Options):
            raise TypeError('options must be an Options or None.')
        elif len(keywords) != 0:
            raise ValueError('Extra keyword arguments cannot be passed '
                             'if options is not None.')
        else:
            options = copy.copy(options)
        # Store the required arguments.
        self._writable = True
        self._options = options
        # Open the file. If writable is False, we can just open it. If
        # it is True, the process is longer.
        if not writable:
            self._file = h5py.File(filename, mode='r')
        else:
            # If the file doesn't already exist or the option is set to
            # truncate it if it does, just open it truncating whatever
            # is there. Otherwise, open it for read/write access without
            # truncating. Now, if we are doing matlab compatibility and
            # it doesn't have a big enough userblock (for metadata for
            # MATLAB to be able to tell it is a valid .mat file) and the
            # truncate_invalid_matlab is set, then it needs to be closed
            # and re-opened with truncation. Whenever we create the file
            # from scratch, even if matlab compatibility isn't being
            # done, a sufficiently sized userblock is going to be
            # allocated (smallest size is 512) for future use (after
            # all, someone might want to turn it to a .mat file later
            # and need it and it is only 512 bytes).
            if truncate_existing or not os.path.isfile(filename):
                self._file = h5py.File(filename, mode='w',
                                       userblock_size=512)
            else:
                self._file = h5py.File(filename, mode='a')
                if options.matlab_compatible \
                        and truncate_invalid_matlab \
                        and self._file.userblock_size < 128:
                    self._file.close()
                    self._file = None
                    self._file = h5py.File(filename, mode='w',
                                           userblock_size=512)
            # If matlab_compatible is set and we have a big enough
            # userblock, get the userblock size, close  the file, set
            # the userblock, and then reopen the file.
            if options.matlab_compatible \
                    and self._file.userblock_size >= 128:
                self._file.close()
                self._file = None
                # Get the time.
                now = datetime.datetime.now()
                # Construct the leading string. The MATLAB one looks
                # like
                #
                # s = 'MATLAB 7.3 MAT-file, Platform: GLNXA64, ' \
                #     'Created on: ' \
                #     + now.strftime('%a %b %d %H:%M:%S %Y') \
                #     + ' HDF5 schema 1.00 .'
                #
                # Platform is going to be changed to hdf5storage
                # version.
                s = 'MATLAB 7.3 MAT-file, Platform: hdf5storage ' \
                    + __version__ + ', Created on: ' \
                    + now.strftime('%a %b %d %H:%M:%S %Y') \
                    + ' HDF5 schema 1.00 .'

                # Make the bytearray while padding with spaces up to
                # 128-12 (the minus 12 is there since the last 12 bytes
                # are special).
                b = bytearray(s + (128-12-len(s))*' ', encoding='utf-8')
                # Add 8 nulls (0) and the magic number (or something)
                # that MATLAB uses.
                b.extend(bytearray.fromhex('00000000 00000000 0002494D'))
                # Now, write it to the beginning of the file.
                with open(filename, 'r+b') as f:
                    f.write(b)
                # Done writing the userblock, so we can re-open the
                # file.
                self._file = h5py.File(filename, mode='a')
        # Make the lowlevel file wrapper which will be used for the
        # actual reading and writing
        self._file_wrapper = utilities.LowLevelFile(self._file, options)

    def __enter__(self):
        return self

    def __exit__(self, tp, value, traceback):
        self.close()

    def __del__(self):
        try:
            self.close()
        except:
            pass

    @property
    def closed(self):
        return (self._file is None)

    def close(self):
        """ Closes the file. """
        with self._lock:
            self._file.close()
            self._file = None

    def flush(self):
        """ Flush contents to disk.

        Raises
        ------
        IOError
            If the file is closed.

        """
        with self._lock:
            if self._file is None:
                raise IOError('File is closed.')
            if self._writable:
                self._file.flush()

    def write(self, data, path='/'):
        """ Writes one piece of data into the file.

        A wrapper around the ``writes`` method to write a single piece
        of data, `data`, to a single location, `path`.

        Parameters
        ----------
        data : any
            The python object to write.
        path : str or bytes pathlib.PurePath or Iterable, optional
            The path to write the data to.  ``str`` and ``bytes`` paths
            must be POSIX style. The directory name is the Group to put
            it in and the basename is the Dataset/Group name to write it
            to. The default is ``'/'``.

        Raises
        ------
        IOError
            If the file is closed or it isn't writable.
        TypeError
            If `path` is an invalid type.
        NotImplementedError
            If writing `data` is not supported.
        exceptions.TypeNotMatlabCompatibleError
            If writing a type not compatible with MATLAB and the
            ``action_for_matlab_incompatible`` option is set to
            ``'error'``.

        See Also
        --------
        writes

        """
        self.writes({path: data})

    def writes(self, mdict):
        """ Write one or more pieces of data to the file.

        Stores one or more python objects in `mdict` to the specified
        locations in the HDF5. The paths are specified as POSIX style
        paths where the directory name is the Group to put it in and the
        basename is the Dataset/Group name to write to.

        Parameters
        ----------
        mdict : Mapping
            A ``dict`` or similar Mapping type of paths and the data to
            write to the file. The paths are the keys ( ``str`` and
            ``bytes`` paths must be POSIX style) where the directory
            name is the Group to put it in and the basename is the name
            to write it to. The values are the data to write.

        Raises
        ------
        IOError
            If the file is closed or it isn't writable.
        TypeError
            If a path in `mdict` is an invalid type.
        NotImplementedError
            If writing an object in `mdict` is not supported.
        exceptions.TypeNotMatlabCompatibleError
            If writing a type not compatible with MATLAB and the
            ``action_for_matlab_incompatible`` option is set to
            ``'error'``.

        """
        # Check the type of mdict. Technically a check of Mapping is
        # sufficient for dict but it is slow, so we check for dict
        # explicitly first.
        if not isinstance(mdict, (dict, collections.abc.Mapping)):
            raise TypeError('mdict must be a Mapping.')
        # File had to be opened writable.
        if not self._writable:
            raise IOError('File is not writable.')
        # Go through mdict, extract the paths and data, and process the
        # paths. A list of tulpes for each piece of data to write will
        # be constructed where he first element is the group name, the
        # second the target name (name of the Dataset/Group holding the
        # data), and the third element the data to write. We do not
        # allow any paths inside the Group specified by
        # options.group_for_references.
        towrite = []
        for p, v in mdict.items():
            groupname, targetname = pathesc.process_path(p)
            if posixpath.isabs(groupname):
                prefix = ''
            else:
                prefix = '/'
            if '/' != posixpath.commonpath(
                    (self._options.group_for_references,
                     posixpath.join(prefix, groupname, targetname))):
                raise ValueError('Cannot write to paths inside the the '
                                 'Group specified by the '
                                 'group_for_references option.')
            towrite.append((groupname, targetname, v))
        # File operations must be synchronized.
        with self._lock:
            # Check that the file is open.
            if self._file is None:
                raise IOError('File is closed.')
            # Go through each element of towrite and write them with the
            # low level write function.
            for groupname, targetname, data in towrite:
                self._file_wrapper.write_data(
                    self._file.require_group(groupname),
                    targetname, data,
                    None)

    def read(self, path='/'):
        """ Reads one piece of data from the file.

        A wrapper around the ``reads`` method to read a single piece of
        data at the   single location `path`.

        Parameters
        ----------
        path : str or bytes or pathlib.PurePath or Iterable, optional
            The path to read from. ``str`` and ``bytes`` paths must be
            POSIX style. The default is ``'/'``.

        Returns
        -------
        data : any
            The data that is read.

        Raises
        ------
        IOError
            If the file is closed.
        KeyError
            If the `path` cannot be found.
        exceptions.CantReadError
            If reading the data can't be done.

        See Also
        --------
        reads

        """
        return self.reads((path, ))[0]

    def reads(self, paths):
        """ Read pieces of data from the file.

        Parameters
        ----------
        paths : Iterable
            An iterable of paths to read data from. ``str`` and
            ``bytes`` paths must be POSIX style.

        Returns
        -------
        datas : Iterable
            An Iterable holding the piece of data for each path in
            `paths` in the same order.

        Raises
        ------
        IOError
            If the file is closed.
        KeyError
            If a path cannot be found.
        exceptions.CantReadError
            If reading the data can't be done.

        """
        if not isinstance(paths, collections.abc.Iterable):
            raise TypeError('paths must be an Iterable.')
        # Process the paths and stuff the group names and target names
        # as tuples into toread. We do not allow any paths inside the
        # Group specified by options.group_for_references.
        toread = []
        for p in paths:
            groupname, targetname = pathesc.process_path(p)
            if posixpath.isabs(groupname):
                prefix = ''
            else:
                prefix = '/'
            if '/' != posixpath.commonpath(
                    (self._options.group_for_references,
                     posixpath.join(prefix, groupname, targetname))):
                raise ValueError('Cannot read from paths inside the the '
                                 'Group specified by the '
                                 'group_for_references option.')
            toread.append((groupname, targetname))
        # File operations must be synchronized.
        with self._lock:
            # Check that the file is open.
            if self._file is None:
                raise IOError('File is closed.')
            # Read the data item by item
            datas = []
            for groupname, targetname in toread:
                # Check that the containing group is in the file and is
                # indeed a group. If it isn't an error needs to be
                # thrown.
                if groupname not in self._file \
                        or not isinstance(self._file[groupname],
                                          h5py.Group):
                    raise KeyError(
                        'Could not find containing Group '
                        + groupname + '.')
                # Hand off everything to the low level reader.
                datas.append(self._file_wrapper.read_data(
                    self._file[groupname], targetname))
        # Return it all.
        return datas

    def __len__(self):
        """ Get the number of objects stored in the file root.

        Returns
        -------
        length : int
            The number of objects stored in the file root.

        Raises
        ------
        IOError
            If the file is not open.

        """
        # File operations must be synchronized.
        with self._lock:
            # Check that the file is open.
            if self._file is None:
                raise IOError('File is closed.')
            # Get the length from the file, and then, if the Group for
            # references is in the root group, subtract one if it is
            # present (impossible if the length is zero).
            length = len(self._file)
            if length != 0 and posixpath.split( \
                    self._options.group_for_references)[0] == '/' \
                    and self._options.group_for_references \
                    in self._file:
                return length - 1
            else:
                return length

    def __contains__(self, path):
        """ Checks if an object exists at the specified `path`.

        Parameters
        ----------
        path : str or bytes or pathlib.PurePath Iterable
            The path to check for the existence of an object at. ``str``
            and ``bytes`` paths must be POSIX style.

        Raises
        ------
        IOError
            If the file is not open.

        """
        groupname, targetname = pathesc.process_path(path)
        # File operations must be synchronized.
        with self._lock:
            # Check that the file is open.
            if self._file is None:
                raise IOError('File is closed.')
            # Do the check.
            return (posixpath.join(groupname, targetname) in self._file)

    def __iter__(self):
        """ Get an Iterator over the names in the file root.

        Warning
        -------
        The names are returned as is, rather than unescaped. Use
        ``pathesc.unescape_path`` to unescape them.

        Returns
        -------
        it : Iterator
            Iterator over the names of the objects in the file root.

        Raises
        ------
        IOError
            If the file is not open.

        See Also
        --------
        pathesc.unescape_path

        """
        # File operations must be synchronized.
        with self._lock:
            # Check that the file is open.
            if self._file is None:
                raise IOError('File is closed.')
            # We will use the output of the __iter__ method of the file,
            # but if the Group for references is in the root Group, we
            # will need to filter it out.
            refgrp = self._options.group_for_references
            it = self._file.__iter__()
            if posixpath.split(refgrp)[0] == '/':
                refgrp = refgrp[1:]
                return itertools.dropwhile(lambda k: k == refgrp, it)
            else:
                return it

    def __getitem__(self, path):
        """ Reads the object at the specified `path` from the file.

        A wrapper around the ``reads`` method to read a single piece of
        data at the single location `path`.

        Parameters
        ----------
        path : str or bytes or pathlib.PurePath or Iterable, optional
            The path to read from. ``str`` and ``bytes`` paths must be
            POSIX style.

        Returns
        -------
        data : any
            The data that is read.

        Raises
        ------
        IOError
            If the file is closed.
        KeyError
            If the `path` cannot be found.
        exceptions.CantReadError
            If reading the data can't be done.

        See Also
        --------
        reads

        """
        return self.reads((path, ))[0]

    def __setitem__(self, path, data):
        """ Writes one piece of data into the file.

        A wrapper around the ``writes`` method to write a single piece
        of data, `data`, to a single location, `path`.

        Parameters
        ----------
        path : str or bytes or pathlib.PurePath or Iterable
            The path to write the data to. ``str`` and ``bytes`` paths
            must be POSIX style. The directory name is the Group to put
            it in and the basename is the Dataset/Group name to write it
            to.
        data : any
            The python object to write.

        Raises
        ------
        IOError
            If the file is closed or it isn't writable.
        TypeError
            If `path` is an invalid type.
        NotImplementedError
            If writing `data` is not supported.
        exceptions.TypeNotMatlabCompatibleError
            If writing a type not compatible with MATLAB and the
            ``action_for_matlab_incompatible`` option is set to
            ``'error'``.

        See Also
        --------
        writes

        """
        self.writes({path: data})

    def __delitem__(self, path):
        """ Deletes one path from the file.

        Deletes one location from the file specified by `path`.

        Parameters
        ----------
        path : str or bytes or pathlib.PurePath or Iterable
            The path to write the data to. ``str`` and ``bytes`` paths
            must be POSIX style. The directory name is the Group to put
            it in and the basename is the Dataset/Group name to write it
            to.

        Raises
        ------
        IOError
            If the file is closed or it isn't writable.
        TypeError
            If `path` is an invalid type.
        KeyError
            If there is no object at `path` in the file.

        """
        # File had to be opened writable.
        if not self._writable:
            raise IOError('File is not writable.')
        # Process the path.
        groupname, targetname = pathesc.process_path(path)
        # File operations must be synchronized.
        with self._lock:
            # Check that the file is open.
            if self._file is None:
                raise IOError('File is closed.')
            del self._file[posixpath.join(groupname, targetname)]


def writes(mdict, **keywords):
    """ Writes data into an HDF5 file.

    Wrapper around ``File`` and ``File.writes``. Specifically, this
    function is

        >>> with File(writable=True, **keywords) as f:
        >>>     f.writes(mdict)

    Parameters
    ----------
    mdict : Mapping
        The ``dict`` or other dictionary type object of paths
        and data to write to the file. The paths are the keys (``str``
        and ``bytes`` paths must be POSIX style) where the directory
        name is the Group to put it in and the basename is the name to
        write it to. The values are the data to write.
    **keywords :
        Extra keyword arguments to pass to ``File``.

    Raises
    ------
    TypeError
        If an argument has an invalid type.
    ValueError
        If an argument has an invalid value.
    IOError
        If the file cannot be opened or some other file operation
        failed.
    NotImplementedError
        If writing anything in `mdict` is not supported.
    exceptions.TypeNotMatlabCompatibleError
        If writing a type not compatible with MATLAB and the
        ``action_for_matlab_incompatible`` option is set to
        ``'error'``.

    See Also
    --------
    File
    File.writes

    """
    with File(writable=True, **keywords) as f:
        f.writes(mdict)


def write(data, path='/', **keywords):
    """ Writes one piece of data into an HDF5 file.

    Wrapper around ``File`` and ``File.write``. Specifically, this
    function is

        >>> with File(writable=True, **keywords) as f:
        >>>     f.write(data, path)

    Parameters
    ----------
    data : any
        The python object to write.
    path : str or bytes or pathlib.PurePath or Iterable, optional
        The path to write the data to. ``str`` and ``bytes`` paths must
        be POSIX style. The directory name is the Group to put it in and
        the basename is the Dataset name to write it to. The default is
        ``'/'``.
    **keywords :
        Extra keyword arguments to pass to ``File``.

    Returns
    -------
    data : any
        The data that is read.

    Raises
    ------
    TypeError
        If an argument has an invalid type.
    ValueError
        If an argument has an invalid value.
    IOError
        If the file cannot be opened or some other file operation
        failed.
    NotImplementedError
        If writing `data` is not supported.
    exceptions.TypeNotMatlabCompatibleError
        If writing a type not compatible with MATLAB and the
        ``action_for_matlab_incompatible`` option is set to
        ``'error'``.

    See Also
    --------
    File
    File.write

    """
    with File(writable=True, **keywords) as f:
        f.write(data, path)


def reads(paths, **keywords):
    """ Reads pieces of data from an HDF5 file.

    Wrapper around ``File`` and ``File.reads`` with the exception that
    the ``matlab_compatible`` option is set to ``False`` if it isn't
    given explicitly. Specifically, this function does

        >>> if 'matlab_compatible' in keywords or (
        ...         'options' in keywords
        ...          and keywords['options'] is not None):
        >>>     extra_kws = dict()
        >>> else:
        >>>     extra_kws = {'matlab_compatible': False}
        >>> with File(writable=False, **extra_kws, **keywords) as f:
        >>>     f.reads(paths)

    Parameters
    ----------
    paths : Iterable
        An iterable of paths to read data from. ``str`` and ``bytes``
        paths must be POSIX style.
    **keywords :
        Extra keyword arguments to pass to ``File``.

    Returns
    -------
    datas : iterable
        An iterable holding the piece of data for each path in `paths`
        in the same order.

    Raises
    ------
    TypeError
        If an argument has an invalid type.
    ValueError
        If an argument has an invalid value.
    KeyError
        If a path cannot be found.
    IOError
        If the file cannot be opened or some other file operation
        failed.
    IOError
        If the file is closed.
    exceptions.CantReadError
        If reading the data can't be done.

    See Also
    --------
    File
    File.read

    """
    if 'matlab_compatible' in keywords or (
            'options' in keywords
            and keywords['options'] is not None):
        extra_kws = dict()
    else:
        extra_kws = {'matlab_compatible': False}
    with File(writable=False, **extra_kws, **keywords) as f:
        return f.reads(paths)


def read(path='/', **keywords):
    """ Reads one piece of data from an HDF5 file.

    Wrapper around ``File`` and ``File.reads`` with the exception that
    the ``matlab_compatible`` option is set to ``False`` if it isn't
    given explicitly. Specifically, this function does

        >>> if 'matlab_compatible' in keywords or (
        ...         'options' in keywords
        ...          and keywords['options'] is not None):
        >>>     extra_kws = dict()
        >>> else:
        >>>     extra_kws = {'matlab_compatible': False}
        >>> with File(writable=False, **extra_kws, **keywords) as f:
        >>>     f.read(path)

    Parameters
    ----------
    path : str or bytes or pathlib.PurePath or Iterable, optional
        The path to read from. ``str`` and ``bytes`` paths must be POSIX
        style. The default is ``'/'``.
    **keywords :
        Extra keyword arguments to pass to ``File``.

    Raises
    ------
    TypeError
        If an argument has an invalid type.
    ValueError
        If an argument has an invalid value.
    KeyError
        If the `path` cannot be found.
    IOError
        If the file cannot be opened or some other file operation
        failed.
    IOError
        If the file is closed.
    exceptions.CantReadError
        If reading the data can't be done.

    See Also
    --------
    File
    File.reads

    """
    if 'matlab_compatible' in keywords or (
            'options' in keywords
            and keywords['options'] is not None):
        extra_kws = dict()
    else:
        extra_kws = {'matlab_compatible': False}
    with File(writable=False, **extra_kws, **keywords) as f:
        return f.read(path)


def savemat(file_name, mdict, appendmat=True, format='7.3',
            oned_as='row', store_python_metadata=True,
            action_for_matlab_incompatible='error',
            marshaller_collection=None, truncate_existing=False,
            truncate_invalid_matlab=False, **keywords):
    """ Save a dictionary of python objects to a MATLAB MAT file.

    Saves the data provided in the dictionary `mdict` to a MATLAB MAT
    file. `format` determines which kind/vesion of file to use. The
    '7.3' version, which is HDF5 based, is handled by this package and
    all types that this package can write are supported. Versions 4 and
    5 are not HDF5 based, so everything is dispatched to the SciPy
    package's ``scipy.io.savemat`` function, which this function is
    modelled after (arguments not specific to this package have the same
    names, etc.).

    Parameters
    ----------
    file_name : str or file-like object
        Name of the MAT file to store in. The '.mat' extension is
        added on automatically if not present if `appendmat` is set to
        ``True``. An open file-like object can be passed if the writing
        is being dispatched to SciPy (`format` < 7.3).
    mdict : dict
        The dictionary of variables and their contents to store in the
        file.
    appendmat : bool, optional
        Whether to append the '.mat' extension to `file_name` if it
        doesn't already end in it or not.
    format : {'4', '5', '7.3'}, optional
        The MATLAB mat file format to use. The '7.3' format is handled
        by this package while the '4' and '5' formats are dispatched to
        SciPy.
    oned_as : {'row', 'column'}, optional
        Whether 1D arrays should be turned into row or column vectors.
    store_python_metadata : bool, optional
        Whether or not to store Python type information. Doing so allows
        most types to be read back perfectly. Only applicable if not
        dispatching to SciPy (`format` >= 7.3).
    action_for_matlab_incompatible: str, optional
        The action to perform writing data that is not MATLAB
        compatible. The actions are to write the data anyways
        ('ignore'), don't write the incompatible data ('discard'), or
        throw a ``TypeNotMatlabCompatibleError`` exception.
    marshaller_collection : MarshallerCollection, optional
        Collection of marshallers to disk to use. Only applicable if
        not dispatching to SciPy (`format` >= 7.3).
    truncate_existing : bool, optional
        Whether to truncate the file if it already exists before writing
        to it.
    truncate_invalid_matlab : bool, optional
        Whether to truncate a file if the file doesn't have the proper
        header (userblock in HDF5 terms) setup for MATLAB metadata to be
        placed.
    **keywords :
        Additional keywords arguments to be passed onto
        ``scipy.io.savemat`` if dispatching to SciPy (`format` < 7.3).

    Raises
    ------
    ImportError
        If `format` < 7.3 and the ``scipy`` module can't be found.
    NotImplementedError
        If writing a variable in `mdict` is not supported.
    exceptions.TypeNotMatlabCompatibleError
        If writing a type not compatible with MATLAB and
        `action_for_matlab_incompatible` is set to ``'error'``.

    Notes
    -----
    Writing the same data and then reading it back from disk using the
    HDF5 based version 7.3 format (the functions in this package) or the
    older format (SciPy functions) can lead to very different
    results. Each package supports a different set of data types and
    converts them to and from the same MATLAB types differently.

    See Also
    --------
    loadmat : Equivelent function to do reading.
    scipy.io.savemat : SciPy function this one models after and
        dispatches to.
    Options
    writes : Function used to do the actual writing.

    """
    # If format is a number less than 7.3, the call needs to be
    # dispatched to the scipy version, if it is available, with all the
    # relevant and extra keywords options provided.
    if float(format) < 7.3:
        importlib.import_module('scipy.io').savemat(
            file_name, mdict, appendmat=appendmat,
            format=format, oned_as=oned_as, **keywords)
        return

    # Append .mat if it isn't on the end of the file name and we are
    # supposed to.
    if appendmat:
        if isinstance(file_name, str) \
                and not file_name.endswith('.mat'):
            file_name = file_name + '.mat'
        elif isinstance(file_name, bytes) \
                and not file_name.endswith(b'.mat'):
            file_name = file_name + b'.mat'

    # Make the options with matlab compatibility forced.
    options = Options(
        store_python_metadata=store_python_metadata,
        matlab_compatible=True, oned_as=oned_as,
        action_for_matlab_incompatible=action_for_matlab_incompatible,
        marshaller_collection=marshaller_collection)

    # Write the variables in the dictionary to file.
    writes(mdict=mdict, filename=file_name,
           truncate_existing=truncate_existing,
           truncate_invalid_matlab=truncate_invalid_matlab,
           options=options)


def loadmat(file_name, mdict=None, appendmat=True,
            variable_names=None,
            marshaller_collection=None, **keywords):
    """ Loads data to a MATLAB MAT file.

    Reads data from the specified variables (or all) in a MATLAB MAT
    file. There are many different formats of MAT files. This package
    can only handle the HDF5 based ones (the version 7.3 and later).
    As SciPy's ``scipy.io.loadmat`` function can handle the earlier
    formats, if this function cannot read the file, it will dispatch it
    onto the scipy function with all the calling arguments it uses
    passed on. This function is modelled after the SciPy one (arguments
    not specific to this package have the same names, etc.).

    Warning
    -------
    Variables in `variable_names` that are missing from the file do not
    cause an exception and will just be missing from the output.

    Parameters
    ----------
    file_name : str
        Name of the MAT file to read from. The '.mat' extension is
        added on automatically if not present if `appendmat` is set to
        ``True``.
    mdict : dict, optional
        The dictionary to insert read variables into
    appendmat : bool, optional
        Whether to append the '.mat' extension to `file_name` if it
        doesn't already end in it or not.
    variable_names: None or sequence, optional
        The variable names to read from the file. ``None`` selects all.
    marshaller_collection : MarshallerCollection, optional
        Collection of marshallers from disk to use. Only applicable if
        not dispatching to SciPy (version 7.3 and newer files).
    **keywords :
        Additional keywords arguments to be passed onto
        ``scipy.io.loadmat`` if dispatching to SciPy if the file is not
        a version 7.3 or later format.

    Returns
    -------
    mdict : dict
        Dictionary of all the variables read from the MAT file (name
        as the key, and content as the value). If a variable was missing
        from the file, it will not be present here.

    Raises
    ------
    ImportError
        If it is not a version 7.3 .mat file and the ``scipy`` module
        can't be found when dispatching to SciPy.
    KeyError
        If a variable cannot be found.
    exceptions.CantReadError
        If reading the data can't be done.

    Notes
    -----
    Writing the same data and then reading it back from disk using the
    HDF5 based version 7.3 format (the functions in this package) or the
    older format (SciPy functions) can lead to very different
    results. Each package supports a different set of data types and
    converts them to and from the same MATLAB types differently.

    See Also
    --------
    savemat : Equivalent function to do writing.
    scipy.io.loadmat : SciPy function this one models after and
        dispatches to.
    Options
    reads : Function used to do the actual reading.

    """
    # Will first assume that it is the HDF5 based 7.3 format. If an
    # OSError occurs, then it wasn't an HDF5 file and the scipy function
    # can be tried instead.
    try:
        # Make the options with the given marshallers.
        options = Options(marshaller_collection=marshaller_collection)

        # Append .mat if it isn't on the end of the file name and we are
        # supposed to.
        if appendmat:
            if isinstance(file_name, str) \
                    and not file_name.endswith('.mat'):
                filename = file_name + '.mat'
            elif isinstance(file_name, bytes) \
                    and not file_name.endswith(b'.mat'):
                filename = file_name + b'.mat'
            else:
                filename = file_name
        else:
            filename = file_name

        # Read everything if we were instructed.
        with File(filename, writable=False, options=options) as f:
            if variable_names is None:
                data = {pathesc.unescape_path(k): v for k, v in f.items()}
            else:
                data = dict()
                for k in variable_names:
                    try:
                        data[k] = f.read(k)
                    except:
                        pass
        # Read all the variables, stuff them into mdict, and return it.
        if mdict is None:
            mdict = data
        for k, v in data.items():
            mdict[k] = v
        return mdict
    except OSError:
        return importlib.import_module('scipy.io').loadmat(
            file_name, mdict, appendmat=appendmat,
            variable_names=variable_names,
            **keywords)


def get_default_MarshallerCollection():
    """ Gets the default MarshallerCollection.

    The initial default only includes the builtin marshallers in the
    ``Marshallers`` submodule.

    Returns
    -------
    mc : MarshallerCollection
        The default MarshallerCollection.

    Warning
    -------
    Any changes made to `mc` after getting it will be persistent to
    future calls of this function till
    ``make_new_default_MarshallerCollection`` is called.

    See Also
    --------
    make_new_default_MarshallerCollection

    """
    return _default_marshaller_collection[0]


def make_new_default_MarshallerCollection(*args, **keywords):
    """ Makes a new default MarshallerCollection.

    Replaces the current default ``MarshallerCollection`` with a new
    one.

    Parameters
    ----------
    *args : positional arguments
        Positional arguments to use in creating the
       ``MarshallerCollection``.
    **keywords : keywords arguments
        Keyword arguments to use in creating the
       ``MarshallerCollection``.

    See Also
    --------
    MarshallerCollection
    get_default_MarshallerCollection

    """
    _default_marshaller_collection[0] = MarshallerCollection(*args,
                                                             **keywords)


# Make a default MarshallerCollection of just the builtins with lazy
# loading. This will be used as the source for those used in options. It
# must be packed into a list so that it can be set from functions inside
# this module without scoping problems.
_default_marshaller_collection = [None]
make_new_default_MarshallerCollection(lazy_loading=True)
