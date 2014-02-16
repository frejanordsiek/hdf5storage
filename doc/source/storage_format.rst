.. currentmodule:: hdf5storage

==============
Storage Format
==============

This package adopts certain conventions for the conversion and storage
of Python datatypes and the metadata that is written with them. Then, to
make the data MATLAB MAT file compatible, additional metadata must be
written. This page assumes that one has imported collections and numpy
as ::

    import collections as cl
    import numpy as np


MATLAB File Header
==================

In order for a file to be MATLAB v7.3 MAT file compatible, it must have
a properly formatted file header, or userblock in HDF5 terms. The file
must have a 512 byte userblock, of which 128 bytes are used. The 128
bytes consists of a 116 byte string (spaces pad the end) followed by a
specific 12 byte sequence (magic number). On MATLAB, the 116 byte string, depending on the computer system and the date, looks like ::

    b'MATLAB 7.3 MAT-file, Platform: GLNXA64, Created on: Fri Feb 07 02:29:00 2014 HDF5 schema 1.00 .'

This package just changes the Platform part to ::

    b'CPython A.B.C'

Where A, B, and C are the major, minor, and micro version numbers of the Python interpreter (e.g. 3.3.0).

The 12 byte sequence, in hexidecimal is ::

    00000000 00000000 0002494D


How Data Is Stored
==================

All data is stored either as a Dataset or as a Group. Most non-Numpy
types must be converted to a Numpy type before they are written, and
some Numpy types must be converted to other ones before being
written. The table below lists how every supported Python datatype is
stored (Group or Dataset), what type/s it is converted to (no conversion
if none are listed), as well as the first version of this package to
support the datatype.

=============  =======  ====================================  =====================
Type           Version  Converted to                          Group or Dataset
=============  =======  ====================================  =====================
bool           0.1      np.bool\_ or np.uint8 [1]_            Dataset
None           0.1      ``np.float64([])``                    Dataset
int            0.1      np.int64                              Dataset
float          0.1      np.float64                            Dataset
complex        0.1      np.complex128                         Dataset
str            0.1      np.uint32/16 [2]_                     Dataset
bytes          0.1      np.bytes\_ or np.uint16 [3]_          Dataset
bytearray      0.1      np.bytes\_ or np.uint16 [3]_          Dataset
list           0.1      np.object\_                           Dataset
tuple          0.1      np.object\_                           Dataset
set            0.1      np.object\_                           Dataset
frozenset      0.1      np.object\_                           Dataset
cl.deque       0.1      np.object\_                           Dataset
dict [4]_      0.1                                            Group
np.bool\_      0.1      not or np.uint8 [1]_                  Dataset
np.void        0.1                                            Dataset
np.uint8       0.1                                            Dataset
np.uint16      0.1                                            Dataset
np.uint32      0.1                                            Dataset
np.uint64      0.1                                            Dataset
np.uint8       0.1                                            Dataset
np.int16       0.1                                            Dataset
np.int32       0.1                                            Dataset
np.int64       0.1                                            Dataset
np.float16     0.1                                            Dataset
np.float32     0.1                                            Dataset
np.float64     0.1                                            Dataset
np.complex64   0.1                                            Dataset
np.complex128  0.1                                            Dataset
np.str\_       0.1      np.uint32/16 [2]_                     Dataset
np.bytes\_     0.1      np.bytes\_ or np.uint16 [3]_          Dataset
np.object\_    0.1                                            Dataset
np.ndarray     0.1      not or Group of contents [5]_         Dataset or Group [5]_
np.matrix      0.1      np.ndarray                            Dataset
np.chararray   0.1      np.bytes\_ or np.uint16/32 [2]_ [3]_  Dataset
np.recarray    0.1      structued np.ndarray [5]_             Dataset or Group [5]_
=============  =======  ====================================  =====================

.. [1] Depends on the selected options. Always ``np.uint8`` when
       ``convert_bools_to_uint8 == True`` (set implicitly when
       ``matlab_compatible == True``).
