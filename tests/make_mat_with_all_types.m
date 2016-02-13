% Copyright (c) 2013-2016, Freja Nordsiek
% All rights reserved.
%
% Redistribution and use in source and binary forms, with or without
% modification, are permitted provided that the following conditions are
% met:
%
% 1. Redistributions of source code must retain the above copyright
% notice, this list of conditions and the following disclaimer.
%
% 2. Redistributions in binary form must reproduce the above copyright
% notice, this list of conditions and the following disclaimer in the
% documentation and/or other materials provided with the distribution.
%
% THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
% "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
% LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
% A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
% HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
% SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
% LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
% DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
% THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
% (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
% OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


clear a

% Main types as scalars and arrays.

a.logical = true;

a.uint8 = uint8(2);
a.uint16 = uint16(28);
a.uint32 = uint32(28347394);
a.uint64 = uint64(234392);

a.int8 = int8(-32);
a.int16 = int16(284);
a.int32 = int32(-7394);
a.int64 = int64(2334322);

a.single = single(4.2134e-2);
a.single_complex = single(33.4 + 3i);
a.single_nan = single(NaN);
a.single_inf = single(inf);

a.double = 14.2134e200;
a.double_complex = 8e-30 - 3.2e40i;
a.double_nan = NaN;
a.double_inf = -inf;

a.char = 'p';

a.logical_array = logical([1 0 0 0; 0 1 1 0]);

a.uint8_array = uint8([0 1 3 4; 92 3 2 8]);
a.uint16_array = uint16([0 1; 3 4; 92 3; 2 8]);
a.uint32_array = uint32([0 1 3 4 92 3 2 8]);
a.uint64_array = uint64([0; 1; 3; 4; 92; 3; 2; 8]);

a.int8_array = int8([0 1 3 4; 92 3 2 8]);
a.int16_array = int16([0 1; 3 4; 92 3; 2 8]);
a.int32_array = int32([0 1 3 4 92 3 2 8]);
a.int64_array = int64([0; 1; 3; 4; 92; 3; 2; 8]);

a.single_array = single(rand(4, 9));
a.single_array_complex = single(rand(2,7) + 1i*rand(2,7));

a.double_array = rand(3, 2);
a.double_array_complex = rand(5,2) + 1i*rand(5,2);

a.char_array = ['ivkea'; 'avvai'];
a.char_cell_array = {'v83nv', 'aADvai98v3'};

% Empties of main types.

a.logical_empty = logical([]);
a.uint8_empty = uint8([]);
a.uint16_empty = uint16([]);
a.uint32_empty = uint32([]);
a.uint64_empty = uint64([]);
a.int8_empty = int8([]);
a.int16_empty = int16([]);
a.int32_empty = int32([]);
a.int64_empty = int64([]);
a.single_empty = single([]);
a.double_empty = [];

% Main container types.

a.cell = {5.34+9i};
a.cell_array = {1, [2 3]; 8.3, -[3; 3]; [], 20};
a.cell_empty = {};

a.struct = struct('a', {3.3}, 'bc', {[1 4 5]});
a.struct_empty = struct('vea', {}, 'b', {});
a.struct_array = struct('a', {3.3; 3}, 'avav_Ab', {[1 4 5]; []});

% % Function handles.
% 
% ab = 1:6;
% a.fhandle = @sin;
% a.fhandle_args = @(x, y) x .* cos(y);
% a.fhandle_args_environment = @(m, n) m*(b.*rand(size(b))) + n;
% 
% % Map type.
% 
% a.map_char = containers.Map({'4v', 'u', '2vn'}, {4, uint8(9), 'bafd'});
% a.map_single = containers.Map({single(3), single(38.3), single(2e-3)}, {4, uint8(9), 'bafd'});
% a.map_empty = containers.Map;
% 
% % The categorical type.
% 
% b = {'small', 'medium', 'small', 'medium', 'medium', 'large', 'medium'};
% c = {'small', 'medium', 'large'};
% d = round(2*rand(10,3));
% 
% a.categorical = categorical(b);
% a.categorical_ordinal = categorical(b, c, 'Ordinal', true);
% a.categorical_ordinal_int = categorical(d, 0:2, c, 'Ordinal', true);
% 
% a.categorical_empty = categorical({});
% a.categorical_ordinal_empty = categorical({}, c, 'Ordinal', true);
% a.categorical_ordinal_int_empty = categorical([], 0:2, c, 'Ordinal', true);
% 
% % Tables.
% 
% a.table = readtable('patients.dat');
% a.table_oneentry = a.table(1,:);
% a.table_empty = a.table([], :);
% 
% % Not doing time series yet.

save('types_v7p3.mat','-struct','a','-v7.3')
save('types_v7.mat','-struct','a','-v7')

exit
