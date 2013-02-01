import logging
import os
import sys
import zlib

from logging import debug, info, warning, error
from hashlib import sha1

#logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)

def is_executable(path):
	return os.access(path, os.X_OK)

def is_directory(path):
	return os.path.isdir(path)

def is_symlink(path):
	return os.path.islink(path)

def git_hash(data):
	return sha1(data).digest()

def hash_hex(byte_hash):
	return ("{:0%dx}"%(len(byte_hash)*2)).format(int.from_bytes(byte_hash, 'big'))

class GitObject:
	PATHTYPE_GITOBJECT            = 1 # filename to a git file
	PATHTYPE_GITOBJECT_RAW        = 2 # contents of a git file
	PATHTYPE_REALWORLD            = 3 # filename to an actual file
	PATHTYPE_REALWORLD_RAW        = 4 # contents of an actual file
	PATHTYPE_GITOBJECT_UNCOMP     = 5 # filename to an decompressed git file
	PATHTYPE_GITOBJECT_UNCOMP_RAW = 6 # contents of an decompressed git file

	def __init__(self, type_, path__data=None, pathtype=PATHTYPE_REALWORLD):
		debug("gitobj constr self={!r} type={!r} path__data={!r} pathtype={!r}".format(self, type_, path__data, pathtype))
		self.type_ = type_
		if path__data is not None:
			if pathtype == self.PATHTYPE_GITOBJECT: # normal (= compressed) git file
				self._construct_from_git_comp(path__data)
			elif pathtype == self.PATHTYPE_GITOBJECT_RAW:
				self._construct_from_git_comp_raw(path__data)
			elif pathtype == self.PATHTYPE_REALWORLD: # actual file
				self._construct_from_real(path__data)
			elif pathtype == self.PATHTYPE_REALWORLD_RAW:
				self._construct_from_real_raw(path__data)
			elif pathtype == self.PATHTYPE_GITOBJECT_UNCOMP: # decompressed git file
				self._construct_from_git(path__data)
			elif pathtype == self.PATHTYPE_GITOBJECT_UNCOMP_RAW:
				self._construct_from_git_raw(path__data)
			else:
				error("unknown pathtype={}".format(pathtype))
		else:
			self._construct_empty()

	def _construct_empty(self):
		self._construct_from_real_raw(b'')
		self.source = ('ce', None)

	def _construct_from_git(self, path):
		with open(path, 'rb') as f:
			self._construct_from_git_raw(f.read())
		self.source = ('cfg', path)

	def _construct_from_real(self, path):
		with open(path, 'rb') as f:
			self._construct_from_real_raw(f.read())
		self.source = ('cfr', path)

	def _construct_from_git_comp(self, path):
		with open(path, 'rb') as f:
			self._construct_from_git_comp_raw(f.read())
		self.source = ('cfgc', path)

	def _construct_from_git_comp_raw(self, data):
		self._construct_from_git_raw(zlib.decompress(data))
		self.source = ('cfgcr', None)

	def _construct_from_git_raw(self, data):
		space_index = data.find(b' ')
		nul_index = data.find(b'\0', space_index+1)

		if space_index == -1 or nul_index == -1:
			error("header format error")

		type_ = data[0:space_index].decode('ascii')
		if type_ != self.type_:
			error("wrong type")

		size = int(data[space_index+1:nul_index].decode('ascii'))

		info("parsing file type={} size={}".format(type_, size))

		data = data[nul_index+1:]

		if len(data) != size:
			error("wrong size in header read_size={} actual_size={}".format(size, len(data)))

		self._construct_from_real_raw(data)
		self.source = ('cfgr', None)

	def _construct_from_real_raw(self, data):
		self.data = data
		self.source = ('cfrr', None)

	def print(self):
		print(self.data)

	@property
	def raw(self):
		return b''.join((
			self.type_.encode('ascii'),
			b' ',
			str(len(self.data)).encode('ascii'),
			b'\0',
			self.data
		))

	@property
	def hash(self):
		return git_hash(self.raw)


