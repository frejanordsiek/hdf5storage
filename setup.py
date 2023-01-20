import sys

if sys.hexversion < 0x2060000:
    raise NotImplementedError('Python < 2.6 not supported.')

# Try to import setuptools and if that fails, use ez_setup to get it
# (fallback for old versions of python if it isn't installed).
try:
    from setuptools import setup
except:
    try:
        import ez_setup
        ez_setup.use_setuptools()
    except:
        pass
    from setuptools import setup


# If distutils.version.StrictVersion no longer exists, setuptools is
# also a dependency to get version parsing.
try:
    from distutils.version import StrictVersion
    extra_deps = []
except:
    extra_deps = ['setuptools']



with open('README.rst') as file:
    long_description = file.read()

setup(name='hdf5storage',
      version='0.1.19',
      description='Utilities to read/write Python types to/from HDF5 files, including MATLAB v7.3 MAT files.',
      long_description=long_description,
      author='Freja Nordsiek',
      author_email='fnordsie@posteo.net',
      url='https://github.com/frejanordsiek/hdf5storage',
      packages=['hdf5storage'],
      install_requires=["numpy < 1.12.0 ; python_version == '2.6'",
                        "numpy ; python_version == '2.7'",
                        "numpy<1.6.0 ; python_version == '3.0'",
                        "numpy<1.8.0 ; python_version == '3.1'",
                        "numpy<1.12.0 ; python_version == '3.2'",
                        "numpy<1.12.0 ; python_version == '3.3'",
                        "numpy ; python_version >= '3.4'",
                        "h5py>=2.1 ; python_version == '2.6'",
                        "h5py>=2.1 ; python_version == '2.7'",
                        "h5py>=2.1,<2.4 ; python_version == '3.0'",
                        "h5py>=2.1,<2.7 ; python_version == '3.1'",
                        "h5py>=2.1,<2.7 ; python_version == '3.2'",
                        "h5py>=2.1 ; python_version >= '3.3'"] + extra_deps,
      license='BSD',
      keywords='hdf5 matlab',
      classifiers=[
          "Programming Language :: Python :: 2.6",
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
          ],
      test_suite='nose.collector',
      tests_require='nose>=1.0'
      )
