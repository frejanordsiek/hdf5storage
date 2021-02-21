hdf5storage.Marshallers
=======================

.. currentmodule:: hdf5storage.Marshallers

.. automodule:: hdf5storage.Marshallers

.. autosummary::

   write_object_array
   read_object_array
   TypeMarshaller
   NumpyScalarArrayMarshaller
   PythonScalarMarshaller
   PythonStringMarshaller
   PythonNoneMarshaller
   PythonDictMarshaller
   PythonListMarshaller
   PythonTupleSetDequeMarshaller


write_object_array
------------------

.. autofunction:: write_object_array


read_object_array
------------------

.. autofunction:: read_object_array


TypeMarshaller
--------------

.. autoclass:: TypeMarshaller
   :members: get_type_string, read, write, write_metadata 
   :show-inheritance:

   .. autoattribute:: TypeMarshaller.python_attributes
      :annotation: = {'Python.Type'}

   .. autoattribute:: TypeMarshaller.matlab_attributes
      :annotation: = {'H5PATH'}

   .. autoattribute:: TypeMarshaller.types
      :annotation: = []

   .. autoattribute:: TypeMarshaller.python_type_strings
      :annotation: = []

   .. autoattribute:: TypeMarshaller.matlab_classes
      :annotation: = []


NumpyScalarArrayMarshaller
--------------------------

.. autoclass:: NumpyScalarArrayMarshaller
   :members: read, write, write_metadata 
   :show-inheritance:

   .. autoattribute:: NumpyScalarArrayMarshaller.python_attributes
      :annotation: = {'Python.Type', 'Python.Shape', 'Python.Empty',
		      'Python.numpy.UnderlyingType',
                      'Python.numpy.Container', 'Python.Fields'}

   .. autoattribute:: NumpyScalarArrayMarshaller.matlab_attributes
      :annotation: = {'H5PATH', 'MATLAB_class', 'MATLAB_empty',
		      'MATLAB_int_decode', 'MATLAB_fields'}

   .. autoattribute:: NumpyScalarArrayMarshaller.types
      :annotation: = [np.ndarray, np.matrix,
                      np.chararray, np.core.records.recarray,
                      np.bool_, np.void,
                      np.uint8, np.uint16, np.uint32, np.uint64,
                      np.int8, np.int16, np.int32, np.int64,
                      np.float16, np.float32, np.float64,
                      np.complex64, np.complex128,
                      np.bytes_, np.str_, np.object_]

   .. autoattribute:: NumpyScalarArrayMarshaller.python_type_strings
      :annotation: = ['numpy.ndarray', 'numpy.matrix',
                      'numpy.chararray', 'numpy.recarray',
                      'numpy.bool_', 'numpy.void',
                      'numpy.uint8', 'numpy.uint16',
                      'numpy.uint32', 'numpy.uint64', 'numpy.int8',
		      'numpy.int16', 'numpy.int32', 'numpy.int64',
                      'numpy.float16', 'numpy.float32', 'numpy.float64',
                      'numpy.complex64', 'numpy.complex128',
                      'numpy.bytes_', 'numpy.str_', 'numpy.object_']

   .. autoattribute:: NumpyScalarArrayMarshaller.matlab_classes
      :annotation: = ['logical', 'char', 'single', 'double', 'uint8',
	              'uint16', 'uint32', 'uint64', 'int8', 'int16',
                      'int32', 'int64', 'cell', 'canonical empty']


PythonScalarMarshaller
----------------------

.. autoclass:: PythonScalarMarshaller
   :members: read, write
   :show-inheritance:

   .. autoattribute:: PythonScalarMarshaller.python_attributes
      :annotation: = {'Python.Type', 'Python.Shape', 'Python.Empty',
		      'Python.numpy.UnderlyingType',
                      'Python.numpy.Container', 'Python.Fields'}

   .. autoattribute:: PythonScalarMarshaller.matlab_attributes
      :annotation: = {'H5PATH', 'MATLAB_class', 'MATLAB_empty',
		      'MATLAB_int_decode'}

   .. autoattribute:: PythonScalarMarshaller.types
      :annotation: = [bool, int, float, complex]

   .. autoattribute:: PythonScalarMarshaller.python_type_strings
      :annotation: = ['bool', 'int', 'float', 'complex']

   .. autoattribute:: PythonScalarMarshaller.matlab_classes
      :annotation: = []


PythonStringMarshaller
----------------------

