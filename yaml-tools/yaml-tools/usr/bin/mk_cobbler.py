#!/usr/bin/python

#
# SCRIPT
#   mk_cobbler.py
# DESCRIPTION
#   Create a Cobbler script from a node YAML file. The node
#   YAML file must have the "machine" key.
# DEPENDENCIES
# FAILURE
# AUTHORS
#   Date strings made with 'date +"\%Y-\%m-\%d \%H:\%M"'.
#   Allard Berends (AB), 2014-07-27 10:30
# HISTORY
# LICENSE
#   Copyright (C) 2014 Allard Berends
# 
#   mk_cobbler.py is free software; you can redistribute it
#   and/or modify it under the terms of the GNU General
#   Public License as published by the Free Software
#   Foundation; either version 3 of the License, or (at your
#   option) any later version.
#
#   mk_cobbler.py is distributed in the hope that it will be
#   useful, but WITHOUT ANY WARRANTY; without even the
#   implied warranty of MERCHANTABILITY or FITNESS FOR A
#   PARTICULAR PURPOSE. See the GNU General Public License
#   for more details.
#
#   You should have received a copy of the GNU General
#   Public License along with this program; if not, write to
#   the Free Software Foundation, Inc., 59 Temple Place -
#   Suite 330, Boston, MA 02111-1307, USA.
# DESIGN
#

import ipaddr
import iptools
import optparse
import sys
import time
import yaml

machine_types = ['dl3x0', 'kvm', 'rhev']

def print_dl3x0_prod():
  print '''$COBBLER system edit \\
  --name=${ORG}_${MACH}_${P}${NAME} \\
  --interface=${ETH1_NAME} \\
  --mac=${MAC_ETH1} \\
  --bonding=subordinate \\
  --bonding-main=bond0

$COBBLER system edit \\
  --name=${ORG}_${MACH}_${P}${NAME} \\
  --interface=${ETH2_NAME} \\
  --mac=${MAC_ETH2} \\
  --bonding=subordinate \\
  --bonding-main=bond0

$COBBLER system edit \\
  --name=${ORG}_${MACH}_${P}${NAME} \\
  --interface=bond0 \\
  --mac=${MAC_ETH1} \\
  --bonding=main \\
  --bonding-opts="mode=1 primary=${ETH1_NAME} miimon=100" \\
  --static=1 \\
  --ip-address=${PROD_IP} \\
  --subnet=${PROD_SUBNET_MASK} \\
  --dns-name=${DNS_NAME} \\
  --dhcp-tag=${DHCP_TAG}'''

def print_dl3x0_cic():
  print '''$COBBLER system edit \\
  --name=${ORG}_${MACH}_${P}${NAME} \\
  --interface=${ETH3_NAME} \\
  --mac=${MAC_ETH3} \\
  --bonding=subordinate \\
  --bonding-main=bond1

$COBBLER system edit \\
  --name=${ORG}_${MACH}_${P}${NAME} \\
  --interface=${ETH4_NAME} \\
  --mac=${MAC_ETH4} \\
  --bonding=subordinate \\
  --bonding-main=bond1

$COBBLER system edit \\
  --name=${ORG}_${MACH}_${P}${NAME} \\
  --interface=bond1 \\
  --mac=${MAC_ETH3} \\
  --bonding=main \\
  --bonding-opts="mode=1 primary=${ETH3_NAME} miimon=100" \\
  --static=1 \\
  --ip-address=${CLUSTER_IP} \\
  --subnet=${CLUSTER_SUBNET_MASK} \\
  --dhcp-tag=${DHCP_TAG}'''

def print_dl3x0_ext1():
  print '''$COBBLER system edit \\
  --name=${ORG}_${MACH}_${P}${NAME} \\
  --interface=${ETH5_NAME} \\
  --mac=${MAC_ETH5} \\
  --static=1 \\
  --ip-address=${EXT1_IP} \\
  --subnet=${EXT1_SUBNET_MASK}'''

def print_dl3x0_ext2():
  print '''$COBBLER system edit \\
  --name=${ORG}_${MACH}_${P}${NAME} \\
  --interface=${ETH6_NAME} \\
  --mac=${MAC_ETH6} \\
  --static=1 \\
  --ip-address=${EXT2_IP} \\
  --subnet=${EXT2_SUBNET_MASK}'''

