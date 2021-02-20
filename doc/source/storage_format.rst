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

Also, pickling is not used at all in this format and should not be
added. It is a security risk since pickled data is read through the
interpreter allowing arbitrary code (which could be malicious) to be
executed in the interpreter. One wants to be able to read possibly HDF5
and MAT files from untrusted sources, so pickling is avoided in this
package.


MATLAB File Header
==================

In order for a file to be MATLAB v7.3 MAT file compatible, it must have
a properly formatted file header, or userblock in HDF5 terms. The file
must have a 512 byte userblock, of which 128 bytes are used. The 128
bytes consists of a 116 byte string (spaces pad the end) followed by a
specific 12 byte sequence (magic number). On MATLAB, the 116 byte string, depending on the computer system and the date, looks like ::

    b'MATLAB 7.3 MAT-file, Platform: GLNXA64, Created on: Fri Feb 07 02:29:00 2014 HDF5 schema 1.00 .'

This package just changes the Platform part to ::

    b'hdf5storage VERSION'

Where VERSION is the hdf5storage version.

.. versionchanged:: 0.2

   In the version 0.1.x series, the platform part was
   ``b'CPython A.B.C'`` where A, B, and C are the major, minor, and
   micro version numbers of the Python interpreter (e.g. 3.3.0).

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

========================  =======  ====================================  ======================
Type                      Version  Converted to                          Group or Dataset
========================  =======  ====================================  ======================
bool                      0.1      np.bool\_ or np.uint8 [1]_            Dataset
None                      0.1      ``np.float64([])``                    Dataset
Ellipsis                  0.2      ``np.float64([])``                    Dataset
NotImplemented            0.2      ``np.float64([])``                    Dataset
int [2]_ [3]_             0.1      np.int64 or np.bytes\_ [2]_ [3]_      Dataset
long [3]_ [4]_            0.1      np.int64 or np.bytes\_ [3]_ [4]_      Dataset
float                     0.1      np.float64                            Dataset
complex                   0.1      np.complex128                         Dataset
str                       0.1      np.uint32/16 [5]_                     Dataset
bytes                     0.1      np.bytes\_ or np.uint16 [6]_          Dataset
bytearray                 0.1      np.bytes\_ or np.uint16 [6]_          Dataset
list                      0.1      np.object\_                           Dataset
tuple                     0.1      np.object\_                           Dataset
set                       0.1      np.object\_                           Dataset
frozenset                 0.1      np.object\_                           Dataset
cl.deque                  0.1      np.object\_                           Dataset
cl.ChainMap               0.2      np.object\_                           Dataset
dict [7]_                 0.1                                            Group
cl.OrderedDict [7]_       0.2                                            Group
cl.Counter [7]_           0.2                                            Group
slice                     0.2                                            Group
range                     0.2                                            Group
datetime.timedelta        0.2                                            Group
datetime.timezone         0.2                                            Group
datetime.date             0.2                                            Group
datetime.time             0.2                                            Group
datetime.datetime         0.2                                            Group
fractions.Fraction        0.2                                            Group
np.bool\_                 0.1      not or np.uint8 [1]_                  Dataset
np.void                   0.1                                            Dataset
np.uint8                  0.1                                            Dataset
np.uint16                 0.1                                            Dataset
np.uint32                 0.1                                            Dataset
np.uint64                 0.1                                            Dataset
np.uint8                  0.1                                            Dataset
np.int16                  0.1                                            Dataset
np.int32                  0.1                                            Dataset
np.int64                  0.1                                            Dataset
np.float16 [8]_           0.1                                            Dataset
np.float32                0.1                                            Dataset
np.float64                0.1                                            Dataset
np.complex64              0.1                                            Dataset
np.complex128             0.1                                            Dataset
np.str\_                  0.1      np.uint32/16 [5]_                     Dataset
np.bytes\_                0.1      np.bytes\_ or np.uint16 [6]_          Dataset
np.object\_               0.1                                            Dataset
np.ndarray                0.1      not or Group of contents [9]_         Dataset or Group [9]_
np.matrix [10]_           0.1      np.ndarray                            Dataset
np.chararray              0.1      np.bytes\_ or np.uint16/32 [5]_ [6]_  Dataset
np.recarray               0.1      structured np.ndarray [9]_            Dataset or Group [9]_
np.dtype [11]_            0.2      np.bytes\_ or np.uint16 [6]_          Dataset
========================  =======  ====================================  ======================

.. [1] Depends on the selected options. Always ``np.uint8`` when
       ``convert_bools_to_uint8 == True`` (set implicitly when
       ``matlab_compatible == True``).
