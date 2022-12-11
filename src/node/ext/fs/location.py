from node.ext.fs.interfaces import IFSLocation
from plumber import Behavior
from plumber import default
from zope.interface import implementer
import os


def get_fs_name(directory, name):
    renamed = getattr(directory, '_renamed_fs_children', {})
    for old_name, new_name in renamed.items():
        if name == new_name:
            name = old_name
            break
    return name


def get_fs_path(ob, child_path=[]):
    # Use fs_path if provided by ob, otherwise fallback to path
    if hasattr(ob, 'fs_path'):
        return ob.fs_path + child_path
    return ob.path + child_path


def join_fs_path(ob, child_path=[]):
    return os.path.join(*get_fs_path(ob, child_path))


@implementer(IFSLocation)
class FSLocation(Behavior):

    @property
    def fs_path(self):
        if getattr(self, '_fs_path', None) is not None:
            return self._fs_path
        parent = self.parent
        if parent is not None and hasattr(parent, 'fs_path'):
            return self.parent.fs_path + [get_fs_name(self.parent, self.name)]
        return self.path

    @default
    @fs_path.setter
    def fs_path(self, path):
        self._fs_path = path