def print_dl3x0_bck(n):
  d = {'n': n}
  print '''$COBBLER system edit \\
  --name=${ORG}_${MACH}_${P}${NAME} \\
  --interface=${ETH%(n)d_NAME} \\
  --mac=${MAC_ETH%(n)d} \\
  --static=1 \\
  --ip-address=${BCK_IP} \\
  --subnet=${BCK_SUBNET_MASK}''' % d

def print_dl3x0_adm(n):
  d = {'n': n}
  print '''$COBBLER system edit \\
  --name=${ORG}_${MACH}_${P}${NAME} \\
  --interface=${ETH%(n)d_NAME} \\
  --mac=${MAC_ETH%(n)d} \\
  --static=1 \\
  --ip-address=${ADMIN_IP} \\
  --subnet=${ADMIN_SUBNET_MASK}''' % d

def print_kvm_prod():
  print '''$COBBLER system edit \\
  --name=${ORG}_${MACH}_${P}${NAME} \\
  --interface=${ETH1_NAME} \\
  --mac=${MAC_ETH1} \\
  --static=1 \\
  --ip-address=${PROD_IP} \\
  --subnet=${PROD_SUBNET} \\
  --dns-name=${DNS_NAME}'''

def print_kvm_nic(n, name):
  d = {'n': n, 'name': name}
  print '''$COBBLER system edit \\
  --name=${ORG}_${MACH}_${P}${NAME} \\
  --interface=${ETH%(n)d_NAME} \\
  --mac=${MAC_ETH%(n)d} \\
  --static=1 \\
  --ip-address=${%(name)s_IP} \\
  --subnet=${%(name)s_SUBNET_MASK}''' % d

def check_parameters(d, depzone, dns):
  global machine_types
  if not d['machine']['machinetype'] in machine_types:
    print >> sys.stderr, "ERROR: machine type \"%s\" not in \"%s\"" % (d['machine']['machinetype'], ' '.join(machine_types))
    sys.exit(1)

