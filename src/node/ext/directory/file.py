from node.behaviors import DefaultInit
from node.behaviors import Node
from node.behaviors import Reference
from node.ext.directory.interfaces import IFileNode
from node.ext.directory.interfaces import MODE_BINARY
from node.ext.directory.interfaces import MODE_TEXT
from node.ext.directory.location import FSLocation
from node.ext.directory.location import get_fs_path
from node.ext.directory.mode import FSMode
from node.locking import locktree
from plumber import default
from plumber import finalize
from plumber import plumbing
from zope.interface import implementer
import os


@implementer(IFileNode)
class FileNode(Node, FSLocation):
    direct_sync = default(False)

    @property
    def mode(self):
        if not hasattr(self, '_mode'):
            self.mode = MODE_TEXT
        return self._mode

    @default
    @mode.setter
    def mode(self, mode):
        self._mode = mode

    @property
    def data(self):
        if not hasattr(self, '_data'):
            if self.mode == MODE_BINARY:
                self._data = None
            else:
                self._data = ''
            file_path = os.path.join(*get_fs_path(self))
            if os.path.exists(file_path):
                mode = self.mode == MODE_BINARY and 'rb' or 'r'
                with open(file_path, mode) as file:
                    self._data = file.read()
        return self._data

    @default
    @data.setter
    def data(self, data):
        setattr(self, '_changed', True)
        self._data = data

    @property
    def lines(self):
        if self.mode == MODE_BINARY:
            raise RuntimeError('Cannot read lines from binary file.')
        if not self.data:
            return []
        return self.data.split('\n')

    @default
    @lines.setter
    def lines(self, lines):
        if self.mode == MODE_BINARY:
            raise RuntimeError('Cannot write lines to binary file.')
        self.data = '\n'.join(lines)

    @finalize
    @locktree
    def __call__(self):
        file_path = os.path.join(*get_fs_path(self))
        exists = os.path.exists(file_path)
        # Only write file if it's data has changed or not exists yet
        if hasattr(self, '_changed') or not exists:
            write_mode = self.mode == MODE_BINARY and 'wb' or 'w'
            with open(file_path, write_mode) as file:
                file.write(self.data)
                if self.direct_sync:
                    file.flush()
                    os.fsync(file.fileno())
            self._changed = False


@plumbing(
    DefaultInit,
    Reference,  # XXX: remove from default file
    FSMode,
    FileNode)
class File(object):
    pass