class GitTree(GitObject):
	MODE_DEFAULT    = 0o100644
	MODE_EXECUTABLE = 0o100755
	MODE_SYMLINK    = 0o120000
	MODE_DIRECTORY  =  0o40000

	MODE_CHOICES = (MODE_DIRECTORY, MODE_EXECUTABLE, MODE_DIRECTORY)

	def __init__(self, *args, **kwargs):
		debug("gittree constr self={!r} args={!r} kwargs={!r}".format(self, args, kwargs))
		super().__init__('tree', *args, **kwargs)

	def _construct_empty(self):
		debug("cfe")
		self.entries = {}

	def _construct_from_git_raw(self, data):
		debug("cfgr")
		self._construct_empty()
		while len(data) > 0:
			HASH_LEN = 20

			space_index = data.find(b' ')
			nul_index = data.find(b'\0', space_index+1)

			mode = int(data[0:space_index].decode('ascii'), 8), # base 8
			name = data[space_index+1:nul_index].decode('utf-8'),
			hash = data[nul_index+1:nul_index+1+HASH_LEN],

			self.entries[name] = {'mode': mode, 'hash': hash}

			data = data[nul_index+1+HASH_LEN:]

	def _construct_from_real_raw(self, data):
		debug("cfrr")
		raise TypeError("Logic error: There is no way to provide a raw directory")

	def _construct_from_real(self, path):
		debug("cfr")
		self._construct_empty()

		for filename in os.listdir(path):
			if filename == '.git':
				continue

			absolute = os.path.join(path, filename)
			entry = {}
			if is_directory(absolute):
				entry['hash'] = GitTree(absolute).hash
				entry['mode'] = self.MODE_DIRECTORY
			elif is_symlink(absolute):
				entry['hash'] = GitBlob('Documentation/RelNotes/1.8.2.txt'.encode('utf-8'), self.PATHTYPE_REALWORLD_RAW).hash
				entry['mode'] = self.MODE_SYMLINK
			else:
				entry['hash'] = GitBlob(absolute).hash
				if not is_executable(absolute):
					entry['mode'] = self.MODE_DEFAULT
				else:
					entry['mode'] = self.MODE_EXECUTABLE
			self.entries[filename] = entry

	@property
	def data(self):
		result = []
		def get_key(name):
			# Tree entries are sorted by the byte sequence that comprises
			# the entry name. However, for the purposes of the sort
			# comparison, entries for tree objects are compared as if the
			# entry name byte sequence has a trailing ASCII '/' (0x2f).
			#
			# Taken from http://git.rsbx.net/Documents/Git_Data_Formats.txt
			if self.entries[name]['mode'] == self.MODE_DIRECTORY:
				return name.encode('utf-8') + b'/'
			else:
				return name.encode('utf-8')
		for name in sorted(self.entries.keys(), key=get_key):

			entry = self.entries[name]
			result.append(b''.join((
				'{:o}'.format(entry['mode']).encode('ascii'),
				b' ',
				name.encode('utf-8'),
				b'\0',
				entry['hash'],
			)))

		return b''.join(result)

	def print(self):
		for name in sorted(self.entries.keys()):
			entry = self.entries[name]
			print("{:06o} {:040x} {}".format(entry['mode'], int.from_bytes(entry['hash'], 'big'), name))

class GitCommit(GitObject):
	def __init__(self, *args, **kwargs):
		super().__init__('commit', *args, **kwargs)

	def _construct_from_real_raw(self, data):
		self.data = data.decode('utf-8')

class GitBlob(GitObject):
	def __init__(self, *args, **kwargs):
		super().__init__('blob', *args, **kwargs)

if __name__ == '__main__':
	for filename in sys.argv[1:]:
		with open(filename, 'rb') as f:
			parse(zlib.decompress(f.read()), filename)

	t = GitTree('.')
	#t.print()
	print(hash_hex(t.hash))
	#sys.stdout.buffer.write(t.raw)

