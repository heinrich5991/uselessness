import logging
import os
import sys
import zlib

from logging import info, warning, error
from hashlib import sha1

logging.basicConfig(level=logging.INFO)

def is_executable(path):
	return os.access(path, os.X_OK)

def is_directory(path):
	return os.path.isdir(path)

def parse_commit(data):
	print(data.decode('utf8'))

def parse_blob(data):
	print(data)

def parse_tree(data):
	while len(data) > 0:
		HASH_LEN = 20

		space_index = data.find(b' ')
		nul_index = data.find(b'\0', space_index+1)

		mode = data[0:space_index].decode('ascii') # base 8
		name = data[space_index+1:nul_index].decode('utf-8')
		hash = int.from_bytes(data[nul_index+1:nul_index+1+HASH_LEN], 'big')

		print(mode, "{:040x}".format(hash), name)

		data = data[nul_index+1+HASH_LEN:]


def parse(data, name=None):
	if name != None:
		info("processing file name={}".format(name))

	space_index = data.find(b' ')
	nul_index = data.find(b'\0', space_index+1)

	if space_index == -1 or nul_index == -1:
		error("header format error")

	type_ = data[0:space_index].decode('ascii')
	size = int(data[space_index+1:nul_index].decode('ascii'))

	info("parsing file type={} size={}".format(type_, size))

	data = data[nul_index+1:]

	if len(data) != size:
		error("wrong size in header read_size={} actual_size={}".format(size, len(data)))

	parse_function = 'parse_' + type_

	if parse_function not in globals():
		warning("unknown type={}, skipping file".format(type_))
		return

	parse_function = globals()[parse_function]

	parse_function(data)

def create_tree(path):
	entries = []

	MODE_DEFAULT    = 0o100644
	MODE_EXECUTABLE = 0o100755
	MODE_DIRECTORY  =  0o40000

	for filename in sorted(os.listdir(path), key=lambda x:x.encode('utf-8')):
		if filename == '.git':
			continue

		absolute = os.path.join(path, filename)
		entry = { 'name': filename }
		if is_directory(absolute):
			entry['hash'] = hash('tree', absolute)
			entry['mode'] = MODE_DIRECTORY
		else:
			entry['hash'] = hash('blob', absolute)
			if not is_executable(absolute):
				entry['mode'] = MODE_DEFAULT
			else:
				entry['mode'] = MODE_EXECUTABLE
		entries.append(entry)

	result = []
	for entry in entries:
		result.append(b''.join((
			'{:o}'.format(entry['mode']).encode('ascii'),
			b' ',
			entry['name'].encode('utf-8'),
			b'\0',
			entry['hash'],
		)))

	return b''.join(result)

def create_blob(path):
	with open(path, 'rb') as f:
		return f.read()

def create(type_, path):
	info("creating object type={} path={}".format(type_, path))
	create_function = 'create_' + type_
	if create_function not in globals():
		error("unknown type={}".format(type_))
	create_function = globals()[create_function]
	data = create_function(path)
	data = b''.join((
		type_.encode('ascii'),
		b' ',
		str(len(data)).encode('ascii'),
		b'\0',
		data,
	))
	return data

def hash(type_, path):
	return sha1(create(type_, path)).digest()

if __name__ == '__main__':
#	for filename in sys.argv[1:]:
#		with open(filename, 'rb') as f:
#			parse(zlib.decompress(f.read()), filename)

	parse_tree(create_tree('.'))
	print("{:40x}".format(int.from_bytes(hash('tree', '.'), 'big')))
