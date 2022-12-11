from contextlib import contextmanager
from node.behaviors import DictStorage
from node.behaviors import MappingAdopt
from node.behaviors import MappingNode
from node.behaviors import WildcardFactory
from node.compat import IS_PY2
from node.ext.fs.file import File
from node.ext.fs.interfaces import IDirectory
from node.ext.fs.interfaces import IFile
from node.ext.fs.location import FSLocation
from node.ext.fs.location import get_fs_name
from node.ext.fs.location import join_fs_path
from node.ext.fs.mode import FSMode
from node.locking import locktree
from plumber import default
from plumber import finalize
from plumber import plumbing
from zope.interface import implementer
import inspect
import os
import shutil
import threading


def _encode_name(fs_encoding, name):
    name = (
        name.encode(fs_encoding)
        if IS_PY2 and isinstance(name, unicode)
        else name
    )
    return name


class DirectoryContext(threading.local):
    validate_child = True


_directory_context = DirectoryContext()


@contextmanager
def _skip_validate_child():
    """Context manager to skip validation when setting directory child."""
    _directory_context.validate_child = False
    try:
        yield
    finally:
        _directory_context.validate_child = True


@implementer(IDirectory)
class DirectoryStorage(DictStorage, WildcardFactory, FSLocation):
    fs_encoding = default('utf-8')
    default_file_factory = default(File)
    ignores = default(list())

    @default
    @property
    def default_directory_factory(self):
        return Directory

    @finalize
    def __init__(
        self,
        name=None,
        parent=None,
        fs_path=None,
        factories=None,
        ignores=None
    ):
        self.__name__ = name
        self.__parent__ = parent
        self.fs_path = fs_path
        if factories is not None:
            self.factories = factories
        if ignores is not None:
            self.ignores = ignores
        self._deleted_fs_children = list()
        self._renamed_fs_children = dict()

    @finalize
    def __getitem__(self, name):
        name = _encode_name(self.fs_encoding, name)
        if name in self._deleted_fs_children:
            raise KeyError(name)
        try:
            return self.storage[name]
        except KeyError:
            filepath = join_fs_path(self, [name])
            if not os.path.exists(filepath):
                raise KeyError(name)
            factory = self.factory_for_pattern(name)
            if not factory:
                factory = (
                    self.default_directory_factory
                    if os.path.isdir(filepath)
                    else self.default_file_factory
                )
            with _skip_validate_child():
                self[name] = factory(name=name, parent=self)
        return self.storage[name]

    @finalize
    def __setitem__(self, name, value):
        name = _encode_name(self.fs_encoding, name)
        if name in self.ignores:
            raise KeyError('Name is contained in ignores')
        if _directory_context.validate_child:
            if not name:
                raise KeyError('Empty key not allowed in directories')
            if not IDirectory.providedBy(value) and not IFile.providedBy(value):
                raise ValueError(
                    'Incompatible child node. ``IDirectory`` or ``IFile`` '
                    'must be implemented.'
                )
            factory = self.factory_for_pattern(name)
            if factory:
                if not inspect.isclass(factory):
                    class_ = factory(name=name, parent=self).__class__
                else:
                    class_ = factory
                if not isinstance(value, class_):
                    raise ValueError((
                        'Given child node has wrong type. Expected ``{}``, '
                        'got ``{}``'
                    ).format(class_, type(value)))
        if name in self._deleted_fs_children:
            self._deleted_fs_children.remove(name)
        self.storage[name] = value

    @finalize
    def __delitem__(self, name):
        name = _encode_name(self.fs_encoding, name)
        if name in self.ignores:
            raise KeyError('Name is contained in ignores')
        fs_name = get_fs_name(self, name)
        if name in self._renamed_fs_children.values():
            del self._renamed_fs_children[fs_name]
        if os.path.exists(join_fs_path(self, [fs_name])):
            self._deleted_fs_children.append(fs_name)
        if name in self.storage:
            del self.storage[name]

    @finalize
    def __iter__(self):
        try:
            existing = set(os.listdir(join_fs_path(self)))
        except OSError:
            existing = set()
        existing.update(self.storage)
        return iter(existing
            .difference(self._deleted_fs_children)
            .difference(self.ignores)
            .difference(self._renamed_fs_children)
            .union(self._renamed_fs_children.values())
        )

    @finalize
    @locktree
    def __call__(self):
        if IDirectory.providedBy(self):
            path = join_fs_path(self)
            if not os.path.exists(path):
                os.mkdir(path)
            elif not os.path.isdir(path):
                raise KeyError((
                    'Attempt to create directory with name '
                    '"{}" which already exists as file.'
                ).format(self.name))
        while self._deleted_fs_children:
            path = join_fs_path(self, [self._deleted_fs_children.pop()])
            if os.path.exists(path):
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
        for name, new_name in self._renamed_fs_children.items():
            src = os.path.join(*self.fs_path + [name])
            if os.path.exists(src):
                dst = os.path.join(os.path.dirname(src), new_name)
                os.rename(src, dst)
        self._renamed_fs_children = dict()
        for value in self.values():
            if IDirectory.providedBy(value) or IFile.providedBy(value):
                value()

    @default
    def rename(self, name, new_name):
        name = _encode_name(self.fs_encoding, name)
        new_name = _encode_name(self.fs_encoding, new_name)
        if name not in self:
            raise KeyError(name)
        if not new_name:
            raise KeyError('No new name given')
        if new_name in self:
            raise KeyError('File or directory with new name already exists')
        if new_name in self.ignores:
            raise KeyError('New name is contained in ignores')
        if name in self.storage:
            child = self[name]
            child.__name__ = new_name
            with _skip_validate_child():
                self[new_name] = child
            del self.storage[name]
        fs_name = get_fs_name(self, name)
        self._renamed_fs_children[fs_name] = new_name


@plumbing(
    MappingAdopt,
    MappingNode,
    FSMode,
    DirectoryStorage)
class Directory(object):
    """Object mapping a file system directory."""
