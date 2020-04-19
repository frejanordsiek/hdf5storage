.. currentmodule:: hdf5storage

============
Introduction
============

Getting Started
===============

Most of the functionality that one will use is contained in the main
module ::

    import hdf5storage

Lower level functionality needed mostly for extending this package to
work with more datatypes are in its submodules.

The main functions in this module are :py:func:`write` and
:py:func:`read` which write a single Python variable to an HDF5 file or
read the specified contents at one location in an HDF5 file and convert
to Python types.

HDF5 files are structured much like a Unix filesystem, so everything can
be referenced with a POSIX style path, which look like
``'/pyth/hf'``. Unlike a Windows path, forward slashes (``'/'``) are
used as directory separators instead of backward slashes (``'\\'``) and
the base of the file system is just ``'/'`` instead of something like
``'C:\\'``. In the language of HDF5, what we call directories and files
in filesystems are called groups and datasets.

More information about paths, the supported escapes, etc. can be found
at :ref:`Paths`.

.. versionadded:: 0.2
   
   Ability to escape characters not allowed in Group or Dataset names.

:py:func:`write` has many options for controlling how the data is
stored, and what metadata is stored, but we can ignore that for now. If
we have a variable named ``foo`` that we want to write to an HDF5 file
named ``data.h5``, we would write it by ::

    hdf5storage.write(foo, path='/foo', filename='data.h5')

And then we can read it back from the file with the :py:func:`read`
function, which returns the read data. Here, we will put the data we
read back into the variable ``bar`` ::

    bar = hdf5storage.read(path='/foo', filename='data.h5')

Writing And Reading Several Python Variables at Once
====================================================

To write and read more than one Python variable, one could use
:py:func:`write` and :py:func:`read` for each variable individually.
This can incur a major performance penalty, especially for large HDF5
files, since each call opens and closes the HDF5 file (sometimes more
than once).

Version ``0.1.10`` added a way to do this without incuring this
performance penalty by adding two new functions: :py:func:`writes` and
:py:func:`reads`.

They can write and read more than one Python variable at once, though
they can still work with a single variable. In fact, :py:func:`write`
and :py:func:`read` are now wrappers around them. :py:func:`savemat`
and :py:func:`loadmat` currently use them for the improved performance.

.. versionadded:: 0.1.10
   
   Ability to write and read more than one Python variable at a time
   without opening and closing the HDF5 file each time.

Main Options Controlling Writing/Reading Data
=============================================

There are many individual options that control how data is written and
read to/from file. These can be set by passing an :py:class:`Options`
object to :py:func:`write` and :py:func:`read` by ::

    options = hdf5storage.Options(...)
    hdf5storage.write(... , options=options)
    hdf5storage.read(... , options=options)

or passing the individual keyword arguments used by the
:py:class:`Options` constructor to :py:func:`write` and
:py:func:`read`. The two methods cannot be mixed (the functions will
give precedence to the given :py:class:`Options` object).

.. note::

   Functions in the various submodules only support the
   :py:class:`Options` object method of passing options.

The two main options are :py:attr:`Options.store_python_metadata` and
:py:attr:`Options.matlab_compatible`. A more minor option is
:py:attr:`Options.oned_as`.


.. versionadded:: 0.1.9

   Support for the transparent compression of data has been added. It
   is enabled by default, compressing all python objects resulting in
   HDF5 Datasets larger than 16 KB with the GZIP/Deflate algorithm.


store_python_metadata
---------------------

``bool``

Setting this options causes metadata to be written so that the written
objects can be read back into Python accurately. As HDF5 does not
natively support many Python data types (essentially only Numpy types),
most Python data types have to be converted before being written. If
metadata isn't also written, the data cannot be read back to its
original form and will instead be read back as the Python type most
closely resembling how it is stored, which will be a Numpy type of some
sort.

.. note

   This option is especially important when we consider that when
   ``matlab_compatible == True``, many additional conversions and
   manipulations will be done to the data that cannot be reversed
   without this metadata.

matlab_compatible
-----------------

``bool``