.. autoclass:: PythonStringMarshaller
   :members: read, write
   :show-inheritance:

   .. autoattribute:: PythonStringMarshaller.python_attributes
      :annotation: = {'Python.Type', 'Python.Shape', 'Python.Empty',
		      'Python.numpy.UnderlyingType',
                      'Python.numpy.Container', 'Python.Fields'}

   .. autoattribute:: PythonStringMarshaller.matlab_attributes
      :annotation: = {'H5PATH', 'MATLAB_class', 'MATLAB_empty',
		      'MATLAB_int_decode'}

   .. autoattribute:: PythonStringMarshaller.types
      :annotation: = [str, bytes, bytearray]

   .. autoattribute:: PythonStringMarshaller.python_type_strings
      :annotation: = ['str', 'bytes', 'bytearray']

   .. autoattribute:: PythonStringMarshaller.matlab_classes
      :annotation: = []


PythonNoneMarshaller
--------------------

.. autoclass:: PythonNoneMarshaller
   :members: read, write
   :show-inheritance:

   .. autoattribute:: PythonNoneMarshaller.python_attributes
      :annotation: = {'Python.Type', 'Python.Shape', 'Python.Empty',
		      'Python.numpy.UnderlyingType',
                      'Python.numpy.Container', 'Python.Fields'}

   .. autoattribute:: PythonNoneMarshaller.matlab_attributes
      :annotation: = {'H5PATH', 'MATLAB_class', 'MATLAB_empty',
		      'MATLAB_int_decode'}

   .. autoattribute:: PythonNoneMarshaller.types
      :annotation: = [builtins.NoneType]

   .. autoattribute:: PythonNoneMarshaller.python_type_strings
      :annotation: = ['builtins.NoneType']

   .. autoattribute:: PythonNoneMarshaller.matlab_classes
      :annotation: = []


PythonDictMarshaller
--------------------

.. autoclass:: PythonDictMarshaller
   :members: read, write, write_metadata
   :show-inheritance:

   .. autoattribute:: PythonDictMarshaller.python_attributes
      :annotation: = {'Python.Type', 'Python.Fields'}

   .. autoattribute:: PythonDictMarshaller.matlab_attributes
      :annotation: = {'H5PATH', 'MATLAB_class', 'MATLAB_fields'}

   .. autoattribute:: PythonDictMarshaller.types
      :annotation: = [dict]

   .. autoattribute:: PythonDictMarshaller.python_type_strings
      :annotation: = ['dict']

   .. autoattribute:: PythonDictMarshaller.matlab_classes
      :annotation: = []


PythonListMarshaller
--------------------

.. autoclass:: PythonListMarshaller
   :members: read, write
   :show-inheritance:

   .. autoattribute:: PythonListMarshaller.python_attributes
      :annotation: = {'Python.Type', 'Python.Shape', 'Python.Empty',
		      'Python.numpy.UnderlyingType',
                      'Python.numpy.Container', 'Python.Fields'}

   .. autoattribute:: PythonListMarshaller.matlab_attributes
      :annotation: = {'H5PATH', 'MATLAB_class', 'MATLAB_empty',
		      'MATLAB_int_decode'}

   .. autoattribute:: PythonListMarshaller.types
      :annotation: = [list]

   .. autoattribute:: PythonListMarshaller.python_type_strings
      :annotation: = ['list']

   .. autoattribute:: PythonListMarshaller.matlab_classes
      :annotation: = []


PythonTupleSetDequeMarshaller
-----------------------------

.. autoclass:: PythonTupleSetDequeMarshaller
   :members: read, write
   :show-inheritance:

   .. autoattribute:: PythonTupleSetDequeMarshaller.python_attributes
      :annotation: = {'Python.Type', 'Python.Shape', 'Python.Empty',
		      'Python.numpy.UnderlyingType',
                      'Python.numpy.Container', 'Python.Fields'}

   .. autoattribute:: PythonTupleSetDequeMarshaller.matlab_attributes
      :annotation: = {'H5PATH', 'MATLAB_class', 'MATLAB_empty',
		      'MATLAB_int_decode'}

   .. autoattribute:: PythonTupleSetDequeMarshaller.types
      :annotation: = [tuple, set, frozenset, collections.deque]

   .. autoattribute:: PythonTupleSetDequeMarshaller.python_type_strings
      :annotation: = ['tuple', 'set', 'frozenset', 'collections.deque']

   .. autoattribute:: PythonTupleSetDequeMarshaller.matlab_classes
      :annotation: = []

