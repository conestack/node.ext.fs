from node.behaviors import DictStorage
from node.behaviors import MappingAdopt
from node.behaviors import MappingNode
from node.behaviors import WildcardFactory
from node.compat import IS_PY2
from node.ext.fs.file import File
from node.ext.fs.interfaces import IDirectory
from node.ext.fs.interfaces import IFile
from node.ext.fs.location import FSLocation
from node.ext.fs.location import get_fs_path
from node.ext.fs.mode import FSMode
from node.locking import locktree
from plumber import default
from plumber import finalize
from plumber import plumbing
from zope.interface import implementer
import logging
import os
import shutil


logger = logging.getLogger('node.ext.fs')


def _encode_name(fs_encoding, name):
    name = (
        name.encode(fs_encoding)
        if IS_PY2 and isinstance(name, unicode)
        else name
    )
    return name


@implementer(IDirectory)
class DirectoryStorage(DictStorage, WildcardFactory, FSLocation):
    fs_encoding = default('utf-8')
    default_directory_factory = default(None)
    default_file_factory = default(None)
    ignores = default(list())

    @finalize
    def __init__(
        self,
        name=None,
        parent=None,
        fs_path=None,
        default_directory_factory=None,
        default_file_factory=None,
        factories=None,
        ignores=None
    ):
        self.__name__ = name
        self.__parent__ = parent
        self.fs_path = fs_path
        self.default_directory_factory = (
            default_directory_factory
            if default_directory_factory is not None
            else Directory
        )
        self.default_file_factory = (
            default_file_factory
            if default_file_factory is not None
            else File
        )
        if factories is not None:
            self.factories = factories
        if ignores is not None:
            self.ignores = ignores
        self._deleted_fs_children = list()

    @finalize
    def __getitem__(self, name):
        name = _encode_name(self.fs_encoding, name)
        if name in self._deleted_fs_children:
            raise KeyError(name)
        try:
            return self.storage[name]
        except KeyError:
            filepath = os.path.join(*get_fs_path(self, [name]))
            if not os.path.exists(filepath):
                raise KeyError(name)
            factory = self.factory_for_pattern(name)
            if not factory:
                factory = (
                    self.default_directory_factory
                    if os.path.isdir(filepath)
                    else self.default_file_factory
                )
            # XXX: Check IDirectory/IFile here?
            self[name] = factory(name=name, parent=self)
        return self.storage[name]

    @finalize
    def __setitem__(self, name, value):
        if not name:
            raise KeyError('Empty key not allowed in directories')
        if not IDirectory.providedBy(value) and not IFile.providedBy(value):
            raise ValueError(
                'Incompatible child node. ``IDirectory`` or '
                '``IFile`` must be implemented.'
            )
        name = _encode_name(self.fs_encoding, name)
        if name in self._deleted_fs_children:
            self._deleted_fs_children.remove(name)
        self.storage[name] = value

    @finalize
    def __delitem__(self, name):
        name = _encode_name(self.fs_encoding, name)
        if os.path.exists(os.path.join(*get_fs_path(self, [name]))):
            self._deleted_fs_children.append(name)
        del self.storage[name]

    @finalize
    def __iter__(self):
        try:
            existing = set(os.listdir(os.path.join(*get_fs_path(self))))
        except OSError:
            existing = set()
        existing.update(self.storage)
        return iter(existing
            .difference(self._deleted_fs_children)
            .difference(self.ignores)
        )

    @finalize
    @locktree
    def __call__(self):
        if IDirectory.providedBy(self):
            path = os.path.join(*get_fs_path(self))
            if not os.path.exists(path):
                os.mkdir(path)
            elif not os.path.isdir(path):
                raise KeyError((
                    'Attempt to create directory with name '
                    '"{}" which already exists as file.'
                ).format(self.name))
        while self._deleted_fs_children:
            path = os.path.join(*get_fs_path(
                self,
                [self._deleted_fs_children.pop()]
            ))
            if os.path.exists(path):
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
        for value in self.values():
            if IDirectory.providedBy(value) or IFile.providedBy(value):
                value()


@plumbing(
    MappingAdopt,
    MappingNode,
    FSMode,
    DirectoryStorage)
class Directory(object):
    """Object mapping a file system directory."""
