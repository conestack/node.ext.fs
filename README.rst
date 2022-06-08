node.ext.fs
===========

.. image:: https://img.shields.io/pypi/v/node.ext.fs.svg
    :target: https://pypi.python.org/pypi/node.ext.fs
    :alt: Latest PyPI version

.. image:: https://img.shields.io/pypi/dm/node.ext.fs.svg
    :target: https://pypi.python.org/pypi/node.ext.fs
    :alt: Number of PyPI downloads

.. image:: https://github.com/conestack/node.ext.fs/actions/workflows/test.yaml/badge.svg
    :target: https://github.com/conestack/node.ext.fs/actions/workflows/test.yaml
    :alt: Test node.ext.fs


Overview
--------

``node.ext.fs`` is a node implementation for file system directories. It is
the successor of `node.ext.directory <https://pypi.python.org/pypi/node.ext.directory>`_.

For more information about ``node`` see
`https://pypi.python.org/pypi/node <https://pypi.python.org/pypi/node>`_.


Usage
-----

Create new file:

.. code-block:: python

    from node.ext.fs import File

    file_path = 'file.txt'
    f = File(name=file_path)

    # set contents via data attribute
    f.data = 'data\n'

    # set contents via lines attribute
    f.lines = ['data']

    # set permissions
    f.fs_mode = 0o644

    # persist
    f()

Read existing file:

.. code-block:: python

    file_path = 'file.txt'
    f = File(name=file_path)

    assert(f.data == 'data\n')
    assert(f.lines == ['data'])
    assert(f.fs_mode == 0o644)

Files with binary data:

.. code-block:: python

    from node.ext.fs import MODE_BINARY

    file_path = 'file.txt'
    f = File(name=file_path)
    f.mode = MODE_BINARY

    f.data = b'\x00\x00'

    assert(f.data == b'\x00\x00')

    # lines property won't work if file in binary mode
    f.lines  # raises RuntimeError

Create directory:

.. code-block:: python

    from node.ext.fs import Directory

    dir_path = '.'
    d = Directory(name=dir_path)

    # add subdirectories and files
    d['sub'] = Directory()
    d['file.txt'] = File()

    # set permissions for directory
    d['sub'].fs_mode = 0o755

    # persist
    d()

Read existing directory:

.. code-block:: python

    dir_path = '.'
    d = Directory(name=dir_path)

.. code-block:: pycon

    >>> d.printtree()
    <class 'node.ext.fs.directory.Directory'>: .
      <class 'node.ext.fs.directory.File'>: file.txt
      <class 'node.ext.fs.directory.Directory'>: sub

Defining the default factories for files and directories is done by setting
``default_file_factory`` respective ``default_directory_factory``:

.. code-block:: python

    class CustomFile(File):
        pass

    class CustomDirectory(Directory):
        default_file_factory = CustomFile

    CustomDirectory.default_directory_factory = CustomDirectory

    dir_path = '.'
    d = CustomDirectory(name=dir_path)

.. code-block:: pycon

    >>> d.printtree()
    <class '...CustomDirectory'>: .
      <class '...CustomFile'>: file.txt
      <class '...CustomDirectory'>: sub

Define wildcard factories. Factories can be defined for directories and files.
Pattern matching is done using ``fnmatch``. See
``node.behaviors.WildcardFactory``:

.. code-block:: python

    class TextFile(File):
        pass

    class LogsDirectory(Directory):
        pass

    d = Directory(
        name='.',
        factories={
            '*.txt': TextFile,
            'logs': LogsDirectory
        })

Now when reading children, factories matching the file or directory name
patterns are used to instantiate the children, using the default factories if
no pattern matches.

.. code-block:: pycon

    >>> os.mkdir('logs')

    >>> os.mkdir('other')

    >>> with open('file.txt', 'w') as f:
    ...     f.write('text')

    >>> with open('file.rst', 'w') as f:
    ...     f.write('rst')

    >>> d = Directory(
    ...     name='.',
    ...     factories={
    ...         '*.txt': TextFile,
    ...         'logs': LogsDirectory
    ...     })

    >>> d.printtree()
    <class 'node.ext.fs.directory.Directory'>: .
      <class '...File'>: file.rst
      <class '...TextFile'>: file.txt
      <class '...LogsDirectory'>: logs
      <class '...Directory'>: other


Python Versions
===============

- Python 2.7, 3.7+
- May work with other versions (untested)


Contributors
============

- Robert Niederreiter (Author)