.. [2] In Python 2.x with version 0.1.x of this package, it may be read
       back as a ``long`` if it can't fit in the size of an ``int``.
.. [3] Stored as a ``np.int64`` if it is small enough to fit. Otherwise
       its decimal string representation is stored as an ``np.bytes_``
       for hdf5storage >= 0.2 (error in earlier versions).
.. [4] Type only found in Python 2.x. Python 2.x's ``long`` and ``int``
       are unified into a single ``int`` type in Python 3.x. Read as an
       ``int`` in Python 3.x.
.. [5] Depends on the selected options and whether it can be converted
       to UTF-16 without using doublets. If
       ``convert_numpy_str_to_utf16 == True`` (set implicitly when
       ``matlab_compatible == True``) and it can be converted to UTF-16
       without losing any characters that can't be represented in UTF-16
       or using UTF-16 doublets (MATLAB doesn't support them), then it
       is written as ``np.uint16`` in UTF-16 encoding. Otherwise, it is
       stored at ``np.uint32`` in UTF-32 encoding.
.. [6] Depends on the selected options. If
       ``convert_numpy_bytes_to_utf16 == True`` (set implicitly when
       ``matlab_compatible == True``), it will be stored as
       ``np.uint16`` in UTF-16 encoding unless it contains non-ASCII
       characters in which case a ``NotImplementedError`` is raised.
       Otherwise, it is just written as ``np.bytes_``.
.. [7] Stored either as each key-value as their own Dataset or as two
       Datasets, one for keys and one for values. The former is used if
       all keys can be converted to ``str`` in Python 3 or ``unicode``
       in Python 2. Otherwise, the latter format is used.
.. [8] ``np.float16`` are not supported for h5py versions before
       ``2.2``. Version ``2.3`` or higher is required for this package
       since version ``0.2``.
.. [9] If it doesn't have any fields in its dtype or if
       :py:attr:`Options.structured_numpy_ndarray_as_struct` is not set
       and none of its fields are of dtype ``'object'``, it is not
       converted and is written as is as a Dataset. Otherwise, it
       is written as a Group with its the contents of its individual
       fields written as Datasets within the Group having the fields as
       names.
.. [10] Read back as ``np.ndarray`` after the class is removed from NumPy (it
        is pending deprecation).
.. [11] Stored as its string representation converted to ``np.bytes_``.


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

.. note::

   'Python.Type', 'Python.numpy.UnderlyingType', and 'MATLAB_class' are
   all ``np.bytes_``. 'MATLAB_int_decode' is a ``np.int64``.
   'Python.Fields' is a ``np.object_`` array of ``str``.

==================  =============================  ===============================  ==================  =====================
                    Python Attributes                                               MATLAB Attributes
                    --------------------------------------------------------------  -----------------------------------------
Type                Python.Type                    Python.numpy.UnderlyingType      MATLAB_class        MATLAB_int_decode
==================  =============================  ===============================  ==================  =====================
bool                'bool'                         'bool'                           'logical'           1
None                'builtins.NoneType'            'float64'                        'double'
Ellipsis            'builtins.ellipsis'            'float64'                        'double'
NotImplemented      'builtins.NotImplementedType'  'float64'                        'double'
int                 'int'                          'int64' or 'bytes#' [12]_ [13]_  'int64' or 'char'   *not used* or 2 [12]_
long                'long'                         'int64' or 'bytes#' [12]_ [13]_  'int64' or 'char'   *not used* or 2 [12]_
float               'float'                        'float64'                        'double'
complex             'complex'                      'complex128'                     'double'
str                 'str'                          'str#' [13]_                     'char'              2
bytes               'bytes'                        'bytes#' [13]_                   'char'              2
bytearray           'bytearray'                    'bytes#' [13]_                   'char'              2
list                'list'                         'object'                         'cell'
tuple               'tuple'                        'object'                         'cell'
set                 'set'                          'object'                         'cell'
frozenset           'frozenset'                    'object'                         'cell'
cl.deque            'collections.deque'            'object'                         'cell'
cl.ChainMap         'collections.ChainMap'         'object'                         'cell'
dict                'dict'                                                          'struct'
cl.OrderedDict      'collections.OrderedDict'                                       'struct'
cl.Counter          'collections.Counter'                                           'struct'
slice               'slice'                                                         'struct'
range               'range'                                                         'struct'
datetime.timedelta  'datetime.timedelta'                                            'struct'
datetime.timezone   'datetime.timezone'                                             'struct'
datetime.date       'datetime.date'                                                 'struct'
datetime.time       'datetime.time'                                                 'struct'
datetime.datetime   'datetime.datetime'                                             'struct'
fractions.Fraction  'fractions.Fraction'                                            'struct'
np.bool\_           'numpy.bool'                   'bool'                           'logical'           1
np.void             'numpy.void'                   'void#' [13]_
np.uint8            'numpy.uint8'                  'uint8'                          'uint8'
np.uint16           'numpy.uint16'                 'uint16'                         'uint16'
np.uint32           'numpy.uint32'                 'uint32'                         'uint32'
np.uint64           'numpy.uint64'                 'uint64'                         'uint64'
np.uint8            'numpy.int8'                   'int8'                           'int8'
np.int16            'numpy.int16'                  'int16'                          'int16'
np.int32            'numpy.int32'                  'int32'                          'int32'
np.int64            'numpy.int64'                  'int64'                          'int64'
np.float16          'numpy.float16'                'float16'
np.float32          'numpy.float32'                'float32'                        'single'
np.float64          'numpy.float64'                'float64'                        'double'
np.complex64        'numpy.complex64'              'complex64'                      'single'
np.complex128       'numpy.complex128'             'complex128'                     'double'
np.str\_            'numpy.str\_'                  'str#' [13]_                     'char' or 'uint32'  2 or 4 [14]_
np.bytes\_          'numpy.bytes\_'                'bytes#' [13]_                   'char'              2
np.object\_         'numpy.object\_'               'object'                         'cell'
np.ndarray          'numpy.ndarray'                [15]_                            [15]_ [16]_
np.matrix           'numpy.matrix'                 [15]_                            [15]_
np.chararray        'numpy.chararray'              [15]_                            'char' [15]_
np.recarray         'numpy.recarray'               [15]_                            [15]_ [16]_
==================  =============================  ===============================  ==================  =====================

.. [12] The former if it can fit in a ``np.int64`` and the latter if not.
.. [13] '#' is replaced by the number of bits taken up by the string, or
        each string in the case that it is an array of strings. This is 8
        and 32 bits per character for ``np.bytes_`` and ``np.str_``
        respectively.
.. [14] ``2`` if it is stored as ``np.uint16`` or ``4`` if ``np.uint32``.
.. [15] The value that would be put in for a scalar of the same dtype is
       used.
.. [16] If it is structured (its dtype has fields),
        :py:attr:`Options.structured_numpy_ndarray_as_struct` is set,
        and none of its fields are of dtype ``'object'``; it is set to
        ``'struct'`` overriding anything else.


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

.. note::

   The ``np.matrix`` class is marked as pending deprecation. When it is removed,
   objects with this container class will be read back as ``numpy.ndarray``.

Python.Fields
-------------

Python Attribute

``np.object_`` array of ``str``

For ``dict``, ``cl.OrderedDict``, and structured ``np.ndarray`` types
(and those converted to them), an array of the field names of the array
is stored in this Attribute in the proper order. In the HDF5 file, they
are variable length strings.

.. versionchanged:: 0.2
   
   The field names are escaped as described in :ref:`Paths`.

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

numpy array of vlen numpy arrays of ``'S1'``

.. versionchanged:: 0.1.2
   
   Support for this Attribute added. Was deleted upon writing and
   ignored when reading before.

For MATLAB structures, MATLAB sets this field to all of the field names
of the structure. If this Attribute is missing, MATLAB does not seem to
care. Can only be set or read properly for h5py version ``2.3`` and
newer. Trying to set it to a differently formatted array of strings that
older versions of h5py can handle causes an error in MATLAB when the file
is imported, so this package does not set this Attribute at all for h5py
version before ``2.3``. Version ``0.2`` of this package drops support for
h5py ``2.1.x`` and ``2.2.x``.
  
The Attribute is an array of variable length arrays of single character
ASCII numpy strings (vlen of ``'S1'``). If there are two fields named
``'a'`` and ``'cd'``, it is created like so::
  
  fields = ['a', 'cd']
  dt = h5py.special_dtype(vlen=np.dtype('S1'))
  fs = np.empty(shape=(len(fields),), dtype=dt)
  for i, s in enumerate(fields):
      fs[i] = np.array([c.encode('ascii') for c in s],
                       dtype='S1')

Then ``fs`` looks like::
  
  array([array([b'a'], dtype='|S1'),
         array([b'c', b'd'], dtype='|S1']), dtype=object)

.. versionchanged:: 0.2
   
   The field names are escaped as described in :ref:`Paths`.

Python.dict.StoredAs
--------------------

Python Attribute

``np.bytes_`` : ``{b'individual', b'keys_values'}``

.. versionadded:: 0.2

``dict`` like data (includes ``cl.OrderedDict``) can be stored in two
ways. This Attribute specifies which one. It is ``b'individual'`` if
each key-value pair is stored as its own Dataset with the key as the
name. It is set to ``b'key_values'`` if the keys are all stored in their
own Dataset (as a ``tuple``) and the values in another Dataset (as a
``tuple``).

Python.dict.key_str_types
-------------------------

Python Attribute

``np.bytes_``

.. versionadded:: 0.2

A ``dict`` like object (includes ``cl.OrderedDict``) is stored with
each key-value pair as its own Dataset if all the keys are string like
and either are Python 3.x ``str`` or Python 2.x ``unicode`` or can be
converted to those. A key is string like if it is a Python 3.x ``'str``
or ``'bytes'``, a Python 2.x ``'unicode'`` or ``'str'``, a
``np.unicode_``, or a ``np.bytes_``.

This Attribute stores what their original types are. Otherwise, the
exact type would be lost in the conversion to Dataset names. The
Attribute has one character corresponding to each field in the
``'Python.Fields'`` Attribute. The character designates the type. The
characters are

=========  ============================================
Character  Type
=========  ============================================
``b't'``   Python 3.x ``str`` or Python 2.x ``unicode``
``b'b'``   Python 3.x ``bytes`` or Python 2.x ``str``
``b'U'``   ``np.unicode_``
``b'S'``   ``np.bytes_``
=========  ============================================

Python.dict.keys_values_names
-----------------------------

Python Attribute

``np.object_`` array of ``str``

.. versionadded:: 0.2

If ``dict`` like data (includes ``cl.OrderedDict``) is stored with the
keys in their own Dataset and the values in another Dataset (the
``'Python.dict.StoredAs'`` Attribute is ``b'keys_values'``), it stores
the names of the Datasets holding the keys and values respectively (in
that order). It has exactly two elements.

The two ``str`` used are controlled by the :py:class:`Options`
:py:attr:`Options.dict_like_keys_name` and
:py:attr:`Options.dict_like_values_name` respectively.

	 
Storage of Special Types
========================

int and long
------------

Python 2.x has two integer types: a fixed-width ``int`` corresponding
to a C int type, and a variable-width ``long`` for holding arbitrarily
large values. An ``int`` is thus 32 or 64 bits depending on whether the
python interpreter was is a 32 or 64 bit executable. In Python 3.x,
both types are both unified into a single ``int`` type.

Both an ``int`` and a ``long`` written in Python 2.x with version 0.1.x
of this package will be read as a ``int`` in Python 3.x. Python 3.x
always writes as ``int``. Due to this and the fact that the interpreter
in Python 2.x could be using 32-bits ``int``, it is possible that a
value could be read that is too large to fit into ``int``. When that
happens, it read as a ``long`` instead.

.. versionchanged:: 0.2
   
   Added support for writing Python 2.x ``long`` and Python 3.x ``int``
   too big to fit into an ``np.int64``. They are written as their
   string base 10 representation (as a ``np.bytes_``) in such a case.
   In earlier versions, ``NotImplementedError`` is raised if attempted.


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

dict and dict like
------------------

``dict`` like data (``dict``, ``cl.OrderedDict``, and ``cl.Counter``)
are stored either with each key-value as their own Dataset or as two
Datasets, one for keys and one for values. The former is used if all
keys are string like. Keys are converted to ``str``. Otherwise, the
latter format is used. A key is string like if it is a ``'str``, a
``'bytes'``, a ``np.unicode_``, or a ``np.bytes_`` and it an be
converted successfully to ``str``.

When they can't be stored with each key-value pair as their own Dataset,
the keys and values are stored as ``tuple`` in Datasets set by the the
:py:class:`Options`
:py:attr:`Options.dict_like_keys_name` and
:py:attr:`Options.dict_like_values_name` respectively.

If Python metadata is being stored, Attributes are used to indicae how
the data is stored. The Attribute ``'Python.dict.StoredAs'`` is used to
store the method of storage (key-value pairs individually or as keys and
values).

When storing each key-value pair as its own Dataset, the Attribute
``'Python.dict.key_str_types'`` is used to store the type of each key so
that they can be converted back to the right string type.

When storing as keys and values in their own Datasets, the Dataset names
are stored in the Attribute ``'Python.dict.keys_values_names'``.

.. versionchanged:: 0.2
   
   Support added for storing the keys and values as their own Datasets
   instead of each key-value pair as their own Dataset. This feature
   adds the ability to store ``dict`` like data with keys that are not
   ``str`` or can't be converted to them. If writing the values to
   individual datasets, the key names are escaped.

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

Structure np.ndarray
--------------------

When storing structured ``np.ndarray`` (or data that is stored as it)
when :py:attr:`Options.structured_numpy_ndarray_as_struct` is set and
none of its fields are of dtype ``'object'``), it is stored as an HDF5
Group with its contents of its fields written inside of the Group. For
single element data, the fields are written to Datasets inside
the Group. For multi-element data, the elements for each field are
written in :py:attr:`Options.group_for_references` and an HDF5 Reference
array to all of those elements is written as a Dataset under the field
name in the Groups. Othewise, it is written as is as a Dataset that is
an HDF5 COMPOUND type.

