#
# Copyright 2022 Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Generasl Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301 USA
#
# Refer to the README and COPYING files for full details of the license
#

import urllib.parse

import pytest


class Backend:
    """
    Wrap a userstorage.Backend, adding a url and context manager interface to
    simplify fixtures.
    """

    def __init__(self, storage, can_detect_sector_size=True):
        if not storage.exists():
            pytest.xfail(f"Storage {storage.name} is not available")

        self._storage = storage
        self.path = storage.path
        self.url = urllib.parse.urlparse(f"file:{storage.path}")
        self.block_size = storage.sector_size
        self.can_detect_sector_size = can_detect_sector_size

    def __enter__(self):
        self._storage.setup()
        return self

    def __exit__(self, *args):
        self._storage.teardown()
