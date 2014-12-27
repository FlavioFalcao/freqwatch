# Freqwatch v0.1
Joshua Davis (freqwatch -!- covert.codes)  
http://covert.codes/freqwatch/


Introduction
============

* Explore vast regions of the RF spectrum

* Log radio activity to a mysql database for trend analysis

* Delegate scanners to find radio traffic and log it

* Delegate monitors to store interesting data in the database


Usage
=====

* Install (see the INSTALL file)

* Use the 'blacklist' file to prevent frequency ranges from showing up in
  your database / output

* Configure some sticks as scanners using freqwatch.conf.  Scanners scan
  frequency ranges and log signals above a defined threshold to the database,
  in the 'freqs' table.

* Configure other sticks as monitors by using the modified rtl_fm included.
  Use regular rtl_fm options to specify frequency ranges (several to scan
  different frequencies), etc.  The output will be logged to the database
  'intercepts' table.

* See the freqwatch.conf file for examples


Security Note
==============

You should run freqwatch in a controlled environment (e.g. with the web and
database servers on localhost, and a firewall blocking the relevant ports
from outsiders.)


Bugs
====

Please send bugs to freqwatch -!- covert.codes

