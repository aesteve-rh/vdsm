#
# Copyright 2015-2016 Red Hat, Inc.
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
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301  USA
#
# Refer to the README and COPYING files for full details of the license
#

from __future__ import absolute_import
from contextlib import contextmanager
import os
import six

from nose.plugins.attrib import attr

from vdsm.network.netinfo import misc
from vdsm.tool import unified_persistence

from monkeypatch import MonkeyPatchScope
from testlib import VdsmTestCase as TestCaseBase
from testlib import namedTemporaryDir

NETWORK_NAME = 'test-network10'
VLAN = '100'
BOND_NAME = 'bond10'
NIC_NAME = 'eth3'

FAKE_NETINFO = {
    'nics': {
        NIC_NAME: {
            'permhwaddr': 'ba:8d:23:4d:d7:41', 'addr': '',
            'ipv6addrs': [], 'mtu': '1500', 'netmask': '', 'ipv4addrs': [],
            'hwaddr': 'ba:8d:23:4d:d7:41', 'speed': 0},
        'eth0': {
            'addr': '192.168.122.4',
            'ipv6addrs': ['fe80::5054:ff:fec4:49fb/64'], 'mtu': '1500',
            'netmask': '255.255.255.0', 'ipv4addrs': ['192.168.122.4/24'],
            'hwaddr': '52:54:00:c4:49:fb', 'speed': 0}},
    'vlans': {
        BOND_NAME + '.' + VLAN: {
            'iface': BOND_NAME, 'addr': '',
            'ipv6addrs': ['fe80::b88d:23ff:fe4d:d741/64'], 'vlanid': int(VLAN),
            'mtu': '1500', 'netmask': '', 'ipv4addrs': []}},
    'bondings': {
        'bond0': {
            'addr': '',
            'ipv6addrs': [], 'mtu': '1500', 'netmask': '', 'ipv4addrs': [],
            'hwaddr': '00:00:00:00:00:00', 'slaves': [], 'opts':
            {'arp_all_targets': '0'}},
        BOND_NAME: {
            'addr': '',
            'ipv6addrs': ['fe80::b88d:23ff:fe4d:d741/64'], 'mtu': '1500',
            'netmask': '', 'ipv4addrs': [], 'hwaddr': 'ba:8d:23:4d:d7:41',
            'slaves': [NIC_NAME], 'opts': {'miimon': '150', 'mode': '4',
                                           'arp_all_targets': '0'}}},
    'bridges': {},
    'networks': {
        NETWORK_NAME: {
            'iface': NETWORK_NAME, 'addr': '',
            'bridged': True, 'ipv6addrs': ['fe80::b88d:23ff:fe4d:d741/64'],
            'gateway': '', 'bootproto4': 'none', 'netmask': '', 'stp': 'off',
            'ipv4addrs': [], 'mtu': '1500', 'ipv6gateway': '::', 'ports':
            [BOND_NAME + '.' + VLAN]}},
    'nameservers': [],
}


FAKE_IFCFGS = {
    NETWORK_NAME: (
        '# Generated by VDSM version 4.16.10-8.gitc937927.el6\n'
        'DEVICE=%s\n'
        'TYPE=Bridge\n'
        'DELAY=0\n'
        'STP=off\n'
        'ONBOOT=no\n'
        'MTU=1500\n'
        'DEFROUTE=no\n'
        'NM_CONTROLLED=no\n'
        'HOTPLUG=no' % NETWORK_NAME),
    BOND_NAME + '.' + VLAN: (
        'DEVICE=bond%s.%s\n'
        'VLAN=yes\n'
        'ONBOOT=yes\n'
        'BOOTPROTO=static\n'
        'NM_CONTROLLED=no\n'
        'HOTPLUG=no' % (BOND_NAME, VLAN)),
    BOND_NAME: (
        'DEVICE=%s\n'
        'BONDING_OPTS="mode=802.3ad miimon=150"\n'
        'ONBOOT=yes\n'
        'BOOTPROTO=none\n'
        'DEFROUTE=yes\n'
        'NM_CONTROLLED=no\n'
        'HOTPLUG=no' % BOND_NAME),
    NIC_NAME: (
        'DEVICE=%s\n'
        'MASTER=%s\n'
        'SLAVE=yes\n'
        'ONBOOT=yes\n'
        'MTU=1500\n'
        'NM_CONTROLLED=no' % (NIC_NAME, BOND_NAME))}


@contextmanager
def _fake_ifcfgs():
    with namedTemporaryDir() as temp_dir:
        for iface, conf in six.iteritems(FAKE_IFCFGS):
            with open(os.path.join(temp_dir, 'ifcfg-' + iface), 'w') as f:
                f.write(conf)
        yield temp_dir


@attr(type='unit')
class unfiedPersistenceTests(TestCaseBase):

    def test_getNetInfo(self):
        """Test if getNetInfo marks non-VDSM devices as a part of persistent
        network.
        """
        with _fake_ifcfgs() as ifcfgs_dir:
            FAKE_NET_CONF_PREF = ifcfgs_dir + '/ifcfg-'
            with MonkeyPatchScope(
                [(unified_persistence.netswitch, 'netinfo',
                  lambda: FAKE_NETINFO),
                 (misc, 'NET_CONF_PREF', FAKE_NET_CONF_PREF)]):
                networks, bonds = unified_persistence._getNetInfo()

        self.assertEquals(set(networks), set([NETWORK_NAME]))
        self.assertEquals(set(bonds), set([BOND_NAME]))
