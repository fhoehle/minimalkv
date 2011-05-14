#!/usr/bin/env python
# coding=utf8

import os
import shutil
import urllib

from . import UrlKeyValueStore


class FilesystemStore(UrlKeyValueStore):
    """Store data in files on the filesystem.

    The *FilesystemStore* stores every value as its own file on the filesystem,
    all under a common directory.

    Any call to :func:`url_for` will result in a `file://`-URL pointing towards
    the internal storage to be generated.
    """
    def __init__(self, root, **kwargs):
        """Initialize new FilesystemStore

        :param root: the base directory for the store
        """
        super(FilesystemStore, self).__init__(**kwargs)
        self.root = root
        self.bufsize = 1024 * 1024  # 1m

    def _build_filename(self, key):
        return os.path.join(self.root, key)

    def _delete(self, key):
        try:
            os.unlink(self._build_filename(key))
        except OSError, e:
            if not e.errno == 2:
                raise

    def _has_key(self, key):
        return os.path.exists(self._build_filename(key))

    def _open(self, key):
        try:
            f = open(self._build_filename(key), 'rb')
            return f
        except IOError, e:
            if 2 == e.errno:
                raise KeyError(key)
            else:
                raise

    def _put(self, key, data):
        with file(self._build_filename(key), 'wb') as f:
            f.write(data)

        return key

    def _put_file(self, key, file):
        bufsize = self.bufsize
        with open(self._build_filename(key), 'wb') as f:
            while True:
                buf = file.read(bufsize)
                f.write(buf)
                if len(buf) < bufsize:
                    break

        return key

    def _put_filename(self, key, filename):
        shutil.move(filename, self._build_filename(key))
        return key

    def _url_for(self, key):
        full = os.path.abspath(self._build_filename(key))
        parts = full.split(os.sep)
        location = '/'.join(urllib.quote(p, safe='') for p in parts)
        return 'file://' + location

    def keys(self):
        return os.listdir(self.root)

    def iter_keys(self):
        return iter(self.keys())


class WebFilesystemStore(FilesystemStore):
    """FilesystemStore that supports generating URLs suitable for web
    applications. Most common use is to make the *root* directory of the
    filesystem store available through a webserver. Example:

    >>> from simplekv.fs import WebFilesystemStore
    >>> webserver_url_prefix = 'https://some.domain.invalid/files/'
    >>> webserver_root = '/var/www/some.domain.invalid/www-data/files/'
    >>> store = WebFilesystemStore(webserver_root, webserver_url_prefix)
    >>> print store.url_for('some_key')
    https://some.domain.invalid/files/some_key

    Note that the prefix is simply prepended to the relative URL for the key.
    It therefore, in most cases, must include a trailing slash.
    """
    def __init__(self, root, url_prefix, **kwargs):
        """Initialize new WebFilesystemStore.

        :param root: see :func:`simplekv.FilesystemStore.__init__`
        :param url_prefix: will get prepended to every url generated with
                           url_for.
        """
        super(WebFilesystemStore, self).__init__(root, **kwargs)

        self.url_prefix = url_prefix

    def _url_for(self, key):
        rel = key
        return self.url_prefix + urllib.quote(rel, safe='')
