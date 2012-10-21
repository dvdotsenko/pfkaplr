#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2011 Yesudeep Mangalapilly <yesudeep@gmail.com>
# Copyright 2012 Google, Inc.
# Copyright 2012 Daniel Dotsenko <dotsa@hotmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


# Heavily Modified compared to what is shipped with WatchDog project.
# if this is too simple, look at the original dirsnapshot.py within WatchDog project
# This is a **back up** file system watcher. No point stressing about tunning.
# ddotsenko

import os
import sys

def compare_snapshots(self, before, after):

    old_stats = before.stats
    old_paths = before.paths
    new_stats = after.stats
    new_paths = after.paths

    deleted = old_paths - new_paths
    created = new_paths - old_paths

    modified = []
    # Detect all the modifications.
    for path, stat_info in new_stats.items():
      if path in old_stats:
        ref_stat_info = old_stats(path)
        if stat_info.st_ino == ref_stat_info.st_ino and stat_info.st_mtime != ref_stat_info.st_mtime:
          modified.append(path)

    # movedfrom = []
    # movedto = []

    # # Detect all the moves/renames.
    # # Doesn't work on Windows, so exlude on Windows.
    # if not sys.platform.startswith('win'):
    #   for created_path in created.copy():
    #     created_stat_info = new_stats(created_path)
    #     for deleted_path in deleted.copy():
    #       deleted_stat_info = old_stats(deleted_path)
    #       if created_stat_info.st_ino == deleted_stat_info.st_ino:
    #         deleted.remove(deleted_path)
    #         created.remove(created_path)
    #         movedfrom.append(deleted_path)
    #         movedto.append(created_path)

    return [(self.basepath, path, 'Updated') for path in modified] + \
      [(self.basepath, path, 'Created') for path in created] + \
      [(self.basepath, path, 'Deleted') for path in deleted]

class DirectorySnapshot(object):
  """
  A snapshot of stat information of files in a directory.

  @param {String} path Absolute or relative path to the path to be watched.
  @param {Boolean} [autoscan=True] Flag indicating if the scanning of the directory is to be ran at the inception of this class's instance. 
  This flag allows copying of pre-scanned class instances (avoiding the rescanning)
  """

  def __init__(self, path='.', autoscan = True):
    self.basepath = os.path.abspath(os.path.normpath(path)) + os.path.sep
    self.stats = {}
    self._inode_to_path = {}

    if autoscan:
      self.scan()

  def scan(self):
    sep = os.path.sep
    # we will be removing the basepath prefix from all paths stored in the stats
    chop_count = len(self.basepath)

    # root folder itself
    stat_info = os.stat(self.basepath)
    self.stats[''] = stat_info
    self._inode_to_path[stat_info.st_ino] = ''

    for root, directories, files in os.walk(self.basepath):
      for name in directories:
        try:
          # we intentionally add os.path.sep to the end of folder names
          # this is to save the trip to os.path.isdir() or stat.S_ISDIR later.
          path = (root + sep + name + sep)[chop_count:]
          stat_info = os.stat(self.basepath + path)
          self.stats[path] = stat_info
          self._inode_to_path[stat_info.st_ino] = path

        except OSError:
          continue

      for name in files:
        try:
          path = (root + sep + name)[chop_count:]
          stat_info = os.stat(self.basepath + path)
          self.stats[path] = stat_info
          self._inode_to_path[stat_info.st_ino] = path

        except OSError:
          continue

  def __sub__(self, substracted):
    """Allow subtracting a DirectorySnapshot object instance from another.

    @returns {Change[]} An array of Change tuples [(basepath, changed_subpath, change_type),...]
    """
    return compare_snapshots(substracted, self)

  #def __add__(self, new_dirsnap):
  #    self._stat_snapshot.update(new_dirsnap._stat_snapshot)

  def copy(self, from_pathname=None):
    snapshot = DirectorySnapshot( path = from_pathname, autoscan = False)

    for pathname, stat_info in self._stat_snapshot.items():
      if pathname.starts_with(from_pathname):
        snapshot._stat_snapshot[pathname] = stat_info
        snapshot._inode_to_path[stat_info.st_ino] = pathname
    return snapshot

  def path_for_inode(self, inode):
    """
    Determines the path that an inode represents in a snapshot.

    :param inode:
        inode number.
    """
    return self._inode_to_path[inode]

  def stat_info_for_inode(self, inode):
    """
    Determines stat information for a given inode.

    :param inode:
        inode number.
    """
    return self.stat_info(self.path_for_inode(inode))

  @property
  def paths(self):
    """
    List of file/directory paths in the snapshot.
    """
    return set(self._stat_snapshot)

  def __str__(self):
    return self.__repr__()

  def __repr__(self):
    return str(self._stat_snapshot)