.. [2] Depends on the selected options and whether it can be converted
       to UTF-16 without using doublets. If
       ``convert_numpy_str_to_utf16 == True`` (set implicitly when
       ``matlab_compatible == True``) and it can be converted to UTF-16
       without losing any characters that can't be represented in UTF-16
       or using UTF-16 doublets (MATLAB doesn't support them), then it
       is written as ``np.uint16`` in UTF-16 encoding. Otherwise, it is
       stored at ``np.uint32`` in UTF-32 encoding.
.. [3] Depends on the selected options. If
       ``convert_numpy_bytes_to_utf16 == True`` (set implicitly when
       ``matlab_compatible == True``), it will be stored as
       ``np.uint16`` in UTF-16 encoding. Otherwise, it is just written
       as ``np.bytes_``.
.. [4] All keys must be ``str`` in Python 3 or ``unicode`` in Python 2.
.. [5] If it doesn't have any fields in its dtype or if
       :py:attr:`Options.structured_numpy_ndarray_as_struct` is not set, it
       is not converted and is written as is as a Dataset. Otherwise, it
       is written as a Group with its the contents of its individual
       fields written as Datasets within the Group having the fields as
       names.


Attributes
==========

Many different HDF5 Attributes are set for each object written if the
:py:attr:`Options.store_python_metadata` and/or
:py:attr:`Options.matlab_compatible` options are set. The attributes
associated with each will be referred to as "Python Attributes" and
"MATLAB Attributes" respectively. If neither of them are set, then no
Attributes are used. The table below lists the Attributes that have
definite values depending only on the particular Python datatype being
stored. Then, the other attributes are detailed individually.

.. note

   'Python.Type', 'Python.numpy.UnderlyingType', and 'MATLAB_class' are
   all ``np.bytes_``. 'MATLAB_int_decode' is a ``np.int64``.
   'Python.Fields' is a ``np.object_`` array of ``str``.

=============  ===================  ===========================  ==================  =================
               Python Attributes                                 MATLAB Attributes
               ------------------------------------------------  -------------------------------------
Type           Python.Type          Python.numpy.UnderlyingType  MATLAB_class        MATLAB_int_decode
=============  ===================  ===========================  ==================  =================
bool           'bool'               'bool'                       'logical'           1
None           'builtins.NoneType'  'float64'                    'double'
int            'int'                'int64'                      'int64'
float          'float'              'float64'                    'double'
complex        'complex'            'complex128'                 'double'
str            'str'                'str#' [6]_                  'char'              2
bytes          'bytes'              'bytes#' [6]_                'char'              2
bytearray      'bytearray'          'bytes#' [6]_                'char'              2
list           'list'               'object'                     'cell'
tuple          'tuple'              'object'                     'cell'
set            'set'                'object'                     'cell'
frozenset      'frozenset'          'object'                     'cell'
cl.deque       'collections.deque'  'object'                     'cell'
dict           'dict'                                            'struct'
np.bool\_      'numpy.bool'         'bool'                       'logical'           1
np.void        'numpy.void'         'void#' [6]_
np.uint8       'numpy.uint8'        'uint8'                      'uint8'
np.uint16      'numpy.uint16'       'uint16'                     'uint16'
np.uint32      'numpy.uint32'       'uint32'                     'uint32'
np.uint64      'numpy.uint64'       'uint64'                     'uint64'
np.uint8       'numpy.int8'         'int8'                       'int8'
np.int16       'numpy.int16'        'int16'                      'int16'
np.int32       'numpy.int32'        'int32'                      'int32'
np.int64       'numpy.int64'        'int64'                      'int64'
np.float16     'numpy.float16'      'float16'
np.float32     'numpy.float32'      'float32'                    'single'
np.float64     'numpy.float64'      'float64'                    'double'
np.complex64   'numpy.complex64'    'complex64'                  'single'
np.complex128  'numpy.complex128'   'complex128'                 'double'
np.str\_       'numpy.str\_'        'str#' [6]_                  'char' or 'uint32'  2 or 4 [6]_
np.bytes\_     'numpy.bytes\_'      'bytes#' [6]_                'char'              2
np.object\_    'numpy.object\_'     'object'                     'cell'
np.ndarray     'numpy.ndarray'      [8]_                         [8]_ [9]_
np.matrix      'numpy.matrix'       [8]_                         [8]_
np.chararray   'numpy.chararray'    [8]_                         'char' [8]_
np.recarray    'numpy.recarray'     [8]_                         [8]_ [9]_
=============  ===================  ===========================  ==================  =================

.. [6] '#' is replaced by the number of bits taken up by the string, or
       each string in the case that it is an array of strings. This is 8
       and 32 bits per character for ``np.bytes_`` and ``np.str_``
       respectively.
.. [7] ``2`` if it is stored as ``np.uint16`` or ``4`` if ``np.uint32``.
.. [8] The value that would be put in for a scalar of the same dtype is
       used.
.. [9] If it is structured (its dtype has fields) and
       :py:attr:`Options.structured_numpy_ndarray_as_struct` is set, it is
       set to 'struct' overriding anything else.


Python.Shape
------------

Python Attribute

``np.ndarray(dtype='uint64')``

Every Python datatype that is or ends up being converted to a Numpy
datatype has a shape attribute, which is stored in this Attribute. This
holds the shape before any conversions of arrays to at least 2D, array
transposes, or conversions of strings to unsigned integer types.

Python.numpy.Container
----------------------

Python Attribute

{'scalar', 'ndarray', 'matrix', 'chararray', 'recarray'}

For Numpy types (or types converted to them), whether the type is a
scalar (its type is something such as ``np.uint16``, ``np.str_``, etc.),
some form of array (its type is ``np.ndarray``), a matrix (type
is ``np.matrix``), is a ``np.chararray``, or is a ``np.recarray`` is
stored in this Attribute.

Python.Fields
-------------

Python Attribute

``np.object_`` array of ``str``

For ``dict`` and structured ``np.ndarray`` types (and those converted to
them), an array of the field names of the array is stored in this
Attribute in the proper order. In the HDF5 file, they are variable
length strings.

Python.Empty and MATLAB_empty
-----------------------------

Python and MATLAB Attributes respectively

``np.uint8``

If the datatype being stored has zero elements, then this Attribute is
set to ``1``. Otherwise, the Attribute is deleted. For Numpy types (or
those converted to them), the shape after conversions to at least 2D,
array transposes, and conversions of strings to unsigned integer types
is stored in place of the data as an array of ``np.uint64`` if
:py:attr:`Options.store_shape_for_empty` is set (set implicitly if the
`matlab_compatible` option is set).

H5PATH
------

MATLAB Attribute

``np.str_``

For every object that is stored inside a Group other than the root of
the HDF5 file (``'/'``), the path to the object is stored in this
Attribute. MATLAB does not seem to require this Attribute to be there,
though it does set it in the files it produces.

MATLAB_fields
-------------

MATLAB Attribute

complicated array of string arrays not supported by h5py

For MATLAB structures, MATLAB sets this field to all of the field names
of the structure. If this Attribute is missing, MATLAB does not seem to
care. Trying to set it to a differently formatted array of strings that
the h5py package can handle causes an error in MATLAB when the file is
imported, so this package does not set this Attribute at all.


Storage of Special Types
========================

Complex Numbers
---------------

Complex numbers and ``np.object_`` arrays (and things converted to them)
have to be stored in a special fashion.

Since HDF5 has no builtin complex type, complex numbers are stored as an
HDF5 COMPOUND type with different fieldnames for the real and imaginary
partd like many other pieces of software (including MATLAB)
do. Unfortunately, there is not a standardized pair of field names. h5py
by default uses 'r' and 'i' for the real and imaginary parts. MATLAB
uses 'real' and 'imag' instead. The :py:attr:`Options.complex_names`
option controls the field names (given as a tuple in real, imaginary
order) that are used for complex numbers as they are written. It is set
automatically to ``('real', 'imag')`` when
``matlab_compatible == True``. When reading data, this package
automatically checks numeric types for many combinations of reasonably
expected field names to find complex types.

np.object\_
-----------

When storing ``np.object_`` arrays, the individual elements are stored
elsewhere and then an array of HDF5 Object References to their storage
locations is written as the data object. The elements are all written to
the Group path set by :py:attr:`Options.group_for_references` with a
randomized name (this package keeps generating randomized names till an
available one is found). It must be ``'/#refs#'`` for MATLAB (setting
``matlab_compatible`` sets this automatically). Those elements that
can't be written (doing MATLAB compatibility and we are set to discard
MATLAB incompatible types
:py:attr:`Options.action_for_matlab_incompatible`) will instead end up
being a reference to the canonical empty inside the group. The canonical
empty has the same format as in MATLAB and is a Dataset named 'a' of
``np.uint32/64([0, 0])`` with the Attribute 'MATLAB_class' set to
'canonical empty' and the Attribute 'MATLAB_empty' set to
``np.uint8(1)``.

