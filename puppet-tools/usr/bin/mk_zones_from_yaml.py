#!/usr/bin/python

#
# SCRIPT
#   mk_cobbler.py
# DESCRIPTION
#   Create a Cobbler script from a YAML file.
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

import optparse
import os
import os.path
import sys
import time
import yaml

fqdn_keys = ['p', 'ilo', 'ext1', 'ext2', 'bck', 'adm']
serial    = time.strftime("%Y%m%d%H", time.localtime())

def node_to_dns(y, d, z, nameserver):
  global fqdn_keys
  global serial
  for k in fqdn_keys:
    try:
      if k in d['machine']['fqdn']:
        hostname, sep, domainname = d['machine']['fqdn'][k].partition('.')
        if not domainname in z['zones']:
          z['zones'][domainname] = {
            'ttl':        86400,
            'nameserver': nameserver,
            'serial':     serial,
            'refresh':    '3H',
            'retry':      '15M',
            'expiry':     '1W',
            'minimum':    '1D',
            'addresses':  {hostname: d['machine']['ipv4'][k].split('/')[0]},
          }
        else:
          if hostname in z['zones'][domainname]['addresses']:
            print >> sys.stderr, "ERROR duplicate %s in %s, %s" % (hostname, domainname, y)
            sys.exit(1)
          z['zones'][domainname]['addresses'][hostname] = d['machine']['ipv4'][k].split('/')[0]
      # AB: we always make class C reverse zones!
      if k in d['machine']['ipv4']:
        quads  = d['machine']['ipv4'][k].split('/')[0].split('.')
        arpa   = '%s' % ('.'.join(quads[0:3]),)
        num    = quads[3]
        if not arpa in z['arpas']:
          z['arpas'][arpa] = {
            'ttl':        86400,
            'nameserver': nameserver,
            'serial':     serial,
            'refresh':    '3H',
            'retry':      '15M',
            'expiry':     '1W',
            'minimum':    '1D',
            'pointers':   {num: "%s" % (d['machine']['fqdn'][k],)},
          }
        else:
          if num in z['arpas'][arpa]['pointers']:
            print >> sys.stderr, "ERROR duplicate %s in %s, %s" % (num, arpa, y)
            sys.exit(1)
          z['arpas'][arpa]['pointers'][num] = "%s" % (d['machine']['fqdn'][k],)
    except KeyError, e:
      print >> sys.stderr, str(e)
      print >> sys.stderr, "ERROR: occured in %s" % (y,)
      sys.exit(1)

def write_custom_zone(z, fd):
  print >> fd, '''zone "%(zone)s." IN {
  type master;
  file "%(zone)s.zone";
  notify yes;
  allow-transfer { any; };
};
''' % {'zone': z}

def write_custom_arpa(a, fd):
  rev = a.split('.')
  rev.reverse()
  rev = '.'.join(rev)
  print >> fd, '''zone "%(rev)s.in-addr.arpa." IN {
  type master;
  file "%(arpa)s.in-addr.arpa";
  notify yes;
  allow-transfer { any; };
};
''' % {'arpa': a, 'rev': rev}

def cmp_ipv4(a, b):
  aa = a.split('.')
  la = len(aa)
  bb = b.split('.')
  lb = len(bb)
  m  = min(la, lb)
  i = 0
  while i < m:
    if int(aa[i]) < int(bb[i]): return -1
    if int(aa[i]) > int(bb[i]): return 1
    i += 1
  if la < lb: return -1
  if la > lb: return 1
  return 0

def write_custom_zones_config(d, fd):
  zones = d['zones'].keys()
  zones.sort()
  for z in zones:
    write_custom_zone(z, fd)
  arpas = d['arpas'].keys()
  arpas.sort(cmp_ipv4)
  for a in arpas:
    write_custom_arpa(a, fd)

def sorted_addresses(zone):
  d = dict((y,x) for x,y in zone['addresses'].iteritems())
  ipv4s = d.keys()
  ipv4s.sort(cmp_ipv4)
  return [d[i] for i in ipv4s]

def write_zone_file(zone, fd):
  print >> fd, '''$TTL    %(ttl)d
@       IN SOA %(nameserver)s. root.%(nameserver)s. (
        %(serial)s      ; serial, format: YYYYMMDDNN, where
      ; NN is the daily sequence number.
      ; After editing this file, always
      ; update this serial number to give
      ; slaves a chance to keep
      ; synchronized.
        %(refresh)s              ; refresh. The refresh interval
      ; tells a slave for the zone how
      ; often to check that the data for
      ; this zone is up to date.
        %(retry)s             ; retry. If a slave fails to connect
      ; to the master, it will retry in
      ; this amount of time. So here it is
      ; 15 minutes.
        %(expiry)s              ; expiry. If a slave did not contact
      ; the server for this amount of
      ; time, its records become useless,
      ; i.e. are expired.
        %(minimum)s )            ; minimum. TTL for negative
      ; responses of this nameserver for
      ; authoriative requests. So the
      ; client must not ask for the same
      ; RR (Resource Record) it got a
      ; negative response for in the
      ; specified amount of time.

;
; @ (short for domain name) is implied!
;
        IN NS   %(nameserver)s.
''' % zone
  addresses = zone['addresses']
  s = sorted_addresses(zone)
  for hostname in s:
    print >> fd, '%(hostname)-20.20s IN      A       %(ip)s' % {
      'hostname': hostname,
      'ip':       zone['addresses'][hostname]
    }

