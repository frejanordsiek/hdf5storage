Marshallers
===========

.. currentmodule:: hdf5storage.Marshallers

.. automodule:: hdf5storage.Marshallers


TypeMarshaller
--------------

.. autoclass:: TypeMarshaller
   :members: get_type_string, read, write, write_metadata 
   :show-inheritance:

   .. autoinstanceattribute:: TypeMarshaller.cpython_attributes
      :annotation: = {'CPython.Type'}

   .. autoinstanceattribute:: TypeMarshaller.matlab_attributes
      :annotation: = {'H5PATH'}

   .. autoinstanceattribute:: TypeMarshaller.types
      :annotation: = []

   .. autoinstanceattribute:: TypeMarshaller.cpython_type_strings
      :annotation: = []

   .. autoinstanceattribute:: TypeMarshaller.matlab_classes
      :annotation: = []


NumpyScalarArrayMarshaller
--------------------------

.. autoclass:: NumpyScalarArrayMarshaller
   :members: read, write, write_metadata 
   :show-inheritance:

   .. autoinstanceattribute:: NumpyScalarArrayMarshaller.cpython_attributes
      :annotation: = {'CPython.Type', 'CPython.Shape', 'CPython.Empty',
		      'CPython.numpy.UnderlyingType',
                      'CPython.numpy.Container'}

   .. autoinstanceattribute:: NumpyScalarArrayMarshaller.matlab_attributes
      :annotation: = {'H5PATH', 'MATLAB_class', 'MATLAB_empty',
		      'MATLAB_int_decode'}

   .. autoinstanceattribute:: NumpyScalarArrayMarshaller.types
      :annotation: = [np.ndarray, np.matrix,
                      np.bool_,
                      np.uint8, np.uint16, np.uint32, np.uint64,
                      np.int8, np.int16, np.int32, np.int64,
                      np.float16, np.float32, np.float64,
                      np.complex64, np.complex128,
                      np.bytes_, np.str_]

   .. autoinstanceattribute:: NumpyScalarArrayMarshaller.cpython_type_strings
      :annotation: = ['numpy.ndarray', 'numpy.matrix',
                      'numpy.bool_', 'numpy.uint8', 'numpy.uint16',
                      'numpy.uint32', 'numpy.uint64', 'numpy.int8',
		      'numpy.int16', 'numpy.int32', 'numpy.int64',
                      'numpy.float16', 'numpy.float32', 'numpy.float64',
                      'numpy.complex64', 'numpy.complex128',
                      'numpy.bytes_', 'numpy.str_']

   .. autoinstanceattribute:: NumpyScalarArrayMarshaller.matlab_classes
      :annotation: = ['logical', 'char', 'single', 'double', 'uint8',
	              'uint16', 'uint32', 'uint64', 'int8', 'int16',
                      'int32', 'int64']


PythonScalarMarshaller
----------------------

.. autoclass:: PythonScalarMarshaller
   :members: read, write
   :show-inheritance:

   .. autoinstanceattribute:: PythonScalarMarshaller.cpython_attributes
      :annotation: = {'CPython.Type', 'CPython.Shape', 'CPython.Empty',
		      'CPython.numpy.UnderlyingType',
                      'CPython.numpy.Container'}

   .. autoinstanceattribute:: PythonScalarMarshaller.matlab_attributes
      :annotation: = {'H5PATH', 'MATLAB_class', 'MATLAB_empty',
		      'MATLAB_int_decode'}

   .. autoinstanceattribute:: PythonScalarMarshaller.types
      :annotation: = [bool, int, float, complex]

   .. autoinstanceattribute:: PythonScalarMarshaller.cpython_type_strings
      :annotation: = ['bool', 'int', 'float', 'complex']

   .. autoinstanceattribute:: PythonScalarMarshaller.matlab_classes
      :annotation: = []


PythonStringMarshaller
----------------------

.. autoclass:: PythonStringMarshaller
   :members: read, write
   :show-inheritance:

   .. autoinstanceattribute:: PythonStringMarshaller.cpython_attributes
      :annotation: = {'CPython.Type', 'CPython.Shape', 'CPython.Empty',
		      'CPython.numpy.UnderlyingType',
                      'CPython.numpy.Container'}

   .. autoinstanceattribute:: PythonStringMarshaller.matlab_attributes
      :annotation: = {'H5PATH', 'MATLAB_class', 'MATLAB_empty',
		      'MATLAB_int_decode'}

   .. autoinstanceattribute:: PythonStringMarshaller.types
      :annotation: = [str, bytes, bytearray]

   .. autoinstanceattribute:: PythonStringMarshaller.cpython_type_strings
      :annotation: = ['str', 'bytes', 'bytearray']

   .. autoinstanceattribute:: PythonStringMarshaller.matlab_classes
      :annotation: = []


PythonNoneMarshaller
----------------------

.. autoclass:: PythonNoneMarshaller
   :members: read, write
   :show-inheritance:

   .. autoinstanceattribute:: PythonNoneMarshaller.cpython_attributes
      :annotation: = {'CPython.Type', 'CPython.Shape', 'CPython.Empty',
		      'CPython.numpy.UnderlyingType',
                      'CPython.numpy.Container'}

   .. autoinstanceattribute:: PythonNoneMarshaller.matlab_attributes
      :annotation: = {'H5PATH', 'MATLAB_class', 'MATLAB_empty',
		      'MATLAB_int_decode'}

   .. autoinstanceattribute:: PythonNoneMarshaller.types
      :annotation: = [builtins.NoneType]

   .. autoinstanceattribute:: PythonNoneMarshaller.cpython_type_strings
      :annotation: = ['builtins.NoneType']

   .. autoinstanceattribute:: PythonNoneMarshaller.matlab_classes
      :annotation: = []


PythonDictMarshaller
----------------------

.. autoclass:: PythonDictMarshaller
   :members: read, write, write_metadata
   :show-inheritance:

   .. autoinstanceattribute:: PythonDictMarshaller.cpython_attributes
      :annotation: = {'CPython.Type', 'CPython.Empty'}

   .. autoinstanceattribute:: PythonDictMarshaller.matlab_attributes
      :annotation: = {'H5PATH', 'MATLAB_class', 'MATLAB_empty'}

   .. autoinstanceattribute:: PythonDictMarshaller.types
      :annotation: = [dict]

   .. autoinstanceattribute:: PythonDictMarshaller.cpython_type_strings
      :annotation: = ['dict']

   .. autoinstanceattribute:: PythonDictMarshaller.matlab_classes
      :annotation: = ['struct']

