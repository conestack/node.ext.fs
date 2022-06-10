from contextlib import contextmanager
from node.behaviors import DefaultInit
from node.behaviors import Node
from node.ext.fs.interfaces import IFileIO
from node.ext.fs.interfaces import IFileNode
from node.ext.fs.interfaces import MODE_BINARY
from node.ext.fs.interfaces import MODE_TEXT
from node.ext.fs.location import FSLocation
from node.ext.fs.location import join_fs_path
from node.ext.fs.mode import FSMode
from node.locking import locktree
from node.utils import UNSET
from plumber import default
from plumber import finalize
from plumber import plumbing
from zope.interface import implementer
import os


@contextmanager
def open_file(path, mode):
    fd = open(path, mode)
    try:
        yield fd
    finally:
        fd.close()


@implementer(IFileIO)
class FileIO(FSLocation):
    mode = default(MODE_TEXT)

    @default
    @property
    def read_fd(self):
        return open_file(
            join_fs_path(self),
            'rb' if self.mode == MODE_BINARY else 'r'
        )

    @default
    @property
    def write_fd(self):
        return open_file(
            join_fs_path(self),
            'wb' if self.mode == MODE_BINARY else 'w'
        )


@implementer(IFileNode)
class FileNode(Node, FileIO):
    direct_sync = default(False)

    @property
    def data(self):
        data = getattr(self, '_data', UNSET)
        if data is UNSET:
            data = b'' if self.mode == MODE_BINARY else ''
            if os.path.exists(join_fs_path(self)):
                with self.read_fd as f:
                    data = f.read()
        return data

    @default
    @data.setter
    def data(self, data):
        self._data = data

    @property
    def lines(self):
        if self.mode == MODE_BINARY:
            raise RuntimeError('Cannot read lines from binary file.')
        data = self.data
        if not data:
            return []
        return data.split('\n')

    @default
    @lines.setter
    def lines(self, lines):
        if self.mode == MODE_BINARY:
            raise RuntimeError('Cannot write lines to binary file.')
        self.data = '\n'.join(lines)

    @finalize
    @locktree
    def __call__(self):
        # Only write file if it's data has changed or not exists yet
        exists = os.path.exists(join_fs_path(self))
        if getattr(self, '_data', UNSET) is not UNSET or not exists:
            with self.write_fd as f:
                f.write(self.data)
                if self.direct_sync:
                    f.flush()
                    os.fsync(f.fileno())
            self._data = UNSET


@plumbing(
    DefaultInit,
    FSMode,
    FileNode)
class File(object):
    pass