Structure Like Data
-------------------

When storing data that is MATLAB struct like (``dict`` or structured
``np.ndarray`` when
:py:attr:`Options.structured_numpy_ndarray_as_struct` is set), it is
stored as an HDF5 Group with its contents of its fields written inside
of the Group. For single element data (``dict`` or structured
``np.ndarray`` with only a single element), the fields are written to
Datasets inside the Group. For multi-element data, the elements for
each field are written in :py:attr:`Options.group_for_references` and
an HDF5 Reference array to all of those elements is written as a Dataset
under the field name in the Groups.

.. note::

   If it has no elements and
   :py:attr:`Options.structured_numpy_ndarray_as_struct` is set, it
   can't be read back from the file accurately. The dtype for all the
   fields will become 'object' instead of what they originally were.

.. note::

   In Python 2, importing structured ``np.ndarray`` s if any of their
   fields have characters outside of ASCII.


Optional Data Transformations
=============================

Many different data conversions beyond turning most non-Numpy types into
Numpy types, can be done and are controlled by individual settings in
the :py:class:`Options` class. Most are set to fixed values when
``matlab_compatible == True``, which are shown in the table below. The
transfomations are listed below by their option name, other than
`complex_names` and `group_for_references` which were explained in the
previous section.

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
==================================  ====================


