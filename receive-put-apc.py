#!/usr/bin/env python
# Multicast client
# Adapted from: http://chaos.weblogs.us/archives/164
# http://stackoverflow.com/questions/15197569/any-small-program-to-receive-multicast-packets-on-specified-udp-port
# http://stackoverflow.com/questions/603852/multicast-in-python

import argparse, ConfigParser, inspect
import os, sys, time, signal, threading
from Queue import Queue
from mListener import mListenerThread
from mMessage import mMessage
from mApcMessage import mApcMessage
import urllib2


# Absolute directory of the execution script
# Allows for finding config file even when the script is executed from
# another location
dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))


# Gracefully handle exit requests
# http://stackoverflow.com/questions/1112343/how-do-i-capture-sigint-in-python
def signal_handler(signal, frame):
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)


# Process arguments passed at the command line
parser = argparse.ArgumentParser(usage='%(prog)s [options]', description='Broadcast data to multicast audience.')
parser.add_argument('-c', '--config-file', required=False, default=dir+'/config.ini', nargs='?', dest='config', help='Path to config file')
parser.add_argument('-g', '--multicast-group', required=False, nargs='?', dest='group', help='Multicast group/address')
parser.add_argument('-k', '--shared-key', required=False, nargs='?', dest='key', help='Shared key. Overrides key from config file')
parser.add_argument('-p', '--multicast-port', required=False, nargs='?', dest='port', help='UDP port to use')
parser.add_argument('-v', '--debug', required=False, action='store_true', dest='debug', help='Debug mode')
args, unk = parser.parse_known_args()


# Process the config file
config_parser = ConfigParser.SafeConfigParser()
config_parser.read(args.config)


# Generate a configuration object
config = {}
config['q'] = Queue()
config['ANY'] = "0.0.0.0"
config['DEBUG'] = args.debug
config['MCAST_GRP'] = config_parser.get('Network', 'multicast_group') if args.group is None else args.group
config['MCAST_PORT'] = config_parser.getint('Network', 'multicast_port') if args.port is None else int(args.port)
config['SHARED_KEY'] = config_parser.get('Security', 'shared_key', 1) if args.key is None else args.key


# Create an instance of the multicast listener
mlistener = mListenerThread(config)


while threading.active_count() > 0:

    try:
        # Grab a message from the queue if one is available
        m = config['q'].get_nowait()
        apc = mApcMessage(m)

        influxhostport="raspberrypi.local:8086"
        influxdatabase="power"

        url     = "http://{0}/write?db={1}&precision=s".format(influxhostport, influxdatabase)

        epoch   = int(time.time())
        upsname = apc.getFieldValue('UPSNAME').replace(' ', '_')
        model   = apc.getFieldValue('MODEL').replace(' ', '_')

        measurements = { \
              'power_line_volts': 'LINEV' \
            , 'power_load_pct': 'LOADPCT' \
            , 'power_battery_volts': 'BATTV' \
            , 'power_minutes_left': 'TIMELEFT' \
            , 'power_battery_charge_pct': 'BCHARGE' \
            , 'power_seconds_on_battery': 'TONBATT' \
        }

        for table, field in measurements.iteritems():
            submission="{0},name={1},model={2} value={3} {4}".format(\
                  table \
                , upsname \
                , model \
                , apc.getFieldValue(field) \
                , epoch \
            )

            try:
                req    = urllib2.Request(url, headers={'Content-Type': 'text/plain'})
                result = urllib2.urlopen(url=req, data=submission, timeout=5)

            except Exception as e:
                print "Attempted to send '{0}'".format(submission)
                print e


        # Handle status separately because it's a non-numeric value
        table="power_status"
        field="STATUS"
        submission="{0},name={1},model={2} value=\"{3}\" {4}".format(\
              table \
            , upsname \
            , model \
            , apc.getFieldValue(field).lower() \
            , epoch \
        )

        try:
            req    = urllib2.Request(url, headers={'Content-Type': 'text/plain'})
            result = urllib2.urlopen(url=req, data=submission, timeout=5)

        except (urllib2.URLError, urllib2.HTTPError) as e:
            print "Attempted to send '{0}'".format(submission)
            print e.reason

        # BATTV, MODEL, TIMELEFT, BCHARGE, TONBATT, LINEV, STATUS, LOADPCT, UPSNAME
        # power_status,name=upsname,model=model value=STATUS epoch
        # power_load,upsname,model
        # power_line_volts,upsname,model
        # power_battery_volts,upsname,model
        # power_timeleft,upsname,model
        # power_battery_charge,upsname,model
        # power_time_on_battery,upsname,model



        config['q'].task_done()

    except Exception as e:
        # print e
        # If no messages are available, just wait a moment and try again
        time.sleep(0.5)
