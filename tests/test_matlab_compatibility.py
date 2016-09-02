# Copyright (c) 2014-2016, Freja Nordsiek
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

import os
import os.path
import subprocess

from nose.plugins.skip import SkipTest

import hdf5storage

from asserts import *

mat_files = ['types_v7p3.mat', 'types_v7.mat',
             'python_v7p3.mat', 'python_v7.mat']
for i in range(0, len(mat_files)):
    mat_files[i] = os.path.join(os.path.dirname(__file__), mat_files[i])

script_names = ['make_mat_with_all_types.m', 'read_write_mat.m']
for i in range(0, len(script_names)):
    script_names[i] = os.path.join(os.path.dirname(__file__),
                                   script_names[i])

types_v7 = dict()
types_v7p3 = dict()
python_v7 = dict()
python_v7p3 = dict()


# Have a flag for whether matlab was found and run successfully or not,
# so tests can be skipped if not.
ran_matlab_successful = [False]


def setup_module():
    teardown_module()
    try:
        import scipy.io
        matlab_command = "run('" + script_names[0] + "')"
        subprocess.check_call(['matlab', '-nosplash', '-nodesktop',
                              '-nojvm', '-r', matlab_command])
        scipy.io.loadmat(file_name=mat_files[1], mdict=types_v7)
        hdf5storage.loadmat(file_name=mat_files[0], mdict=types_v7p3)

        hdf5storage.savemat(file_name=mat_files[2], mdict=types_v7p3)
        matlab_command = "run('" + script_names[1] + "')"
        subprocess.check_call(['matlab', '-nosplash', '-nodesktop',
                              '-nojvm', '-r', matlab_command])
        scipy.io.loadmat(file_name=mat_files[3], mdict=python_v7)
        hdf5storage.loadmat(file_name=mat_files[2], mdict=python_v7p3)
    except:
        pass
    else:
        ran_matlab_successful[0] = True


def teardown_module():
    for name in mat_files:
        if os.path.exists(name):
            os.remove(name)


def test_read_from_matlab():
    if not ran_matlab_successful[0]:
        raise SkipTest
    for k in (set(types_v7.keys()) - set(['__version__', '__header__', \
            '__globals__'])):
        yield check_variable_from_matlab, k


def test_to_matlab_back():
    if not ran_matlab_successful[0]:
        raise SkipTest
    for k in set(types_v7p3.keys()):
        yield check_variable_to_matlab_back, k


def check_variable_from_matlab(name):
    assert_equal_from_matlab(types_v7p3[name], types_v7[name])


def check_variable_to_matlab_back(name):
    assert_equal_from_matlab(python_v7p3[name], types_v7[name])
