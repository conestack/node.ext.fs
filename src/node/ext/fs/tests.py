# -*- coding: utf-8 -*-
from node.behaviors import DefaultInit
from node.behaviors import DictStorage
from node.behaviors import MappingAdopt
from node.behaviors import MappingNode
from node.behaviors import MappingReference
from node.behaviors import NodeReference
from node.compat import IS_PY2
from node.ext.fs import Directory
from node.ext.fs import DirectoryStorage
from node.ext.fs import FSLocation
from node.ext.fs import FSMode
from node.ext.fs import File
from node.ext.fs import FileNode
from node.ext.fs import MODE_BINARY
from node.ext.fs import MODE_TEXT
from node.ext.fs import get_fs_mode
from node.ext.fs import get_fs_path
from node.ext.fs import join_fs_path
from node.ext.fs.interfaces import IDirectory
from node.ext.fs.interfaces import IFSLocation
from node.ext.fs.interfaces import IFSMode
from node.ext.fs.interfaces import IFile
from node.tests import NodeTestCase
from node.utils import UNSET
from plumber import plumbing
import os
import shutil
import tempfile
import unittest


###############################################################################
# Mock objects
###############################################################################

@plumbing(FSLocation)
class FSLocationObject(object):

    def __init__(self, name=None, parent=None, path=[]):
        self.name = name
        self.parent = parent
        self.path = path


@plumbing(FSMode)
class FSModeObject(FSLocationObject):

    def __call__(self):
        pass


@plumbing(
    DefaultInit,
    NodeReference,
    FSMode,
    FileNode)
class ReferencingFile(object):
    pass


@plumbing(
    MappingAdopt,
    MappingReference,
    MappingNode,
    FSMode,
    DirectoryStorage)
class ReferencingDirectory(object):
    default_file_factory = ReferencingFile

    @property
    def default_directory_factory(self):
        return ReferencingDirectory


###############################################################################
# Tests
###############################################################################

