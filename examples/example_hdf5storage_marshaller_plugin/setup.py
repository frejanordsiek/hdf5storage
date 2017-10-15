import ez_setup
ez_setup.use_setuptools()

from setuptools import setup

with open('README.rst') as file:
    long_description = file.read()

setup(name='example_hdf5storage_marshaller_plugin',
      version='0.2',
      description='Example marshaller plugin for hdf5storage package.',
      long_description=long_description,
      author='Freja Nordsiek',
      author_email='fnordsie at gmail dt com',
      url='https://github.com/frejanordsiek/hdf5storage/tests/example_hdf5storage_marshaller_plugin',
      py_modules=['example_hdf5storage_marshaller_plugin'],
      entry_points={'hdf5storage.marshallers.plugins':
                    '1.0 = example_hdf5storage_marshaller_plugin:get_marshallers_1p0'},
      license='BSD',
      keywords='hdf5storage',
      zip_safe=True,
      classifiers=[
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3",
          "Development Status :: 3 - Alpha",
          "License :: OSI Approved :: BSD License",
          "Operating System :: OS Independent",
          "Intended Audience :: Developers",
          "Intended Audience :: Information Technology",
          "Intended Audience :: Science/Research",
          "Topic :: Scientific/Engineering",
          "Topic :: Database",
          "Topic :: Software Development :: Libraries :: Python Modules"
          ]
      )