def print_cobbler(d, depzone, org, dns):
  # Mandatory parameters first.
  params = {
    't':       time.strftime("%Y-%m-%d %H:%M", time.localtime()),
    'y':       time.strftime("%Y", time.localtime()),
    'depzone': depzone,
    'machine': d['machine']['aliases']['p'][0],
    'fqdn':    d['machine']['fqdn']['p'],
    'domain':  '.'.join(d['machine']['fqdn']['p'].split('.')[1:]),
    'mach':    d['machine']['machinetype'],
    'comment': d['machine']['description'],
    'pip':     d['machine']['ipv4']['p'].split('/')[0],
    'spip':    "%s/%s" % (
      iptools.ipv4.cidr2block(d['machine']['ipv4']['p'])[0],
      d['machine']['ipv4']['p'].split('/')[1]
    ),
    'mpip':    str(ipaddr.IPv4Network(d['machine']['ipv4']['p']).netmask),
    'dpip':    d['machine']['ipv4']['dp'],
    'org':     org,
    'dnsip':   ' '.join(dns),
    'prov':    d['machine']['provisioning'],
  } # end of params

  for index, item in enumerate(d['machine']['nics']):
    nic = "nic%d" % (index,)
    params[nic] = item

  # Optional parameters second.
  if 'c' in d['machine']['ipv4']:
    params['cip']  = d['machine']['ipv4']['c'].split('/')[0]
    params['scip'] = "%s/%s" % (
      iptools.ipv4.cidr2block(d['machine']['ipv4']['c'])[0],
      d['machine']['ipv4']['c'].split('/')[1]
    )
    params['mcip'] = str(ipaddr.IPv4Network(d['machine']['ipv4']['c']).netmask)
  else:
    params['cip']  = ''
    params['scip'] = ''
    params['mcip'] = ''
  if 'ilo' in d['machine']['ipv4']:
    params['iip']  = d['machine']['ipv4']['ilo'].split('/')[0]
    params['siip'] = "%s/%s" % (
      iptools.ipv4.cidr2block(d['machine']['ipv4']['ilo'])[0],
      d['machine']['ipv4']['ilo'].split('/')[1]
    )
    params['miip'] = str(ipaddr.IPv4Network(d['machine']['ipv4']['ilo']).netmask)
    params['diip'] = d['machine']['ipv4']['dilo']
  else:
    params['iip']  = ''
    params['siip'] = ''
    params['miip'] = ''
    params['diip'] = ''
  if 'ext1' in d['machine']['ipv4']:
    params['e1ip']  = d['machine']['ipv4']['ext1'].split('/')[0]
    params['se1ip'] = "%s/%s" % (
      iptools.ipv4.cidr2block(d['machine']['ipv4']['ext1'])[0],
      d['machine']['ipv4']['ext1'].split('/')[1]
    )
    params['me1ip'] = str(ipaddr.IPv4Network(d['machine']['ipv4']['ext1']).netmask)
    params['de1ip'] = d['machine']['ipv4']['dext1']
  else:
    params['e1ip']  = ''
    params['se1ip'] = ''
    params['me1ip'] = ''
    params['de1ip'] = ''
  if 'ext2' in d['machine']['ipv4']:
    params['e2ip']  = d['machine']['ipv4']['ext2'].split('/')[0]
    params['se2ip'] = "%s/%s" % (
      iptools.ipv4.cidr2block(d['machine']['ipv4']['ext2'])[0],
      d['machine']['ipv4']['ext2'].split('/')[1]
    )
    params['me2ip'] = str(ipaddr.IPv4Network(d['machine']['ipv4']['ext2']).netmask)
    params['de2ip'] = d['machine']['ipv4']['dext2']
  else:
    params['e2ip']  = ''
    params['se2ip'] = ''
    params['me2ip'] = ''
    params['de2ip'] = ''
  if 'bck' in d['machine']['ipv4']:
    params['bip']  = d['machine']['ipv4']['bck'].split('/')[0]
    params['sbip'] = "%s/%s" % (
      iptools.ipv4.cidr2block(d['machine']['ipv4']['bck'])[0],
      d['machine']['ipv4']['bck'].split('/')[1]
    )
    params['mbip'] = str(ipaddr.IPv4Network(d['machine']['ipv4']['bck']).netmask)
    params['dbip'] = d['machine']['ipv4']['dbck']
  else:
    params['bip']  = ''
    params['sbip'] = ''
    params['mbip'] = ''
    params['dbip'] = ''
  if 'adm' in d['machine']['ipv4']:
    params['aip']  = d['machine']['ipv4']['adm'].split('/')[0]
    params['saip'] = "%s/%s" % (
      iptools.ipv4.cidr2block(d['machine']['ipv4']['adm'])[0],
      d['machine']['ipv4']['adm'].split('/')[1]
    )
    params['maip'] = str(ipaddr.IPv4Network(d['machine']['ipv4']['adm']).netmask)
    params['daip'] = d['machine']['ipv4']['dadm']
  else:
    params['aip']  = ''
    params['saip'] = ''
    params['maip'] = ''
    params['daip'] = ''

  print '''#!/bin/bash
#
# SCRIPT
#   cobbler-%(machine)s.sh
# DESCRIPTION
#   This script should be run on the Satellite server:
#   # ./cobbler-%(machine)s.sh
#
#   IP details
#
#   Host     Prod            Cluster         ILO
#   %(machine)-8.8s %(pip)-15.15s %(cip)-15.15s %(iip)-15.15s
#            EXT1            EXT2
#            %(e1ip)-15.15s %(e2ip)-15.15s
#            Backup          Admin
#            %(bip)-15.15s %(aip)-15.15s
#
#   Subnets:
#   P:  %(spip)-18.18s gw: %(dpip)s
#   C:  %(scip)s
#   I:  %(siip)-18.18s gw: %(diip)s
#   E1: %(se1ip)-18.18s gw: %(de1ip)s
#   E2: %(se2ip)-18.18s gw: %(de2ip)s
#   B:  %(sbip)-18.18s gw: %(dbip)s
#   A:  %(saip)-18.18s gw: %(daip)s
#
#   DNS servers:
#   * %(dnsip)s
#
# ARGUMENTS
#   None.
# RETURN
#   Value from cobbler command. See cobbler man page.
# DEPENDENCIES
#   The profile should not yet exist in cobbler. If it does,
#   remove it with:
#   sudo cobbler system remove --name=%(org)s_%(mach)s_%(machine)s
#   Adding an existing profile results in a clear warning
#   from cobbler. No harm is done.
# FAILURE
# AUTHORS
#   Date strings made with 'date +"\%%Y-\%%m-\%%d \%%H:\%%M"'.
#   Allard Berends (AB), %(t)s
# HISTORY
# LICENSE
#   Copyright (C) %(y)s Allard Berends
# 
#   cobbler-%(machine)s.sh is free software; you can redistribute
#   it and/or modify it under the terms of the GNU General
#   Public License as published by the Free Software
#   Foundation; either version 3 of the License, or (at your
#   option) any later version.
#
#   cobbler-%(machine)s.sh is distributed in the hope that it will
#   be useful, but WITHOUT ANY WARRANTY; without even the
#   implied warranty of MERCHANTABILITY or FITNESS FOR A
#   PARTICULAR PURPOSE. See the GNU General Public License
#   for more details.
#
#   You should have received a copy of the GNU General
#   Public License along with this program; if not, write to
#   the Free Software Foundation, Inc., 59 Temple Place -
#   Suite 330, Boston, MA 02111-1307, USA.
# DESIGN
#

COBBLER="sudo cobbler"
# AB: extra Spacewalk organizations have != 1
ORGNUM="$(msat_ls_org.py)"

########## PARAMETERS TO EDIT ##########
NAME="%(machine)s"
DEPZONE="%(depzone)s"
OWNERS="example"
PROFILE="bare-%(mach)s-6u5-x_y_z"
ORG="%(org)s"
MACH="%(mach)s"
COMMENT="%(comment)s"
GATEWAY="%(dpip)s"
NAMESERVERS="%(dnsip)s"
NAMESERVERS_SEARCH="%(domain)s"
HOSTNAME="%(fqdn)s"
PROD_IP="%(pip)s"
PROD_SUBNET_MASK="%(mpip)s"
PROD_DNS_NAME="${HOSTNAME}"''' % params

  if params['cip']:
    print 'CLUSTER_IP="%s"' % (params['cip'],)
    print 'CLUSTER_SUBNET_MASK="%s"' % ipaddr.IPv4Network(params['scip']).netmask

  if params['e1ip']:
    print 'EXT1_IP="%s"' % (params['e1ip'],)
    print 'EXT1_SUBNET_MASK="%s"' % ipaddr.IPv4Network(params['se1ip']).netmask

  if params['e2ip']:
    print 'EXT2_IP="%s"' % (params['e2ip'],)
    print 'EXT2_SUBNET_MASK="%s"' % ipaddr.IPv4Network(params['se2ip']).netmask

  if params['bip']:
    print 'BCK_IP="%s"' % (params['bip'],)
    print 'BCK_SUBNET_MASK="%s"' % ipaddr.IPv4Network(params['sbip']).netmask

  if params['aip']:
    print 'ADMIN_IP="%s"' % (params['aip'],)
    print 'ADMIN_SUBNET_MASK="%s"' % ipaddr.IPv4Network(params['saip']).netmask

  if params['mach'] in ['kvm', 'rhev']:
    # AB: we keep the following order:
    # * nic1: production
    # * nic2: cluster interconnect, if cip exists
    # * nic3: ext1, if e1ip exists
    # * nic4: ext2, if e2ip exists
    # * nic5: backup, if bip exists
    # * nic6: admin, if aip exists
    for index, item in enumerate(d['machine']['nics']):
      print 'MAC_ETH%d="%s"' % (index + 1, item)
    for index, item in enumerate(d['machine']['nics']):
      print 'ETH%d_NAME="em%d"' % (index + 1, index + 1)
    print 'KSDEV="${MAC_ETH1}"'

  elif params['mach'] == 'dl3x0':
    # AB: 4 means:
    # * nic1 and nic2: production
    # * nic3: backup
    # * nic4: admin
    # AB: 8 means:
    # * nic1 and nic2: production
    # * nic3 and nic4: cluster
    # * nic5: external network 1
    # * nic6: external network 2
    # * nic7: backup
    # * nic8: admin
    l = len(d['machine']['nics'])
    if l != 4 and l != 8:
      print >> sys.stderr, "ERROR, machine type dl3x0 requires 4 or 8 NICs"
      sys.exit(1)
    print '''MAC_ETH1="%(nic0)s"
MAC_ETH2="%(nic1)s"
MAC_ETH3="%(nic2)s"
MAC_ETH4="%(nic3)s"''' % params
    if l == 8:
      print '''MAC_ETH5="%(nic4)s"
MAC_ETH6="%(nic5)s"
MAC_ETH7="%(nic6)s"
MAC_ETH8="%(nic7)s"''' % params

    print '''ETH1_NAME="em1"
ETH2_NAME="em2"
ETH3_NAME="em3"
ETH4_NAME="em4"'''

    if l == 8:
      print '''ETH5_NAME="em5"
ETH6_NAME="em6"
ETH7_NAME="em7"
ETH8_NAME="em8"'''

    if l == 4:
      print 'KSDEV="${MAC_ETH4}"'
    else:
      print 'KSDEV="${MAC_ETH8}"'

  if d['machine']['use_proxy'] == 'yes':
    print 'PROXY="%s"' % (params['prov'],)
    print 'P="proxy_"'
  else:
    print 'P=""'

  print
  print '''$COBBLER system list | grep -q ${ORG}_${MACH}_${P}${NAME}$
if [ $? -eq 0 ]; then
  echo "$NAME already exists. Removing system ...."
  $COBBLER system remove --name=${ORG}_${MACH}_${P}${NAME}
fi'''

  print
  print '''########## START SCRIPT ##########
$COBBLER system add \\
  --name=${ORG}_${MACH}_${P}${NAME} \\
  --owners=${OWNERS} \\
  --profile=${PROFILE}:${ORGNUM}:${ORG} \\
  --kopts="ip=${PROD_IP} netmask=${PROD_SUBNET} ksdevice=${KSDEV} hostname=${HOSTNAME} depzone=${DEPZONE} ipv6.disable=1 biosdevname=1" \\
  --kopts-post="ipv6.disable=1 biosdevname=1" \\
  --netboot-enabled=0 \\
  --comment=${COMMENT} \\
  --power-type=ipmitool \\
  --hostname=${HOSTNAME} \\
  --gateway=${GATEWAY} \\
  --name-servers="$NAMESERVERS" \\
  --name-servers-search=$NAMESERVERS_SEARCH \\
  --redhat-management-key='<<inherit>>' \\'''

  if d['machine']['use_proxy'] == 'yes':
    print '''  --redhat-management-server='<<inherit>>' \\
  --server=$PROXY'''
  else:
    print '''  --redhat-management-server='<<inherit>>\''''

  print
  if params['mach'] == 'dl3x0':
    print_dl3x0_prod()
    if params['cip']:
      print
      print_dl3x0_cic()
      if params['e1ip']:
        print
        print_dl3x0_ext1()
      if params['e2ip']:
        print
        print_dl3x0_ext2()
      if params['bip']:
        print
        print_dl3x0_bck(7)
      if params['aip']:
        print
        print_dl3x0_adm(8)
    else:
      if params['bip']:
        print
        print_dl3x0_bck(3)
      if params['aip']:
        print
        print_dl3x0_adm(4)
  elif params['mach'] == 'kvm':
    print_kvm_prod()
    int = 2
    if params['cip']:
      print
      print_kvm_nic(int, 'CLUSTER')
      int += 1
    if params['e1ip']:
      print
      print_kvm_nic(int, 'EXT1')
      int += 1
    if params['e2ip']:
      print
      print_kvm_nic(int, 'EXT2')
      int += 1
    if params['bip']:
      print
      print_kvm_nic(int, 'BCK')
      int += 1
    if params['aip']:
      print
      print_kvm_nic(int, 'ADMIN')
      int += 1