def write_arpa_file(arpa, fd):
  print >> fd, '''$TTL    %(ttl)d
@       IN SOA %(nameserver)s. root.%(nameserver)s. (
        %(serial)s      ; serial, format: YYYYMMDDNN, where
      ; NN is the daily sequence number.
      ; After editing this file, always
      ; update this serial number to give
      ; slaves a chance to keep
      ; synchronized.
        %(refresh)s              ; refresh. The refresh interval
      ; tells a slave for the zone how
      ; often to check that the data for
      ; this zone is up to date.
        %(retry)s             ; retry. If a slave fails to connect
      ; to the master, it will retry in
      ; this amount of time. So here it is
      ; 15 minutes.
        %(expiry)s              ; expiry. If a slave did not contact
      ; the server for this amount of
      ; time, its records become useless,
      ; i.e. are expired.
        %(minimum)s )            ; minimum. TTL for negative
      ; responses of this nameserver for
      ; authoriative requests. So the
      ; client must not ask for the same
      ; RR (Resource Record) it got a
      ; negative response for in the
      ; specified amount of time.

;
; @ (short for domain name) is implied!
;
        IN NS   %(nameserver)s.
''' % arpa
  pointers = arpa['pointers'].keys()
  pointers.sort(cmp_ipv4)
  for num in pointers:
    print >> fd, '%(num)-3.3s IN    PTR    %(fqdn)s.' % {
      'num':  num,
      'fqdn': arpa['pointers'][num]
    }

def write_db_zones(d, zones_dir):
  zones = d['zones'].keys()
  zones.sort()
  for z in zones:
    fd = open(os.path.join(zones_dir, '%s.zone' % (z,)), 'w')
    write_zone_file(d['zones'][z], fd)
    fd.close()
  arpas = d['arpas'].keys()
  arpas.sort(cmp_ipv4)
  for a in arpas:
    fd = open(os.path.join(zones_dir, '%s.in-addr.arpa' % (a,)), 'w')
    write_arpa_file(d['arpas'][a], fd)
    fd.close()

usage = '''usage: %prog [options] <node YAML dir>'''

description = '''This script creates DNS zone files from node YAML files. The input is the directory where the node YAML files are located. The output is a custom zone configuration file and the zone files.'''

parser = optparse.OptionParser(
  usage = usage,
  version = '1.0',
  description = description,
)
parser.add_option(
  "-c",
  "--conf-dir",
  dest = "conf_dir",
  default = '/var/named/chroot/etc',
  help = "Path of the directory where the named configuration is located",
)
parser.add_option(
  "-n",
  "--name-server",
  dest = "name_server",
  default = '@name.server@',
  help = "FQDN of the nameserver for which the zones are created",
)
parser.add_option(
  "-z",
  "--zones-dir",
  dest = "zones_dir",
  default = '/var/named/chroot/var/named',
  help = "Path of the directory where the named zone files are located",
)
(options, args) = parser.parse_args()

if not options.conf_dir:
  parser.error('Error: specify named configuration directory, -c or --conf-dir')
if not options.zones_dir:
  parser.error('Error: specify named zones directory, -z or --zones-dir')

if len(args) != 1:
  parser.error('Error: specify directory path of node YAML files')

conf_dir   = options.conf_dir
zones_dir  = options.zones_dir
nameserver = options.name_server
yaml_dir   = args[0]

# AB: Easier to Ask for Forgiveness than Permission (EAFP).
# This style is very pythonic and contrasts Look Before You
# Leap (LBYL). So, we just try to read and write in a
# try-except clause to verify if we can read yaml_dir and
# write in conf_dir in zones_dir.

yaml_files = []
try:
  yaml_files = [y for y in os.listdir(yaml_dir) if y.endswith('.yaml')]
except IOError, e:
  print >> sys.stderr, "ERROR: %s not readable" % (yaml_dir,)
  sys.exit(1)

try:
  f = open(os.path.join(conf_dir, 'dummy'), 'w')
except IOError, e:
  print >> sys.stderr, "ERROR: %s not writable" % (conf_dir,)
  sys.exit(1)
else:
  f.close()

try:
  f = open(os.path.join(zones_dir, 'dummy'), 'w')
except IOError, e:
  print >> sys.stderr, "ERROR: %s not writable" % (zones_dir,)
  sys.exit(1)
else:
  f.close()

dns_zones = {
  'zones': {},
  'arpas': {},
}

for y in yaml_files:
  try:
    f = open(os.path.join(yaml_dir, y), 'r')
  except IOError, e:
    print >> sys.stderr, str(e)
    sys.exit(1)

  d = yaml.load(f)
  f.close()
  node_to_dns(y, d, dns_zones, nameserver)

fd = open(os.path.join(conf_dir, 'named.custom.zones'), 'w')
write_custom_zones_config(dns_zones, fd)
fd.close()
write_db_zones(dns_zones, zones_dir)