.. versionchanged:: 0.2

   Support for field names with null characters and forward slashes
   in them added. The field names are escaped.


.. warning::

   Field names cannot have null characters (``'\x00'``) and, when
   writing as an HDF5 GROUP, forward slashes (``'/'``) in them are not
   supported before version 0.2.


.. warning::

   If it has no elements and
   :py:attr:`Options.structured_numpy_ndarray_as_struct` is set, it
   can't be read back from the file accurately. The dtype for all the
   fields will become 'object' instead of what they originally were.


Stored as dict (slice, range, fractions.Fraction, datetime objects)
-------------------------------------------------------------------

Stored like a ``dict`` of their relevant attributes or keyword arguments.

For ``slice`` and ``range``; this is start, stop, and step. For example,
``slice(3, None, 1)`` is stored the same way as
``{'start': 3, 'stop': None, 'step': 1}``

For :py:class:`fractions.Fraction`, this is numerator and denominator. For
example, ``fractions.Fraction(1, 3)`` is stored the same way as
``{'numerator': 1, 'denominator': 3}``.

For :py:class:`datetime.timedelta`, :py:class:`datetime.timezone`,
:py:class:`datetime.date`, :py:class:`datetime.time`, and
:py:class:`datetime.datetime`; this is a the keyword arguments
required to build them.