class Tests(NodeTestCase):

    def setUp(self):
        super(Tests, self).setUp()
        self.tempdir = tempfile.mkdtemp()

    def tearDown(self):
        super(Tests, self).tearDown()
        shutil.rmtree(self.tempdir)

    def test_get_fs_path(self):
        ob = FSLocationObject(path=['path'])
        self.assertEqual(get_fs_path(ob), ['path'])
        self.assertEqual(get_fs_path(ob, ['child']), ['path', 'child'])

        class DummyNode:
            path = ['root']

        ob = DummyNode()
        self.assertEqual(get_fs_path(ob), ['root'])
        self.assertEqual(get_fs_path(ob, ['child']), ['root', 'child'])

    def test_join_fs_path(self):
        ob = FSLocationObject(path=['path'])
        self.assertEqual(join_fs_path(ob), 'path')
        self.assertEqual(join_fs_path(ob, ['child']), 'path/child')

    def test_FSLocation(self):
        ob = FSLocationObject(name='name', path=['path'])
        self.assertTrue(IFSLocation.providedBy(ob))
        self.assertEqual(ob.fs_path, ['path'])
        ob.parent = FSLocationObject(path=['root'])
        self.assertEqual(ob.fs_path, ['root', 'name'])
        ob.fs_path = ['path', 'to', 'ob']
        self.assertEqual(ob.fs_path, ['path', 'to', 'ob'])

    def test_get_fs_mode(self):
        path = os.path.join(self.tempdir, 'file')
        with open(path, 'w') as f:
            f.write('')
        os.chmod(path, 0O644)
        ob = FSModeObject(path=[self.tempdir, 'file'])
        self.assertEqual(get_fs_mode(ob), 0O644)
        os.chmod(path, 0O664)
        self.assertEqual(get_fs_mode(ob), 0O664)
        ob = FSModeObject(path=[self.tempdir, 'inexistent'])
        self.assertEqual(get_fs_mode(ob), None)

    def test_FSMode(self):
        path = os.path.join(self.tempdir, 'file')
        with open(path, 'w') as f:
            f.write('')
        ob = FSModeObject(path=[self.tempdir, 'inexistent'])
        self.assertTrue(IFSMode.providedBy(ob))
        self.assertEqual(ob.fs_mode, None)
        ob = FSModeObject(path=[self.tempdir, 'file'])
        ob.fs_mode = 0O777
        ob()
        ob = FSModeObject(path=[self.tempdir, 'file'])
        self.assertEqual(ob.fs_mode, 0O777)

    def test_file_persistance(self):
        filepath = os.path.join(self.tempdir, 'file.txt')
        file = File(name=filepath)
        file.direct_sync = True
        self.assertFalse(os.path.exists(filepath))
        file()
        self.assertFalse(os.path.isdir(filepath))
        self.assertTrue(os.path.exists(filepath))
        with open(filepath) as f:
            out = f.read()
        self.assertEqual(out, '')

    def test_file_mode_text(self):
        filepath = os.path.join(self.tempdir, 'file.txt')
        file = File(name=filepath)
        file.direct_sync = True

        self.assertEqual(file.mode, MODE_TEXT)
        self.assertEqual(file.data, '')
        self.assertEqual(file.lines, [])

        self.assertFalse(hasattr(file, '_data'))
        file.data = 'abc\ndef'
        self.assertEqual(file._data, 'abc\ndef')

        file()
        self.assertEqual(file._data, UNSET)

        with open(filepath) as f:
            out = f.readlines()
        self.assertEqual(out, ['abc\n', 'def'])

        file = File(name=filepath)
        self.assertEqual(file.data, 'abc\ndef')
        self.assertEqual(file.lines, ['abc', 'def'])

        file.lines = ['a', 'b', 'c']
        file()
        with open(filepath) as f:
            out = f.read()
        self.assertEqual(out, 'a\nb\nc')

    def test_file_mode_binary(self):
        filepath = os.path.join(self.tempdir, 'file.bin')

        class BinaryFile(File):
            mode = MODE_BINARY

        file = BinaryFile(name=filepath)
        self.assertEqual(file.data, b'')

        with self.assertRaises(RuntimeError) as arc:
            file.lines
        self.assertEqual(
            str(arc.exception),
            'Cannot read lines from binary file.'
        )

        with self.assertRaises(RuntimeError) as arc:
            file.lines = []
        self.assertEqual(
            str(arc.exception),
            'Cannot write lines to binary file.'
        )

        self.assertFalse(hasattr(file, '_data'))
        file.data = b'\x00\x00'
        self.assertEqual(file._data, b'\x00\x00')

        file()
        self.assertEqual(file._data, UNSET)

        with open(filepath) as f:
            out = f.read()
        self.assertEqual(out, '\x00\x00')

    def test_file_permissions(self):
        filepath = os.path.join(self.tempdir, 'file.txt')
        file = File(name=filepath)
        self.assertEqual(file.fs_mode, None)

        file.fs_mode = 0o644
        file.direct_sync = True

        file()
        self.assertTrue(os.path.exists(filepath))
        self.assertEqual(os.stat(filepath).st_mode & 0o777, 0o644)

        file.fs_mode = 0o600
        file()
        self.assertEqual(os.stat(filepath).st_mode & 0o777, 0o600)

        file = File(name=filepath)
        self.assertEqual(file.fs_mode, 0o600)

    def test_file_with_unicode_name(self):
        directory = Directory(name=self.tempdir)
        directory[u'ä'] = File()
        directory()

        expected = os.listdir(self.tempdir)[0]
        expected = expected.decode('utf-8') if IS_PY2 else expected
        self.assertEqual(expected, u'ä')

        directory = Directory(name=self.tempdir)
        expected = '\xc3\xa4' if IS_PY2 else u'ä'
        self.assertEqual(directory[u'ä'].name, expected)

    def test_file_factories(self):
        class TextFile(File):
            pass

        class AudioFile(File):
            pass

        class LogsDirectory(Directory):
            pass

        factories = {
            '*.txt': TextFile,
            '*.mp3': AudioFile,
            'logs': LogsDirectory
        }

        dir = Directory(name=self.tempdir, factories=factories)
        self.assertEqual(dir.factory_for_pattern('foo'), None)
        self.assertEqual(dir.factory_for_pattern('foo.txt'), TextFile)
        self.assertEqual(dir.factory_for_pattern('foo.mp3'), AudioFile)
        self.assertEqual(dir.factory_for_pattern('logs'), LogsDirectory)

        with open(os.path.join(self.tempdir, 'foo.txt'), 'w') as f:
            f.write('')
        with open(os.path.join(self.tempdir, 'foo.mp3'), 'w') as f:
            f.write('')
        with open(os.path.join(self.tempdir, 'foo'), 'w') as f:
            f.write('')
        os.mkdir(os.path.join(self.tempdir, 'logs'))
        os.mkdir(os.path.join(self.tempdir, 'other'))

        dir = Directory(name=self.tempdir, factories=factories)
        self.checkOutput("""
        <class 'node.ext.fs.directory.Directory'>: ...
        __<class 'node.ext.fs.file.File'>: foo
        __<class 'node.ext.fs.tests...AudioFile'>: foo.mp3
        __<class 'node.ext.fs.tests...TextFile'>: foo.txt
        __<class 'node.ext.fs.tests...LogsDirectory'>: logs
        __<class 'node.ext.fs.directory.Directory'>: other
        """, dir.treerepr(prefix='_'))

    def test_file_fs_path_fallback(self):
        # Path lookup on ``File`` implementations without ``fs_path`` property
        # falls back to ``path`` property
        class FileWithoutFSPath(File):
            @property
            def fs_path(self):
                raise AttributeError

        directory = Directory(name=os.path.join(self.tempdir, 'root'))
        no_fs_path_file = directory['no_fs_path_file'] = FileWithoutFSPath()
        self.assertFalse(hasattr(no_fs_path_file, 'fs_path'))

        directory()

        no_fs_path = os.path.join(*directory.fs_path + ['no_fs_path_file'])
        self.assertTrue(os.path.exists(no_fs_path))

    def test_directory_already_exists_as_file(self):
        # Create a new directory which cannot be persisted
        invalid_dir = os.path.join(self.tempdir, 'invalid_dir')
        with open(invalid_dir, 'w') as f:
            f.write('')

        self.assertTrue(os.path.exists(invalid_dir))
        self.assertFalse(os.path.isdir(invalid_dir))

        directory = Directory(name=invalid_dir)
        with self.assertRaises(KeyError) as arc:
            directory()
        self.checkOutput("""
        'Attempt to create directory with name "...invalid_dir" which already
        exists as file.'
        """, str(arc.exception))

    def test_directory_persistence(self):
        dirpath = os.path.join(self.tempdir, 'root')
        directory = Directory(name=dirpath)

        self.assertFalse(os.path.exists(dirpath))

        directory()
        self.assertTrue(os.path.exists(dirpath))
        self.assertTrue(os.path.isdir(dirpath))

    def test_directory_permissions(self):
        dirpath = os.path.join(self.tempdir, 'root')
        directory = Directory(name=dirpath)
        self.assertEqual(directory.fs_mode, None)

        directory.fs_mode = 0o750
        directory()
        self.assertEqual(os.stat(dirpath).st_mode & 0o777, 0o750)

        directory.fs_mode = 0o700
        directory()
        self.assertEqual(os.stat(dirpath).st_mode & 0o777, 0o700)

        directory = Directory(name=dirpath)
        self.assertEqual(directory.fs_mode, 0o700)

    def test_add_sub_directories(self):
        # Create a directory and add sub directories
        directory = Directory(name=os.path.join(self.tempdir, 'root'))

        with self.assertRaises(KeyError) as arc:
            directory[''] = Directory()
        self.assertEqual(
            str(arc.exception),
            "'Empty key not allowed in directories'"
        )

        directory['subdir1'] = Directory()
        directory['subdir2'] = Directory()

        self.checkOutput("""\
        <class 'node.ext.fs.directory.Directory'>: /.../root
          <class 'node.ext.fs.directory.Directory'>: subdir1
          <class 'node.ext.fs.directory.Directory'>: subdir2
        """, directory.treerepr())

        fs_path = os.path.join(*directory.path)
        self.assertEqual(sorted(directory.keys()), ['subdir1', 'subdir2'])
        self.assertFalse(os.path.exists(fs_path))

        directory()
        self.assertEqual(
            sorted(os.listdir(fs_path)),
            ['subdir1', 'subdir2']
        )

        directory = Directory(name=os.path.join(self.tempdir, 'root'))
        self.checkOutput("""\
        <class 'node.ext.fs.directory.Directory'>: /.../root
          <class 'node.ext.fs.directory.Directory'>: subdir1
          <class 'node.ext.fs.directory.Directory'>: subdir2
        """, directory.treerepr())

    def test_delete_from_directory(self):
        directory = Directory(name=os.path.join(self.tempdir))
        directory['file.txt'] = File()
        directory['subdir'] = Directory()

        self.assertEqual(sorted(os.listdir(self.tempdir)), [])

        directory()
        self.assertEqual(
            sorted(os.listdir(self.tempdir)),
            ['file.txt', 'subdir']
        )

        del directory['file.txt']
        with self.assertRaises(KeyError):
            directory['file.txt']
        self.assertEqual(directory._deleted_fs_children, ['file.txt'])
        self.assertEqual(
            sorted(os.listdir(self.tempdir)),
            ['file.txt', 'subdir']
        )
        directory()
        self.assertEqual(directory._deleted_fs_children, [])
        self.assertEqual(sorted(os.listdir(self.tempdir)), ['subdir'])

        del directory['subdir']
        self.assertEqual(directory._deleted_fs_children, ['subdir'])
        self.assertEqual(sorted(os.listdir(self.tempdir)), ['subdir'])
        directory()
        self.assertEqual(directory._deleted_fs_children, [])
        self.assertEqual(sorted(os.listdir(self.tempdir)), [])

        directory['file.txt'] = File()
        directory()
        del directory['file.txt']
        self.assertEqual(directory._deleted_fs_children, ['file.txt'])
        directory['file.txt'] = File()
        self.assertEqual(directory._deleted_fs_children, [])

    def test_directory___getitem__(self):
        directory = Directory(name=os.path.join(self.tempdir))
        directory['file.txt'] = File()
        directory['subdir'] = Directory()
        directory()

        directory = Directory(name=os.path.join(self.tempdir))

        expected = '<File object \'file.txt\' at '
        self.assertTrue(str(directory['file.txt']).startswith(expected))

        expected = '<Directory object \'subdir\' at '
        self.assertTrue(str(directory['subdir']).startswith(expected))

        with self.assertRaises(KeyError) as arc:
            directory['inexistent']
        self.assertEqual(str(arc.exception), '\'inexistent\'')

    def test_sub_directory_permissions(self):
        directory = Directory(name=os.path.join(self.tempdir, 'root'))
        directory.fs_mode = 0o777

        subdir1 = directory['subdir1'] = Directory()
        subdir1.fs_mode = 0o770

        subdir2 = directory['subdir2'] = Directory()
        subdir2.fs_mode = 0o755

        directory()

        dir_path = os.path.join(*directory.fs_path)
        self.assertEqual(os.stat(dir_path).st_mode & 0o777, 0o777)

        dir_path = os.path.join(*subdir1.fs_path)
        self.assertEqual(os.stat(dir_path).st_mode & 0o777, 0o770)

        dir_path = os.path.join(*subdir2.fs_path)
        self.assertEqual(os.stat(dir_path).st_mode & 0o777, 0o755)

        directory = Directory(name=os.path.join(self.tempdir, 'root'))
        self.assertEqual(directory.fs_mode, 0o777)
        self.assertEqual(directory['subdir1'].fs_mode, 0o770)
        self.assertEqual(directory['subdir2'].fs_mode, 0o755)

    def test_directory_child_validation(self):
        class TestFile(File):
            """"""

        class TestFactoryFile(File):
            """"""

        def test_file_factory(name, parent):
            return TestFactoryFile(name=name, parent=parent)

        class TestDirectory(Directory):
            factories = {
                'file': TestFile,
                'factoryfile': test_file_factory
            }

        directory = TestDirectory(fs_path=[self.tempdir, 'root'])

        with self.assertRaises(ValueError) as arc:
            directory['unknown'] = object()
        self.assertEqual(str(arc.exception), (
            'Incompatible child node. ``IDirectory`` '
            'or ``IFile`` must be implemented.'
        ))

        with self.assertRaises(ValueError) as arc:
            directory['file'] = File()
        self.checkOutput("""
        Given child node has wrong type. Expected
        ``<class '...TestFile'>``, got ``<class 'node.ext.fs.file.File'>``
        """, str(arc.exception))

        with self.assertRaises(ValueError) as arc:
            directory['factoryfile'] = File()
        self.checkOutput("""
        Given child node has wrong type. Expected
        ``<class '...TestFactoryFile'>``, got ``<class 'node.ext.fs.file.File'>``
        """, str(arc.exception))

        directory['any'] = File()
        directory['file'] = TestFile()
        directory['factoryfile'] = TestFactoryFile()
        directory()

        directory = TestDirectory(fs_path=[self.tempdir, 'root'])
        self.checkOutput("""
        <class '...TestDirectory'>: ...
        __<class 'node.ext.fs.file.File'>: any
        __<class '...TestFactoryFile'>: factoryfile
        __<class '...TestFile'>: file
        """, directory.treerepr(prefix='_'))

    def test_ignore_children(self):
        # Ignore children in directories
        with open(os.path.join(self.tempdir, 'file1.txt'), 'w') as f:
            f.write('')
        with open(os.path.join(self.tempdir, 'file2.txt'), 'w') as f:
            f.write('')

        class DirectoryWithIgnores(Directory):
            ignores = ['file1.txt']

        self.assertEqual(
            sorted(os.listdir(self.tempdir)),
            ['file1.txt', 'file2.txt']
        )

        directory = DirectoryWithIgnores(name=self.tempdir)
        self.assertEqual(list(directory.keys()), ['file2.txt'])

        directory = Directory(name=self.tempdir, ignores=['file2.txt'])
        self.assertEqual(list(directory.keys()), ['file1.txt'])

        with self.assertRaises(KeyError) as arc:
            directory['file2.txt'] = File()
        self.assertEqual(str(arc.exception), "'Name is contained in ignores'")

        with self.assertRaises(KeyError) as arc:
            del directory['file2.txt']
        self.assertEqual(str(arc.exception), "'Name is contained in ignores'")

        with self.assertRaises(KeyError) as arc:
            directory.rename('file1.txt', 'file2.txt')
        self.assertEqual(str(arc.exception), "'New name is contained in ignores'")

    def test_fs_path_keyword_argument(self):
        directory = Directory(name='foo')
        self.assertEqual(directory.fs_path, ['foo'])

        directory = Directory(name='foo', fs_path=['bar'])
        self.assertEqual(directory.fs_path, ['bar'])

    def test_rename_children(self):
        with open(os.path.join(self.tempdir, 'file1.txt'), 'w') as f:
            f.write('')
        with open(os.path.join(self.tempdir, 'file2.txt'), 'w') as f:
            f.write('')
        os.makedirs(os.path.join(self.tempdir, 'dir1'))
        os.makedirs(os.path.join(self.tempdir, 'dir2'))

        # invalid rename calls
        directory = Directory(name=self.tempdir)
        with self.assertRaises(KeyError) as arc:
            directory.rename('inextistent', '')
        self.assertEqual(str(arc.exception), "'inextistent'")

        with self.assertRaises(KeyError) as arc:
            directory.rename('file1.txt', '')
        self.assertEqual(str(arc.exception), "'No new name given'")

        with self.assertRaises(KeyError) as arc:
            directory.rename('file1.txt', 'file2.txt')
        self.assertEqual(
            str(arc.exception),
            "'File or directory with new name already exists'"
        )

        # case children not loaded in storage yet
        directory = Directory(name=self.tempdir)
        self.assertEqual(directory.storage, {})
        directory.rename('file1.txt', 'file3.txt')
        directory.rename('dir1', 'dir3')
        self.assertEqual(
            directory._renamed_fs_children,
            {'dir1': 'dir3', 'file1.txt': 'file3.txt'}
        )
        self.assertEqual(
            sorted(directory),
            ['dir2', 'dir3', 'file2.txt', 'file3.txt']
        )
        self.assertEqual(
            sorted(os.listdir(self.tempdir)),
            ['dir1', 'dir2', 'file1.txt', 'file2.txt']
        )
        directory()
        self.assertEqual(
            sorted(os.listdir(self.tempdir)),
            ['dir2', 'dir3', 'file2.txt', 'file3.txt']
        )
        self.assertEqual(directory._renamed_fs_children, {})

        # case children loaded in storage
        directory = Directory(name=self.tempdir)
        directory.values()
        self.assertEqual(
            sorted(directory.storage),
            ['dir2', 'dir3', 'file2.txt', 'file3.txt']
        )
        directory.rename('dir3', 'dir1')
        self.assertEqual(
            sorted(directory.storage),
            ['dir1', 'dir2', 'file2.txt', 'file3.txt']
        )
        self.assertEqual(directory['dir1'].name, 'dir1')
        self.assertEqual(
            sorted(os.listdir(self.tempdir)),
            ['dir2', 'dir3', 'file2.txt', 'file3.txt']
        )
        directory()
        self.assertEqual(
            sorted(os.listdir(self.tempdir)),
            ['dir1', 'dir2', 'file2.txt', 'file3.txt']
        )

        # case rename a child to a name which was deleted
        with open(os.path.join(self.tempdir, 'dir1', 'marker'), 'w') as f:
            f.write('')
        directory = Directory(name=self.tempdir)
        del directory['dir2']
        self.assertEqual(
            sorted(directory),
            ['dir1', 'file2.txt', 'file3.txt']
        )
        self.assertEqual(directory._deleted_fs_children, ['dir2'])
        directory.rename('dir1', 'dir2')
        self.assertEqual(directory._renamed_fs_children, {'dir1': 'dir2'})
        self.assertEqual(
            sorted(directory),
            ['dir2', 'file2.txt', 'file3.txt']
        )
        self.assertEqual(
            sorted(os.listdir(self.tempdir)),
            ['dir1', 'dir2', 'file2.txt', 'file3.txt']
        )
        directory()
        self.assertEqual(
            sorted(os.listdir(self.tempdir)),
            ['dir2', 'file2.txt', 'file3.txt']
        )
        self.assertTrue(
            os.path.exists(os.path.join(self.tempdir, 'dir2', 'marker'))
        )

        # Check fs path handling on renamed objects
        directory = Directory(name=self.tempdir)
        directory.rename('dir2', 'dir1')
        child_dir = directory['dir1']
        self.assertEqual(child_dir.path[1:], ['dir1'])
        self.assertEqual(child_dir.fs_path[1:], ['dir2'])
        self.assertEqual(sorted(child_dir), ['marker'])
        marker = child_dir['marker']
        self.assertEqual(marker.path[1:], ['dir1', 'marker'])
        self.assertEqual(marker.fs_path[1:], ['dir2', 'marker'])

        directory()
        self.assertEqual(child_dir.path[1:], ['dir1'])
        self.assertEqual(child_dir.fs_path[1:], ['dir1'])
        self.assertEqual(sorted(child_dir), ['marker'])
        self.assertEqual(marker.path[1:], ['dir1', 'marker'])
        self.assertEqual(marker.fs_path[1:], ['dir1', 'marker'])

        # Check renaming already renamed object
        directory = Directory(name=self.tempdir)
        directory.rename('dir1', 'dir2')
        directory.rename('dir2', 'dir3')
        self.assertEqual(directory._renamed_fs_children, {'dir1': 'dir3'})
        directory()
        self.assertEqual(
            sorted(os.listdir(self.tempdir)),
            ['dir3', 'file2.txt', 'file3.txt']
        )

        # Case delete renamed object
        directory = Directory(name=self.tempdir)
        directory.rename('dir3', 'dir1')
        self.assertEqual(directory._renamed_fs_children, {'dir3': 'dir1'})
        self.assertEqual(directory._deleted_fs_children, [])
        del directory['dir1']
        self.assertEqual(directory._renamed_fs_children, {})
        self.assertEqual(directory._deleted_fs_children, ['dir3'])
        directory()
        self.assertEqual(
            sorted(os.listdir(self.tempdir)),
            ['file2.txt', 'file3.txt']
        )

    def test_node_index(self):
        directory = ReferencingDirectory(
            name=os.path.join(self.tempdir, 'root')
        )
        self.assertEqual(len(directory._index), 1)

        directory['file.txt'] = ReferencingFile()
        self.assertEqual(len(directory._index), 2)

        subdir = directory['subdir'] = ReferencingDirectory()
        self.assertEqual(len(directory._index), 3)

        subdir['subfile.txt'] = ReferencingFile()
        self.assertEqual(len(directory._index), 4)

        directory()
        directory = ReferencingDirectory(
            name=os.path.join(self.tempdir, 'root')
        )
        self.checkOutput("""\
        <class 'node.ext.fs.tests.ReferencingDirectory'>: ...root
          <class 'node.ext.fs.tests.ReferencingFile'>: file.txt
          <class 'node.ext.fs.tests.ReferencingDirectory'>: subdir
            <class 'node.ext.fs.tests.ReferencingFile'>: subfile.txt
        """, directory.treerepr())

        self.assertEqual(len(directory._index), 4)
        del directory['subdir']['subfile.txt']
        self.assertEqual(len(directory._index), 3)
        del directory['subdir']
        self.assertEqual(len(directory._index), 2)

        directory()
        directory = ReferencingDirectory(
            name=os.path.join(self.tempdir, 'root')
        )
        self.checkOutput("""\
        <class 'node.ext.fs.tests.ReferencingDirectory'>: ...root
          <class 'node.ext.fs.tests.ReferencingFile'>: file.txt
        """, directory.treerepr())

        self.assertEqual(len(directory._index), 2)

    def test_interfaces(self):
        directory = Directory()
        self.assertTrue(IDirectory.providedBy(directory))

        file = File()
        self.assertTrue(IFile.providedBy(file))


if __name__ == '__main__':
    from node.ext.fs import tests
    import sys

    suite = unittest.TestSuite()
    suite.addTest(unittest.findTestCases(tests))
    runner = unittest.TextTestRunner(failfast=True)
    result = runner.run(suite)
    sys.exit(not result.wasSuccessful())
