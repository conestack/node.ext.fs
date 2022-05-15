from node.interfaces import ICallable
from node.interfaces import ILeaf
from node.interfaces import INode
from zope.interface import Attribute
from zope.interface import Interface


class IFSLocation(Interface):
    """Plumbing behavior for providing a file system location."""

    fs_path = Attribute('Filesystem location of this object')


class IFSMode(Interface):
    """Plumbing behavior for managing file system mode."""

    fs_mode = Attribute('Filesystem mode as expected by ``os.chmod``')


class IFile(INode, ICallable, IFSLocation):
    """Marker interface for files."""


MODE_TEXT = 0
MODE_BINARY = 1


class IFileNode(IFile, ILeaf):
    """File interface."""

    direct_sync = Attribute(
        'Flag whether to directly sync filesystem with ``os.fsync`` on '
        '``__call__``'
    )

    mode = Attribute(
        'Mode of this file. Either ``MODE_TEXT`` or ``MODE_BINARY``'
    )

    data = Attribute('Data of the file')

    lines = Attribute(
        'Data of the file as list of lines. Can only be used if file mode is '
        '``MODE_TEXT``'
    )


class IDirectory(INode, ICallable, IFSLocation):
    """Directory interface."""

    fs_encoding = Attribute('Filesystem encoding. Defaults to UTF-8')

    child_directory_factory = Attribute(
        'Factory creating concrete node instances for directory children'
    )

    default_file_factory = Attribute(
        'Default factory creating concrete node instances for file children'
    )

    file_factories = Attribute(
        'Dict containing file names or endings as keys with the corresponding '
        'file node creating factory.'
    )

    ignores = Attribute('child keys to ignore')
