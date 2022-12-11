from node.interfaces import ICallable
from node.interfaces import ILeaf
from node.interfaces import INode
from node.interfaces import IWildcardFactory
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


class IFileIO(IFSLocation):
    """File IO interface."""

    mode = Attribute(
        'Mode of this file. Either ``MODE_TEXT`` or ``MODE_BINARY``'
    )

    read_fd = Attribute(
        'Context manager providing the file descriptor in read mode'
    )

    write_fd = Attribute(
        'Context manager providing the file descriptor in write mode'
    )


class IFileNode(IFile, IFileIO, ILeaf):
    """Basic file node interface."""

    direct_sync = Attribute(
        'Flag whether to directly sync filesystem with ``os.fsync`` on '
        '``__call__``'
    )

    data = Attribute('Data of the file')

    lines = Attribute(
        'Data of the file as list of lines. Can only be used if file mode is '
        '``MODE_TEXT``'
    )


class IDirectory(INode, ICallable, IWildcardFactory, IFSLocation):
    """Directory interface."""

    fs_encoding = Attribute('Filesystem encoding. Defaults to UTF-8')

    default_directory_factory = Attribute(
        'Default factory for creating directory children'
    )

    default_file_factory = Attribute(
        'Default factory for creating file children'
    )

    ignores = Attribute('Child keys to ignore')

    def rename(name, new_name):
        """Rename child

        :param name: Name of the child to rename
        :param new_name: New name of the child
        """
