#!/usr/bin/env python2
# freqwatch v0.1
#
# Joshua Davis (freqwatch -*- covert.codes)
# http://covert.codes
# Copyright(C) 2014
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from __future__ import division

import cgi
import MySQLdb
import math
import os
import signal
import sys
import threading
import time
from rtlsdr import RtlSdr
from subprocess import Popen, PIPE

sigint_handled = 0
stop = threading.Event()

BLACKLIST_FILE = 'blacklist'
CONF_FILE = 'freqwatch.conf'
ERR              = 1
FW_VERSION       = 'v0.1'


class Param:
    def __init__(self, param_list):
        self.params = param_list

    def getparam(self, name):
        for p in self.params:
            if p[0].strip() == name:
                try:
                    return p[1].strip()
                except:
                    return None

        return None


class Scanner():
    def __init__(self, devid, freqs, squelch, ppm, params):
        self.devid = devid
        self.freqs = freqs
        self.squelch = squelch
        self.ppm = ppm
        self.cmd = params.getparam('rtl_path')+'/rtl_power'
        self.delay = float(params.getparam('collection_delay'))
        self.params = params
        self.db_scan_table = params.getparam('db_scan_table')

        self.devnull = open(os.devnull, 'w')

        try:
            self.db = MySQLdb.connect(host=params.getparam('db_ip'), \
                                      port=int(params.getparam('db_port')), \
                                      user=params.getparam('db_user'), \
                                      passwd=params.getparam('db_pass'), \
                                      db=params.getparam('db_db'))

            self.db.autocommit(False)
            self.cursor = self.db.cursor()

        except MySQLdb.Error, e:
            print("MySQL Error [{}]: {}".format(e.args[0], e.args[1]))

        self.sql = ('INSERT INTO {} (date, time, freq, power) VALUES ''(%s, %s, %s, %s)'.format(self.db_scan_table))

        # blacklist
        self.blacklist = list()
        blines = None
        try:
            with open(BLACKLIST_FILE) as bfile:
                blines = bfile.readlines()

        except:
            print("Could not import from blacklist file {}".format(BLACKLIST_FILE))

        if blines != None:
            for b in blines:
                if b[0] == '#' or '-' not in b:
                    continue

                try:
                    f1, f2 = b.split('-')
                    self.blacklist.append([int(f1), int(f2)])
                except:
                    pass


    def worker(self):
        print("Scanner thread running for device {}".format(self.devid))

        while not stop.isSet():
            p = Popen([self.cmd, "-d {}".format(self.devid), "-f {}".format(self.freqs), \
                    "-1", "-p {}".format(self.ppm)], stdout=PIPE, stderr=self.devnull)

            data = p.communicate()[0].strip()
            rc = p.returncode

            if rc != 0:
                print("rtl-power exited with error code that was not 0({}); "\
                        "thread terminating".format(rc))

            for tmp in data.split('\n'):
                if stop.isSet():
                    return

                try:
                    d, t, freq_low, freq_high, freq_step, samples, \
                            raw_readings = tmp.split(', ', 6)
                    freq_low = float(freq_low)
                    freq_step = float(freq_step)

                    readings = [x.strip() for x in raw_readings.split(',')]
                except:
                    print("exiting either because sticks not connected, or ctrl-c")
                    sys.exit(0)

                for i in range(len(readings)):
                    f = freq_low+(freq_step*i)

                    if self.blacklisted(f) == True:
                        continue

                    r = float(readings[i])

                    if r > self.squelch:
                        self.insertdb(d, t, f, r)

            self.db.commit()
            time.sleep(self.delay)

        return


    def blacklisted(self, freq):
        for b in self.blacklist:
            if freq > b[0] and freq < b[1]:
                return True

        return False


    def insertdb(self, d, t, freq, power):
        try:
            self.cursor.execute(self.sql, (d, t, freq, power))

        except MySQLdb.Error, e:
            self.db.rollback()
            print("MySQL Error [{}]: {}".format(e.args[0], e.args[1]))
            sys.exit(ERR)


class Collector():
    def __init__(self, params):
        scanners = params.getparam('scanners')
        if scanners == None:
            print("No scanners defined in the configuration file.")
            sys.exit(ERR)

        threads = list()
        devs = list()

        for s in scanners.split(','):
            devid = s.strip()
            if len(devid) == 0:
                continue

            if int(devid) in devs:
                print("You already have assigned the device id {}".format(devid))
                sys.exit(ERR)
            devs.append(int(devid))

            freqs, squelch, ppm = params.getparam('scanner'+s).split('/')
            if freqs == None:
                print("Is there a frequency entry for each device you've " \
                        "specified in 'scanners' in the configuration?")
                sys.exit(ERR)

            freqs = freqs.strip()
            squelch = int(squelch.strip())
            ppm = ppm.strip()
            if len(ppm) == 0:
                ppm = 0
            else:
                ppm = int(ppm)

            sworker = Scanner(devid, freqs, squelch, ppm, params)
            thread = threading.Thread(target=sworker.worker)
            threads.append(thread)
            thread.start()

        for t in threads:
            t.join()


def main():
    try:
        with open(CONF_FILE) as cfile:
            lines = cfile.readlines()
    except:
        print("Could not open configuration file {}".format(CONF_FILE))
        sys.exit(ERR)

    param_list = list()

    for l in lines:
        l = l.strip()
        if len(l) == 0 or l[0] == '#':
            continue

        p = l.split('=')
        if len(p) != 2:
            continue

        param_list.append(p)

    params = Param(param_list)
    c = Collector(params)


def sigint_handler(signal, frame):
    global sigint_handled

    if sigint_handled == 0:
        print("SIGINT received.  Stopping...")
        stop.set()
        sigint_handled = 1


if __name__ == '__main__':
    signal.signal(signal.SIGINT, sigint_handler)

    main()