collections.ChainMap
--------------------

Stored by storings it :py:meth:`collections.ChainMap.maps` attribute as a
``list``.


np.dtype
--------

Stored in a string representation (just passing it through ``str`` and
wrapping in single quotes if the first character is not ``'('``,
``'['``, or ``'{'``) encoded as UTF-8 in ``np.bytes_``. It is read back
by converting to ``str``, passing through :py:func:`ast.literal_eval`,
and then passing that through the constructor of ``np.dtype``.

.. versionadded:: 0.2


Optional Data Transformations
=============================

Many different data conversions beyond turning most non-Numpy types into
Numpy types, can be done and are controlled by individual settings in
the :py:class:`Options` class. Most are set to fixed values when
``matlab_compatible == True``, which are shown in the table below. The
transfomations are listed below by their option name, other than
`complex_names`, `group_for_references`, `dict_like_keys_name` and
`dict_like_values_name`, which were explained in the previous section.

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
written as structures/Groups if their dtype has fields as long as none
of the fields' dtypes are ``'object'`` in which case this option is
treated as if it were ``True``. A dtype with fields looks like
``np.dtype([('a', np.uint16), ('b': np.float32)])``. If an array
satisfies this criterion and the option is set, rather than writing the
data as a single Dataset, it is written as a Group with the contents of
the individual fields written as Datasets within it. This option is set
to ``True`` implicitly by ``matlab_compatible``.

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

.. warning::

   Only ASCII characters are supported in ``np.bytes_`` when this
   option is set. A ``NotImplementedError`` is raised if any non-ASCII
   characters are present.

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
single           0.1      np.float32 or np.complex64 [17]_
double           0.1      np.float64 or np.complex128 [17]_
uint8            0.1      np.uint8
uint16           0.1      np.uint16
uint32           0.1      np.uint32
uint64           0.1      np.uint64
int8             0.1      np.int8
int16            0.1      np.int16
int32            0.1      np.int32
int64            0.1      np.int64
char             0.1      np.str\_
struct           0.1      structured np.ndarray [18]_
cell             0.1      np.object\_
canonical empty  0.1      ``np.float64([])``
===============  =======  =================================

.. [17] Depends on whether there is a complex part or not.
.. [18] If the ``structs_as_dicts`` option is set then a dict will be used instead.