Setting this option causes the writing of HDF5 files be done in a way
compatible with MATLAB v7.3 MAT files. This consists of writing some
file metadata so that MATLAB recognizes the file, adding specific
metadata to every stored object so that MATLAB recognizes them, and
transforming the data to be in the form that MATLAB expects for certain
types (for example, MATLAB expects everything to be at least a 2D array
and strings to be stored in UTF-16 but with no doublets).

.. note::

   There are many individual small options in the :py:class:`Options`
   class that this option sets to specific values. Setting
   ``matlab_compatible`` automatically sets them, while changing their
   values to something else automatically turns ``matlab_compatible``
   off.

action_for_matlab_incompatible
------------------------------

{``'ignore'``, ``'discard'``, ``'error'``}

The action to perform when doing MATLAB compatibility
(``matlab_compatible == True``) but a type
being written is not MATLAB compatible. The actions are to write the
data anyways ('ignore'), don't write the incompatible data ('discard'),
or throw a :py:exc:`exceptions.TypeNotMatlabCompatibleError`
exception. The default is 'error'.

oned_as
-------

{'row', 'column'}

This option is only actually relevant when
``matlab_compatible == True``. MATLAB only supports 2D and higher
dimensionality arrays, but Numpy supports 1D arrays. So, 1D arrays have
to be made 2 dimensional making them either into row vectors or column
vectors. This option sets which they become when imported into MATLAB.


compress
--------

.. versionadded:: 0.1.9

``bool``

Whether to use compression when writing data. Enabled (``True``) by default. See :ref:`Compression` for more information.


Convenience Functions for MATLAB MAT Files
==========================================

Two functions are provided for reading and writing to MATLAB MAT files
in a convenient way. They are :py:func:`savemat` and :py:func:`loadmat`,
which are modelled after the SciPy functions of the same name
(:py:func:`scipy.io.savemat` and :py:func:`scipy.io.loadmat`), which
work with non-HDF5 based MAT files. They take not only the same options,
but dispatch calls automatically to the SciPy versions when instructed
to write to a non-HDF5 based MAT file, or read a MAT file that is not
HDF5 based. SciPy must be installed to take advantage of this
functionality.

:py:func:`savemat` takes a ``dict`` having data (values) and the names
to give each piece of data (keys), and writes them to a MATLAB
compatible MAT file. The `format` keyword sets the MAT file format, with
``'7.3'`` being the HDF5 based format supported by this package and
``'5'`` and ``'4'`` being the non HDF5 based formats supported by
SciPy. If you want the data to be able to be read accurately back into
Python, you should set ``store_python_metadata=True``. Writing a couple
variables to a file looks like ::

    hdf5storage.savemat('data.mat', {'foo': 2.3, 'bar': (1+2j)}, format='7.3', oned_as='column', store_python_metadata=True)

Then, to read variables back, we can either explicitly name the
variables we want ::

    out = hdf5storage.loadmat('data.mat', variable_names=['foo', 'bar'])

or grab all variables by either not giving the `variable_names` option
or setting it to ``None``. ::

    out = hdf5storage.loadmat('data.mat')


Example: Write And Readback Including Different Metadata
========================================================

Making The Data
---------------

Make a ``dict`` containing many different types in it that we want to
store to disk in an HDF5 file. The initialization method depends on
the Python version.

.. versionchanged:: 0.2
   The ``dict`` keys no longer have to all be ``str`` (the unicode
   string type). However, if python metadata is not included, other
   string type keys can get converted to ``str`` when read back or one
   reads back a ``dict`` with two fields, ``keys`` and ``values``,
   holding all the keys and values if at least one key is not a string
   type.

    >>> import numpy as np
    >>> import hdf5storage
    >>> a = {'a': True,
    ...      'b': None,
    ...      'c': 2,
    ...      'd': -3.2,
    ...      'e': (1-2.3j),
    ...      'f': 'hello',
    ...      'g': b'goodbye',
    ...      'h': ['list', 'of', 'stuff', [30, 2.3]],
    ...      'i': np.zeros(shape=(2,), dtype=[('bi', 'uint8')]),
    ...      'j':{'aa': np.bool_(False),
    ...           'bb': np.uint8(4),
    ...           'cc': np.uint32([70, 8]),
    ...           'dd': np.int32([]),
    ...           'ee': np.float32([[3.3], [5.3e3]]),
    ...           'ff': np.complex128([[3.4, 3], [9+2j, 0]]),
    ...           'gg': np.array(['one', 'two', 'three'], dtype='str'),
    ...           'hh': np.bytes_(b'how many?'),
    ...           'ii': np.object_(['text', np.int8([1, -3, 0])])}}

