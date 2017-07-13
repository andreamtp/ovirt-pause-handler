#!/usr/bin/env python

# snmptrap-pause-handler - rev. 0.1
# Copyright (C) 2017 Andrea Perotti <aperotti@redhat.com>
# Copyright (C) 2017 Francesco Ricci <f.ricci@lumit.it>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# From: /usr/share/doc/ovirt-engine/mibs/OVIRT-MIB.txt
#
#virtEngineNotifierVmName OBJECT-TYPE
#    SYNTAX      OCTET STRING
#    MAX-ACCESS  accessible-for-notify
#    STATUS      current
#    DESCRIPTION
#        "The name of the vm associated with the audit event(optional)."
#::= { ovirtEngineNotifierObjectsAudit 102 }
#
#ovirtEngineNotifierVmId OBJECT-TYPE
#    SYNTAX      OCTET STRING
#    MAX-ACCESS  accessible-for-notify
#    STATUS      current
#    DESCRIPTION
#        "The uuid of the vm associated with the audit event(optional)."
#::= { ovirtEngineNotifierObjectsAudit 103 }

import sys
import re
from time import sleep

# from rhev:
from ovirtsdk.api import API
from ovirtsdk.infrastructure import errors
from ovirtsdk.xml import params


for arg in sys.argv[1:]:
  print arg


stdin = sys.stdin.read().splitlines()

host = stdin[0]
ip = stdin[1]
vmname = ''
vmid = ''

for line in stdin[2:]:
        patternName = re.compile("SNMPv2-SMI::enterprises.2312.13.1.1.2.1.102")
        patternID = re.compile("SNMPv2-SMI::enterprises.2312.13.1.1.2.1.103")

        if patternName.match(line):
            vmname = line.split()[1]
        elif patternID.match(line):
            vmid = line.split()[1]

print ( 'host: ' + host + '; ip:' + ip + ';VM Name: ' + vmname + '; VM ID:' + vmid  + ';')


def connect():
    api_url = "https://manager/ovirt-engine/api"
    api_user = "user@internal"
    api_password = "password"
    api_ca = "/path/to/my.cer"

    try:
        api = API ( url=api_url, username=api_user, password=api_password, ca_file=api_ca)
        return api
    except Exception as e:
        sys.exit("api connection failed: %s" % e)


def changeState(vmName, toState, waitExecution = True):
        print "vm name: %s" % vmName
        vm = api.vms.get(name=vmName)
        if (vm == None) or (vm.name != vmName):
            print "vm not found: %s" % vmName
            return 3
        print "current state: %s" % vm.status.state
        print "wanted state: %s" % toState
#        print waitExecution
        if waitExecution:
            print "I will wait the command execution"
        try:
            if toState == 'up':
                vm.start()
                if waitExecution:
                    while api.vms.get(vmName).status.state != 'up':
                        sleep(1)
                    print "vm %s is now up" % vmName
            elif toState == 'down':
                vm.stop()
                if waitExecution:
                    while api.vms.get(vmName).status.state != 'down':
                        sleep(1)
                    print "vm %s is now down" % vmName
            elif toState == 'suspended':
                vm.suspend()
                if waitExecution:
                    while api.vms.get(vmName).status.state != 'suspended':
                        sleep(1)
                    print "vm %s is now suspended" % vmName
            else:
                print "unknown or unsupported wanted state: %s" % toState
                return 4
        except errors.RequestError as e:
            print vm.name
            print e.detail.lower()

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print "You must specify one and only one wanted state"
        sys.exit(2)
    else:
        print "testing the api connection..."
        myApi = connect()
        res = myApi.test()
        print "result: %s" % res
        toState = sys.argv[1]
        changeState(vmname[1:-1], toState)
