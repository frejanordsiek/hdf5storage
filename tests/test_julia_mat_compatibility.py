# Copyright (c) 2014-2021, Freja Nordsiek
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

import os.path
import subprocess
import tempfile

import numpy as np

import pytest

import hdf5storage

from asserts import assert_equal_from_matlab
from make_randoms import dtypes, random_numpy_scalar, random_numpy, \
    random_numpy_shape, random_structured_numpy_array


def julia_command(julia_file, fin, fout):
    subprocess.check_call(['julia', julia_file,
                           fin, fout],
                          stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL)


def test_back_and_forth_julia():
    mat_files = ['to_julia_v7.mat', 'to_julia_v7p3.mat',
                 'julia_v7_to_v7p3.mat', 'julia_v7p3_to_v7p3.mat']

    script_names = ['julia_read_mat.jl']
    for i in range(0, len(script_names)):
        script_names[i] = os.path.join(os.path.dirname(__file__),
                                       script_names[i])

    to_julia = dict()

    # Julia MAT tends to squeeze extra singleton dimensions beyond 2,
    # meaning a (1, 1, 1) goes to (1, 1). In addition, string
    # conversions go on when going back and forth. Thus, string types
    # will be excluded and the minimum length along each dimension will
    # be 2.

    dtypes_exclude = set(('S', 'U'))
    dtypes_to_do = tuple(set(dtypes).difference(dtypes_exclude))

    for dt in dtypes_to_do:
        to_julia[dt] = random_numpy_scalar(dt)
    for dm in (2, 3):
        for dt in dtypes_to_do:
            to_julia[dt + '_array_' + str(dm)] = \
                random_numpy(random_numpy_shape(dm, 6, min_length=2),
                             dt)
    for dt in dtypes_to_do:
        if dt in ('S', 'U'):
            to_julia[dt + '_empty'] = np.array([], dtype=dt + str(6))
        else:
            to_julia[dt + '_empty'] = np.array([], dtype=dt)

    to_julia['float32_nan'] = np.float32(np.NaN)
    to_julia['float32_inf'] = np.float32(np.inf)
    to_julia['float64_nan'] = np.float64(np.NaN)
    to_julia['float64_inf'] = np.float64(-np.inf)

    to_julia['object'] = random_numpy_scalar(
        'object', object_element_dtypes=dtypes_to_do)
    to_julia['object_array_2'] = random_numpy(
        random_numpy_shape(2, 6, min_length=2),
        'object', object_element_dtypes=dtypes_to_do)
    to_julia['object_array_3'] = random_numpy(
        random_numpy_shape(3, 6, min_length=2),
        'object', object_element_dtypes=dtypes_to_do)

    # Julia MAT doesn't seem to read and then write back empty object
    # types.

    #to_julia['object_empty'] = np.array([], dtype='object')

    to_julia['struct'] = random_structured_numpy_array(
        (1,), nondigits_fields=True)
    to_julia['struct_empty'] = random_structured_numpy_array(
        tuple(), nondigits_fields=True)

    # Something goes wrong with 2 dimensional structure arrays that warrants
    # further investigation.

    #to_julia['struct_array_2'] = random_structured_numpy_array(
    #    (3, 5), nondigits_fields=True)

    from_julia_v7_to_v7p3 = dict()
    from_julia_v7p3_to_v7p3 = dict()

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            import scipy.io
            for i in range(0, len(mat_files)):
                mat_files[i] = os.path.join(temp_dir, mat_files[i])
            scipy.io.savemat(file_name=mat_files[0], mdict=to_julia)
            hdf5storage.savemat(file_name=mat_files[1], mdict=to_julia)

            #julia_command(script_names[0], mat_files[0], mat_files[2])
            julia_command(script_names[0], mat_files[1], mat_files[3])

            #hdf5storage.loadmat(file_name=mat_files[2],
            #                    mdict=from_julia_v7_to_v7p3)
            hdf5storage.loadmat(file_name=mat_files[3],
                                mdict=from_julia_v7p3_to_v7p3)
        except:
            pytest.skip('Julia or the MAT package are unavailable '
                        'or their API/s have changed.')

    # Check the results.
    for name in to_julia:
        assert name in from_julia_v7p3_to_v7p3
        #assert name in from_julia_v7_to_v7p3
        assert_equal_from_matlab(from_julia_v7p3_to_v7p3[name],
                                 to_julia[name])
        #assert_equal_from_matlab(from_julia_v7_to_v7p3[name],
        #                         to_julia[name])
