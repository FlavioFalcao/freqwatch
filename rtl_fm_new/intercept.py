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

import MySQLdb

CONF_FILE  = 'freqwatch.conf'
ERR        = 1
FW_VERSION = 'v0.1'


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

    try:
        con =MySQLdb.connect(params.getparam('db_ip'), params.getparam('db_user'), params.getparam('db_pass'), params.getparam('db_db'))
        cur = con.cursor()
    except MySQLdb.Error, e:
        print("Error {}: {}".format(e.args[0], e.args[1]))
        sys.exit(ERR)

    sql = "SELECT data FROM {} ORDER BY date, time".format(params.getparam('db_mon_table'))
    cur.execute(sql)
    rows = cur.fetchall()

    output = ''
    for r in rows:
        output+=''.join(r[0])

    fd = open("output", 'wb')
    fd.write(output)
    fd.close()


if __name__ == '__main__':
    main()