Using No Metadata
-----------------

Write it to a file at the ``'/a'`` directory, but include no Python or
MATLAB metadata. Then, read it back and notice that many objects come
back quite different from what was written. Namely, everything was
converted to Numpy types. This even included the dictionaries which were
converted to structured ``np.ndarray``s. This happens because all
other types (other than ``dict``) must be converted to these types
before being written to the HDF5 file, and without metadata, the
conversion cannot be reversed (while ``dict`` isn't converted, it has
the same form and thus cannot be extracted reversibly).

    >>> hdf5storage.write(data=a, path='/a', filename='data.h5',
    ...                   store_python_metadata=False,
    ...                   matlab_compatible=False)
    >>> hdf5storage.read(path='/a', filename='data.h5')
    array([ (True,
             [],
             2,
             -3.2,
             (1-2.3j),
             b'hello',
             b'goodbye',
             [array(b'list', dtype='|S4'),
              array(b'of', dtype='|S2'),
              array(b'stuff', dtype='|S5'),
              array([array(30), array(2.3)], dtype=object)],
             [(0,), (0,)],
             [(False,
               4,
               array([70,  8], dtype=uint32),
               array([], dtype=int32),
               array([[  3.29999995e+00], [  5.30000000e+03]], dtype=float32),
               array([[ 3.4+0.j,  3.0+0.j], [ 9.0+2.j,  0.0+0.j]]),
               array([111, 110, 101,   0,   0, 116, 119, 111,   0,   0, 116, 104, 114,
                      101, 101], dtype=uint32),
               b'how many?',
               array([array(b'text', dtype='|S4'),
                      array([ 1, -3,  0], dtype=int8)],
                     dtype=object))])], 
          dtype=[('a', '?'),
                 ('b', '<f8', (0,)),
                 ('c', '<i8'),
                 ('d', '<f8'),
                 ('e', '<c16'),
                 ('f', 'S5'),
                 ('g', 'S7'), ('h', 'O', (4,)),
                 ('i', [('bi', 'u1')], (2,)),
                 ('j', [('aa', '?'),
                        ('bb', 'u1'),
                        ('cc', '<u4', (2,)),
                        ('dd', '<i4', (0,)),
                        ('ee', '<f4', (2, 1)),
                        ('ff', '<c16', (2, 2)),
                        ('gg', '<u4', (15,)),
                        ('hh', 'S9'),
                        ('ii', 'O', (2,))],
                  (1,))])


Including Python Metadata
-------------------------

Do the same thing, but now include Python metadata
(``store_python_metadata == True``). This time, everything is read back
the same (or at least, it should) as it was written.

    >>> hdf5storage.write(data=a, path='/a', filename='data_typeinfo.h5',
    ...                   store_python_metadata=True,
    ...                   matlab_compatible=False)
    >>> hdf5storage.read(path='/a', filename='data_typeinfo.h5')
    {'a': True,
     'b': None,
     'c': 2,
     'd': -3.2,
     'e': (1-2.3j),
     'f': 'hello',
     'g': b'goodbye',
     'h': ['list', 'of', 'stuff', [30, 2.3]],
     'i': array([(0,), (0,)], 
          dtype=[('bi', 'u1')]),
     'j': {'aa': False,
      'bb': 4,
      'cc': array([70,  8], dtype=uint32),
      'dd': array([], dtype=int32),
      'ee': array([[  3.29999995e+00],
           [  5.30000000e+03]], dtype=float32),
      'ff': array([[ 3.4+0.j,  3.0+0.j],
           [ 9.0+2.j,  0.0+0.j]]),
      'gg': array(['one', 'two', 'three'], 
          dtype='<U5'),
      'hh': b'how many?',
      'ii': array(['text', array([ 1, -3,  0], dtype=int8)], dtype=object)}}

Including MATLAB Metadata
-------------------------

