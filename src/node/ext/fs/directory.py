from node.behaviors import DictStorage
from node.behaviors import MappingAdopt
from node.behaviors import MappingNode
from node.behaviors import MappingReference
from node.compat import IS_PY2
from node.ext.fs.events import FileAddedEvent
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
from zope.component.event import objectEventNotify
from zope.interface import implementer
import logging
import os
import shutil


logger = logging.getLogger('node.ext.fs')


# global file factories
factories = dict()

# B/C
file_factories = factories


def _encode_name(fs_encoding, name):
    name = (
        name.encode(fs_encoding)
        if IS_PY2 and isinstance(name, unicode)
        else name
    )
    return name


@implementer(IDirectory)
class DirectoryStorage(DictStorage, FSLocation):
    fs_encoding = default('utf-8')
    ignores = default(list())
    default_file_factory = default(File)

    # XXX: rename later to file_factories, keep now as is for B/C reasons
    factories = default(dict())

    @default
    @property
    def file_factories(self):
        # temporary, see above
        return self.factories

    @default
    @property
    def child_directory_factory(self):
        return Directory

    @finalize
    def __init__(
        self,
        name=None,
        parent=None,
        backup=False,
        factories=dict(),
        fs_path=None
    ):
        self.__name__ = name
        self.__parent__ = parent
        if backup or hasattr(self, 'backup'):
            logger.warning(
                '``backup`` handling has been removed from ``Directory`` '
                'implementation as of node.ext.fs 0.7'
            )
        # override factories if given
        if factories:
            self.factories = factories
        self.fs_path = fs_path
        self._deleted = list()

    @finalize
    def __getitem__(self, name):
        name = _encode_name(self.fs_encoding, name)
        try:
            return self.storage[name]
        except KeyError:
            self[name] = self._create_child_by_factory(name)
        return self.storage[name]

    @finalize
    def __setitem__(self, name, value):
        if not name:
            raise KeyError('Empty key not allowed in directories')
        name = _encode_name(self.fs_encoding, name)
        if IFile.providedBy(value) or IDirectory.providedBy(value):
            self.storage[name] = value
            # XXX: This event is currently used in node.ext.zcml and
            #      node.ext.python to trigger parsing. But this behavior
            #      requires the event to be triggered on __getitem__ which is
            #      actually not how life cycle events shall behave. Fix in
            #      node.ext.zcml and node.ext.python, remove event notification
            #      here, use node.behaviors.Lifecycle and suppress event
            #      notification in self.__getitem__
            objectEventNotify(FileAddedEvent(value))
            return
        raise ValueError('Unknown child node.')

    @finalize
    def __delitem__(self, name):
        name = _encode_name(self.fs_encoding, name)
        if os.path.exists(os.path.join(*get_fs_path(self, [name]))):
            self._deleted.append(name)
        del self.storage[name]

    @finalize
    def __iter__(self):
        try:
            existing = set(os.listdir(os.path.join(*get_fs_path(self))))
        except OSError:
            existing = set()
        for key in self.storage:
            existing.add(key)
        for key in existing:
            if key in self._deleted:
                continue
            if key in self.ignores:
                continue
            yield key

    @finalize
    @locktree
    def __call__(self):
        if IDirectory.providedBy(self):
            path = os.path.join(*get_fs_path(self))
            if not os.path.exists(path):
                os.mkdir(path)
            elif not os.path.isdir(path):
                raise KeyError(
                    'Attempt to create a directory with name '
                    'which already exists as file'
                )
        while self._deleted:
            path = os.path.join(*get_fs_path(self, [self._deleted.pop()]))
            if os.path.exists(path):
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
        for value in self.values():
            if IDirectory.providedBy(value):
                value()
            elif IFile.providedBy(value):
                value()

    @default
    @locktree
    def _create_child_by_factory(self, name):
        filepath = os.path.join(*get_fs_path(self, [name]))
        if not os.path.exists(filepath):
            raise KeyError(name)
        if os.path.isdir(filepath):
            return self.child_directory_factory(name=name, parent=self)
        factory = self._factory_for_ending(name)
        if not factory:
            return self.default_file_factory(name=name, parent=self)
        try:
            return factory(name=name, parent=self)
        except TypeError as e:
            # happens if the factory cannot be called with name and parent
            # keyword arguments, in this case we treat it as a flat file.
            logger.error(
                'File creation by factory failed. Fall back to ``File``. '
                'Reason: {}'.format(e))
            return File(name=name, parent=self)

    @default
    def _factory_for_ending(self, name):
        def match(keys, key):
            keys = sorted(keys, key=lambda x: len(x), reverse=True)
            for possible in keys:
                if key.endswith(possible):
                    return possible
        factory_keys = [
            match(self.file_factories.keys(), name),
            match(file_factories.keys(), name),
        ]
        if factory_keys[0]:
            if factory_keys[1] and len(factory_keys[1]) > len(factory_keys[0]):
                return file_factories[factory_keys[1]]
            return self.file_factories[factory_keys[0]]
        if factory_keys[1]:
            return file_factories[factory_keys[1]]


@plumbing(
    MappingAdopt,
    MappingReference,
    MappingNode,
    FSMode,
    DirectoryStorage)
class Directory(object):
    """Object mapping a file system directory.
    """