usage = '''usage: %prog [options] <node YAML file>'''

description = '''This script creates a Cobbler script from a node YAML file.'''

parser = optparse.OptionParser(
  usage = usage,
  description = description,
)
parser.add_option(
  "-d",
  "--deployment-zone",
  dest = "deployment_zone",
  default = None,
  help = "Deployment zone in which this system is deployed",
)
parser.add_option(
  "-s",
  "--dns-server",
  dest = "dns_servers",
  default = None,
  help = "IP or comma separated list of IPs of DNS server(s) used for deployment",
)
parser.add_option(
  "-o",
  "--spacewalk-org",
  dest = "spacewalk_org",
  default = None,
  help = "Organization name on Spacewalk used for deployment",
)
(options, args) = parser.parse_args()

if not options.deployment_zone:
  parser.error('Error: specify Deployment zone, -d or --deployment-zone')
if not options.spacewalk_org:
  parser.error('Error: specify Spacewalk org, -o or --spacewalk-org')
if not options.dns_servers:
  parser.error('Error: specify DNS server(s), -s or --dns-server')

if len(args) != 1:
  parser.error('Error: specify node YAML file as first argumanent')

dns = options.dns_servers.split(',')

yaml_file = args[0]
try:
  f = open(yaml_file, 'r')
except IOError, e:
  print >> sys.stderr, str(e)
  sys.exit(1)

d = yaml.load(f)
f.close()
print_cobbler(d, options.deployment_zone, options.spacewalk_org, dns)
