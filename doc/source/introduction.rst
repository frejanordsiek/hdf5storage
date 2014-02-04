============
Introduction
============

Example: Write And Readback Including Different Metadata
========================================================

Making The Data
---------------

Make a ``dict`` containing many different types in it that we want to
store to disk in an HDF5 file.

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
    ...      'i':{'aa': np.bool_(False),
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

Write it to a file at the root directory, but include no Python or
MATLAB metadata. Then, read it back and notice that many objects come
back quite different from what was written. Namely, everything but
``dict`` types were converted to Numpy types. This happens because all
other types must be converted to these types before being written to the
HDF5 file, and without metadata, the conversion cannot be reversed.

    >>> hdf5storage.write(data=a, name='/', filename='data.h5',
    ...                   store_type_information=False,
    ...                   matlab_compatible=False)
    >>> hdf5storage.read(name='/', filename='data.h5')
    {'a': array(True, dtype=bool),
     'b': array([], dtype=float64),
     'c': array(2),
     'd': array(-3.2),
     'e': array((1-2.3j)),
     'f': array(b'hello', 
          dtype='|S5'),
     'g': array(b'goodbye', 
          dtype='|S7'),
     'h': array([array(b'list', 
          dtype='|S4'),
           array(b'of', 
          dtype='|S2'),
           array(b'stuff', 
          dtype='|S5'),
           array([array(30), array(2.3)], dtype=object)], dtype=object),
     'i': {'aa': array(False, dtype=bool),
      'bb': array(4, dtype=uint8),
      'cc': array([70,  8], dtype=uint32),
      'dd': array([], dtype=int32),
      'ee': array([[  3.29999995e+00],
           [  5.30000000e+03]], dtype=float32),
      'ff': array([[ 3.4+0.j,  3.0+0.j],
           [ 9.0+2.j,  0.0+0.j]]),
      'gg': array([111, 110, 101,   0,   0, 116, 119, 111,   0,   0, 116, 104, 114,
           101, 101], dtype=uint32),
      'hh': array(b'how many?', 
          dtype='|S9'),
      'ii': array([array(b'text', 
          dtype='|S4'), array([ 1, -3,  0], dtype=int8)], dtype=object)}}


Including Python Metadata
-------------------------

Do the same thing, but now include Python metadata
(``store_type_information == True``). This time, everything is read back
the same (or at least, it should) as it was written.

    >>> hdf5storage.write(data=a, name='/', filename='data_typeinfo.h5',
    ...                   store_type_information=True,
    ...                   matlab_compatible=False)
    >>> hdf5storage.read(name='/', filename='data_typeinfo.h5')
    {'a': True,
     'b': None,
     'c': 2,
     'd': -3.2,
     'e': (1-2.3j),
     'f': 'hello',
     'g': b'goodbye',
     'h': ['list', 'of', 'stuff', [30, 2.3]],
     'i': {'aa': False,
      'bb': 4,
      'cc': array([70,  8], dtype=uint32),
      'dd': array([], dtype=int32),
      'ee': array([[  3.29999995e+00],
           [  5.30000000e+03]], dtype=float32),
      'ff': array([[ 3.4+0.j,  9.0+2.j],
           [ 3.0+0.j,  0.0+0.j]]),
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

    >>> hdf5storage.write(data=a, name='/', filename='data.mat',
    ...                   store_type_information=False,
    ...                   matlab_compatible=True)
    >>> hdf5storage.read(name='/', filename='data.mat')
    {'a': array([[ True]], dtype=bool),
     'b': array([], shape=(1, 0), dtype=float64),
     'c': array([[2]]),
     'd': array([[-3.2]]),
     'e': array([[ 1.-2.3j]]),
     'f': array([['hello']], 
          dtype='<U5'),
     'g': array([['goodbye']], 
          dtype='<U7'),
     'h': array([[array([['list']], 
          dtype='<U4'),
            array([['of']], 
          dtype='<U2'),
            array([['stuff']], 
          dtype='<U5'),
            array([[array([[30]]), array([[ 2.3]])]], dtype=object)]], dtype=object),
     'i': {'aa': array([[False]], dtype=bool),
      'bb': array([[4]], dtype=uint8),
      'cc': array([[70,  8]], dtype=uint32),
      'dd': array([], shape=(1, 0), dtype=int32),
      'ee': array([[  3.29999995e+00],
           [  5.30000000e+03]], dtype=float32),
      'ff': array([[ 3.4+0.j,  3.0+0.j],
           [ 9.0+2.j,  0.0+0.j]]),
      'gg': array([['one\x00\x00two\x00\x00three']], 
          dtype='<U15'),
      'hh': array([['how many?']], 
          dtype='<U9'),
      'ii': array([[array([['text']], 
          dtype='<U4'),
            array([[ 1, -3,  0]], dtype=int8)]], dtype=object)}}

Including both Python And MATLAB Metadata
-----------------------------------------

Do the same thing, but now include both Python metadata
(``store_type_information == True``) and MATLAB metadata
(``matlab_compatible == True``). This time, everything is read back
the same (or at least, it should) as it was written. The Python metadata
allows the transformations done by making the stored data MATLAB
compatible reversible.

    >>> hdf5storage.write(data=a, name='/', filename='data_typeinfo.mat',
    ...                   store_type_information=True,
    ...                   matlab_compatible=True)
    >>> hdf5storage.read(name='/', filename='data_typeinfo.mat')
    {'a': True,
     'b': None,
     'c': 2,
     'd': -3.2,
     'e': (1-2.3j),
     'f': 'hello',
     'g': b'goodbye',
     'h': ['list', 'of', 'stuff', [30, 2.3]],
     'i': {'aa': False,
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