delete_unused_variables
-----------------------

``bool``

Whether any variable names in something that would be stored as an HDF5
Group (would end up a struct in MATLAB) that currently exist in the file
but are not in the object being stored should be deleted on the file or
not.

structured_numpy_ndarray_as_struct
----------------------------------

``bool``

Whether ``np.ndarray`` types (or things converted to them) should be
written as structures/Groups if their dtype has fields. A dtype with
fields looks like ``np.dtype([('a', np.uint16), ('b': np.float32)])``.
If an array satisfies this criterion and the option is set, rather than
writing the data as a single Dataset, it is written as a Group with the
contents of the individual fields written as Datasets within it. This
option is set to ``True`` implicitly by ``matlab_compatible``.

make_at_least_2d
----------------

``bool``

Whether all Numpy types (or things converted to them) should be made
into arrays of 2 dimensions if they have less than that or not. This
option is set to ``True`` implicitly by ``matlab_compatible``.

convert_numpy_bytes_to_utf16
----------------------------

``bool``

Whether all ``np.bytes_`` strings (or things converted to it) should be
converted to UTF-16 and written as an array of ``np.uint16`` or not. This
option is set to ``True`` implicitly by ``matlab_compatible``.

convert_numpy_str_to_utf16
--------------------------

``bool``

Whether all ``np.str_`` strings (or things converted to it) should be
converted to UTF-16 and written as an array of ``np.uint16`` if the
strings use no characters outside of the UTF-16 set and the conversion
does not result in any UTF-16 doublets or not. This option is set to
``True`` implicitly by ``matlab_compatible``.

convert_bools_to_uint8
----------------------

``bool``

Whether the ``np.bool_`` type (or things converted to it) should be
converted to ``np.uint8`` (``True`` becomes ``1`` and ``False`` becomes
``0``) or not. If not, then the h5py default of an enum type that is not
MATLAB compatible is used. This option is set to ``True`` implicitly by
``matlab_compatible``.

reverse_dimension_order
-----------------------

``bool``

Whether the dimension order of all arrays should be reversed
(essentially a transpose) or not before writing to the file. This option
is set to ``True`` implicitly by ``matlab_compatible``. This option
needs to be set if one wants an array to end up the same shape when
imported into MATLAB. This option is necessary because Numpy and MATLAB
use opposite dimension ordering schemes, which are C and Fortan schemes
respectively. 2D arrays are stored by row in the C scheme and column in
the Fortran scheme.

store_shape_for_empty
---------------------

``bool``

Whether, for empty arrays, to store the shape of the array (after
transformations) as the Dataset for the object. This option is set to
``True`` implicitly by ``matlab_compatible``.


How Data Is Read from MATLAB MAT Files
======================================

This table gives the MATLAB classes that can be read from a MAT file,
the first version of this package that can read them, and the Python
type they are read as if there is no Python metadata attached to them.

===============  =======  =================================
MATLAB Class     Version  Python Type
===============  =======  =================================
logical          0.1      np.bool\_
single           0.1      np.float32 or np.complex64 [10]_
double           0.1      np.float64 or np.complex128 [10]_
uint8            0.1      np.uint8
uint16           0.1      np.uint16
uint32           0.1      np.uint32
uint64           0.1      np.uint64
int8             0.1      np.int8
int16            0.1      np.int16
int32            0.1      np.int32
int64            0.1      np.int64
char             0.1      np.str\_
struct           0.1      structured np.ndarray
cell             0.1      np.object\_
canonical empty  0.1      ``np.float64([])``
===============  =======  =================================

.. [10] Depends on whether there is a complex part or not.