Do the same thing, but this time including only MATLAB metadata
(``matlab_compatible == True``). This time, the data that is read back
is different from what was written, but in a different way than when no
metadata was used. The biggest differences are that everything was
turned into an at least 2D array, all arrays are transposed, and all
string types got converted to ``numpy.str_``. This happens because
MATLAB can only work with 2D and higher arrays, uses Fortran array
ordering instead of C ordering like Python does, and strings are stored
in a subset of UTF-16 (no doublets) in the version 7.3 MAT files.

    >>> hdf5storage.write(data=a, path='/a', filename='data.mat',
    ...                   store_python_metadata=False,
    ...                   matlab_compatible=True)
    >>> hdf5storage.read(path='/a', filename='data.mat')
    array([ ([[True]],
             [[]],
             [[2]],
             [[-3.2]],
             [[(1-2.3j)]],
             [['hello']],
             [['goodbye']],
             [[array([['list']], dtype='<U4'),
               array([['of']], dtype='<U2'),
               array([['stuff']], dtype='<U5'),
               array([[array([[30]]), array([[ 2.3]])]], dtype=object)]],
             [[(array([[0]], dtype=uint8),)],
              [(array([[0]], dtype=uint8),)]],
             [(array([[False]], dtype=bool),
               array([[4]], dtype=uint8),
               array([[70,  8]], dtype=uint32),
               array([], shape=(1, 0), dtype=int32),
               array([[  3.29999995e+00], [  5.30000000e+03]], dtype=float32),
               array([[ 3.4+0.j,  3.0+0.j], [ 9.0+2.j,  0.0+0.j]]),
               array([['one\x00\x00two\x00\x00three']], dtype='<U15'),
               array([['how many?']], dtype='<U9'),
               array([[array([['text']], dtype='<U4'),
                       array([[ 1, -3,  0]], dtype=int8)]], dtype=object))])], 
          dtype=[('a', '?', (1, 1)),
                 ('b', '<f8', (1, 0)),
                 ('c', '<i8', (1, 1)),
                 ('d', '<f8', (1, 1)),
                 ('e', '<c16', (1, 1)),
                 ('f', '<U5', (1, 1)),
                 ('g', '<U7', (1, 1)),
                 ('h', 'O', (1, 4)),
                 ('i', [('bi', 'u1', (1, 1))], (2, 1)),
                 ('j', [('aa', '?', (1, 1)),
                        ('bb', 'u1', (1, 1)),
                        ('cc', '<u4', (1, 2)),
                        ('dd', '<i4', (1, 0)),
                        ('ee', '<f4', (2, 1)),
                        ('ff', '<c16', (2, 2)),
                        ('gg', '<U15', (1, 1)),
                        ('hh', '<U9', (1, 1)),
                        ('ii', 'O', (1, 2))],
                  (1,))])


Including both Python And MATLAB Metadata
-----------------------------------------

Do the same thing, but now include both Python metadata
(``store_python_metadata == True``) and MATLAB metadata
(``matlab_compatible == True``). This time, everything is read back
the same (or at least, it should) as it was written. The Python metadata
allows the transformations done by making the stored data MATLAB
compatible reversible.

    >>> hdf5storage.write(data=a, path='/a', filename='data_typeinfo.mat',
    ...                   store_python_metadata=True,
    ...                   matlab_compatible=True)
    >>> hdf5storage.read(path='/a', filename='data_typeinfo.mat')
    {'a': True,
     'b': None,
     'c': 2,
     'd': -3.2,
     'e': (1-2.3j),
     'f': 'hello',
     'g': b'goodbye',
     'h': ['list', 'of', 'stuff', [30, 2.3]],
     'i': array([(0,), (0,)], 
          dtype=[('bi', 'u1')]),
     'j': {'aa': False,
      'bb': 4,
      'cc': array([70,  8], dtype=uint32),
      'dd': array([], dtype=int32),
      'ee': array([[  3.29999995e+00],
           [  5.30000000e+03]], dtype=float32),
      'ff': array([[ 3.4+0.j,  3.0+0.j],
           [ 9.0+2.j,  0.0+0.j]]),
      'gg': array(['one', 'two', 'three'], 
          dtype='<U5'),
      'hh': b'how many?',
      'ii': array(['text', array([ 1, -3,  0], dtype=int8)], dtype=object)}}

