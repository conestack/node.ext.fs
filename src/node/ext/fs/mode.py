from node.ext.fs.interfaces import IFSMode
from node.ext.fs.location import join_fs_path
from plumber import Behavior
from plumber import default
from plumber import plumb
from zope.interface import implementer
import os


def get_fs_mode(node):
    fs_path = join_fs_path(node)
    if not os.path.exists(fs_path):
        return None
    return os.stat(fs_path).st_mode & 0o777


@implementer(IFSMode)
class FSMode(Behavior):

    @property
    def fs_mode(self):
        if not hasattr(self, '_fs_mode'):
            fs_mode = get_fs_mode(self)
            if fs_mode is None:
                return None
            self._fs_mode = fs_mode
        return self._fs_mode

    @default
    @fs_mode.setter
    def fs_mode(self, mode):
        self._fs_mode = mode

    @plumb
    def __call__(next_, self):
        # Change file system mode if set
        next_(self)
        fs_mode = self.fs_mode
        if fs_mode is not None:
            os.chmod(join_fs_path(self), fs_mode)
