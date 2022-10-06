Changes
=======

1.0 (2022-10-06)
----------------

- Subclass ``threading.local`` for
  ``node.ext.fs.directory._directory_context`` objects in order to safely
  provide default values.
  [rnix]

- Introduce ``IFileIO`` interface and ``FileIO`` plumbing behavior.
  [rnix]

- Introduce ``IFileNode`` interface.
  [rnix]

- Pass ``name`` and ``parent`` to default file and directory factories.
  [rnix]

- ``DirectoryStorage`` accepts ``fs_path`` keyword argument.
  [rnix]

- Rename ``_FSModeMixin`` plumbing behavior to ``FSMode``. Setting the actual
  file mode is now done by plumbing ``__call__`` function.
  [rnix]

- Introduce ``FSLocation`` plumbing behavior.
  [rnix]

**Breaking Changes**

- Package has been renamed from ``node.ext.directory`` to ``node.ext.fs``.
  There are too many breaking changes for a sane deprecation path.
  [rnix]

- ``DirectoryStorage.__init__`` no longer accepts deprecated ``backup`` keyword
  argument.
  [rnix]

- ``DirectoryStorage.child_directory_factory`` has been renamed to
  ``default_directory_factory``
  [rnix]

- ``DirectoryStorage`` derives from ``node.behaviors.WildcardFactory`` now.
  Own factory pattern logic working with file endings has been removed.
  Patterns must be adopted.
  [rnix]

- Remove global ``file_factories`` and ``DirectoryStorage.file_factories``.
  Wildcard pattern related factories are defined via
  ``DirectoryStorage.factories`` now.
  [rnix]

- Remove ``IFileAddedEvent`` and ``node.ext.fs.events`` module. If you need
  lifecycle events, use ``node.behaviors.Lifecycle`` instead.
  [rnix]

- Basic ``File`` and ``Directory`` objects no longer use referencing related
  plumbung behaviors. You need to define your own base objects plumbing
  ``INodeReference`` implemeting behaviors.
  [rnix]

- Reduce ``IFile`` interface. It no longer inherits from ``ILeaf`` and default
  file implementation related attributes were moved to ``IFileNode`` interface.
  This way it is possible to implement very custom file implementations without
  breaking the interface contract.
  [rnix]

- Rename ``FileStorage`` to ``FileNode``. It no longer inherits from
  ``DictStorage``. Further file data is no longer kept in memory unless it
  changes, then it's kept until it gets written to disk.
  [rnix]

- ``FileNode`` and ``DirectoryStorage`` not inherits from
  ``_FSModeMixin`` respective now ``FSMode`` behavior any more. ``FSMode``
  behavior must be applied explicit on nodes which should provide this
  behavior.
  [rnix]

- Rename ``_fs_path`` helper function to ``get_fs_path``.
  [rnix]

- Rename ``_fs_mode`` helper function to ``get_fs_mode``.
  [rnix]


0.8 (2022-03-21)
----------------

- Replace deprecated use of ``Nodify`` by ``MappingNode``.
  [rnix]

- Replace deprecated use of ``Adopt`` by ``MappingAdopt``.
  [rnix]


0.7
---

- Python 3 support.
  [rnix, 2017-06-06]

- ``fs_mode`` is read from filesystem if file or directory exists and
  fs_mode not set explicitely.
  [rnix, 2017-06-06]

- Remove ``backup`` option from ``IDirectory`` interface. It never really
  worked properly and conceptually ``IDirectory`` is the wrong place for
  handling backups of files.
  [rnix, 2017-06-04]


0.6
---

- Introduce ``node.ext.directory.interfaces.IFile.direct_sync`` setting.
  [rnix, 2017-01-30]

- Complete ``node.ext.directory.interfaces.IFile`` and
  ``node.ext.directory.interfaces.IDirectory`` to reflect implemented features.
  [rnix, 2017-01-30]

- Move ``node.ext.directory.directory.MODE_TEXT`` and
  ``node.ext.directory.directory.MODE_BINARY`` to
  ``node.ext.directory.interfaces``.
  [rnix, 2017-01-30]


0.5.4
-----

- Check whether directory to be peristed already exists by name as file in
  ``node.ext.directory.FileStorage.__call__``.
  [rnix, 2015-10-05]

- Implement fallback to ``path`` in
  ``node.ext.directory.FileStorage.__call__`` if ``fs_path`` not exists.
  [rnix, 2015-10-05]

- Implement fallback to ``path`` in
  ``node.ext.directory.FileStorage._get_data`` if ``fs_path`` not exists.
  [rnix, 2015-10-05]

- Set initial mode with ``self.mode`` property setter instead of internal
  ``self._mode`` in ``node.ext.directory.FileStorage._get_mode``.
  [rnix, 2015-10-05]


0.5.3
-----

- Remove deleted keys from internal reference after ``__call__`` in order
  to return the correct result when adding a file or directory with the same
  key again.
  [rnix, 2015-07-20]


0.5.2
-----

- Use try/except instead of iteration to check whether directory child already
  in memory.
  [rnix, 2015-05-12]


0.5.1
-----

- Always use ``os.chmod`` for setting directory permissions, not only if
  already exists.
  [rnix, 2015-03-03]


0.5
---

- Introduce ``fs_mode`` on directories and files.
  [rnix, 2015-03-03]


0.4
---

- Return empty list in ``File.lines`` if no data.
  [rnix, 2015-02-18]

- Consider filesystem encoding. Defaults to UTF-8.
  [rnix, 2015-02-18]

- Tree locking on modification.
  [rnix, 2014-09-02]

- Prevent empty keys in ``__setitem__``.
  [rnix, 2014-09-02]

- Use ``plumbing`` decorator.
  [rnix, 2014-08-25]


0.3
---

- introduce ``default_file_factory`` on directories for controlling default
  file child creation.
  [rnix, 2013-12-09]

- move file logic in ``FileStorage`` behavior.
  [rnix, 2013-08-06]

- make ``file_factories`` a class property on directory storage.
  [rnix, 2013-08-06]

- make ``ignores`` a class property on directory storage.
  [rnix, 2013-08-06]

- Cleanup interfaces.
  [rnix, 2013-08-06]


0.2
---

- Almost complete rewrite. Fits now paradigms of node based API's.
  [rnix, 2012-01-30]


0.1
---

- initial
