from node.behaviors import DictStorage
from node.behaviors import MappingAdopt
from node.behaviors import MappingNode
from node.behaviors import Reference
from node.compat import IS_PY2
from node.ext.directory.events import FileAddedEvent
from node.ext.directory.file import File
from node.ext.directory.interfaces import IDirectory
from node.ext.directory.interfaces import IFile
from node.ext.directory.location import FSLocation
from node.ext.directory.location import get_fs_path
from node.ext.directory.mode import FSMode
from node.locking import locktree
from plumber import default
from plumber import finalize
from plumber import plumbing
from zope.component.event import objectEventNotify
from zope.interface import implementer
import logging
import os
import shutil


logger = logging.getLogger('node.ext.directory')


# global file factories
file_factories = dict()


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
                'implementation as of node.ext.directory 0.7'
            )
        # override file factories if given
        if factories:
            self.factories = factories
        self.fs_path = fs_path
        self._deleted = list()

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

    @finalize
    def __setitem__(self, name, value):
        if not name:
            raise KeyError('Empty key not allowed in directories')
        name = self._encode_name(name)
        if IFile.providedBy(value) or IDirectory.providedBy(value):
            self.storage[name] = value
            # XXX: This event is currently used in node.ext.zcml and
            #      node.ext.python to trigger parsing. But this behavior
            #      requires the event to be triggered on __getitem__ which is
            #      actually not how life cycle events shall behave. Fix in
            #      node.ext.zcml and node.ext.python, remove event notification
            #      here, use node.behaviors.Lifecycle and suppress event
            #      notification in self._create_child_by_factory
            objectEventNotify(FileAddedEvent(value))
            return
        raise ValueError('Unknown child node.')

    @finalize
    def __getitem__(self, name):
        name = self._encode_name(name)
        try:
            return self.storage[name]
        except KeyError:
            self._create_child_by_factory(name)
        return self.storage[name]

    @default
    @locktree
    def _create_child_by_factory(self, name):
        filepath = os.path.join(*get_fs_path(self, [name]))
        if not os.path.exists(filepath):
            return
        if os.path.isdir(filepath):
            # XXX: to suppress event notify
            self[name] = self.child_directory_factory(name=name, parent=self)
            return
        factory = self._factory_for_ending(name)
        if not factory:
            # XXX: to suppress event notify
            self[name] = self.default_file_factory()
            return
        try:
            # XXX: to suppress event notify
            self[name] = factory()
        except TypeError as e:
            # happens if the factory cannot be called without args, in this
            # case we treat it as a flat file.
            # XXX: to suppress event notify
            logger.error(
                'File creation by factory failed. Fall back to ``File``. '
                'Reason: {}'.format(e))
            self[name] = File()

    @finalize
    def __delitem__(self, name):
        name = self._encode_name(name)
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

    @default
    def _encode_name(self, name):
        name = name.encode(self.fs_encoding) \
            if IS_PY2 and isinstance(name, unicode) \
            else name
        return name

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
    Reference,  # XXX: remove from default directory
    MappingNode,
    FSMode,
    DirectoryStorage)
class Directory(object):
    """Object mapping a file system directory.
    """
