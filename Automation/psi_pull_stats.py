#!/usr/bin/python
#
# Copyright (c) 2011, Psiphon Inc.
# All rights reserved.
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
#

import os
import posixpath
import sys
import tempfile
import re
import textwrap
import gzip
import sqlite3
import traceback
import csv
import datetime
import collections
import bisect

import psi_ssh
from psi_pull_netflows import pull_netflows

sys.path.insert(0, os.path.abspath(os.path.join('..', 'Data')))
import psi_db


#==== Log File Configuration  ==================================================

HOST_LOG_DIR = '/var/log'
HOST_LOG_FILENAME_PATTERN = 'psiphonv*.log*'

STATS_ROOT = os.path.abspath(os.path.join('..', 'Data', 'Stats'))
STATS_DB_FILENAME = os.path.join(STATS_ROOT, 'stats.db')

# if psi_build_config.py exists, load it and use psi_build_config.DATA_ROOT as the data root dir

if os.path.isfile('psi_data_config.py'):
    import psi_data_config
    psi_db.set_db_root(psi_data_config.DATA_ROOT)
    STATS_ROOT = os.path.join(psi_data_config.DATA_ROOT, 'Stats')
    STATS_DB_FILENAME = os.path.join(STATS_ROOT, 'stats.db')


#==============================================================================

# Stats database schema consists of one table per event type. The tables
# have a column per log line field.
#
# The entire log line is considered to be unique. This is how we handle pulling
# down the same log file again: duplicate lines are discarded. This logic also
# handles the unlikely case where our SFTP pull happens in the middle of a
# log rotation, in which case we may pull the same log entries down twice in
# two different file names.
#
# The uniqueness assumption depends on a high resolution timestamp as it's
# likely that there will be multiple handshake events in the same second on
# the same server from the same reion and client build.

# Example log file entries:

'''
2011-06-28T13:14:04.000000-07:00 host1 psiphonv: started 192.168.1.101
2011-06-28T13:15:59.000000-07:00 host1 psiphonv: handshake 192.168.1.101 CA DA77176D642E66FB 1F277F0BD58BB84D 1
2011-06-28T13:15:59.000000-07:00 host1 psiphonv: discovery 192.168.1.101 CA DA77176D642E66FB 1F277F0BD58BB84D 1 192.168.1.102 0
2011-06-28T13:16:00.000000-07:00 host1 psiphonv: download 192.168.1.101 CA DA77176D642E66FB 1F277F0BD58BB84D 2
2011-06-28T13:16:06.000000-07:00 host1 psiphonv: connected 192.168.1.101 CA DA77176D642E66FB 1F277F0BD58BB84D 2 10.1.0.2
2011-06-28T13:16:12.000000-07:00 host1 psiphonv: disconnected 10.1.0.2
'''

# Log line parser looks for space delimited fields. Every log line has a
# timestamp, host ID, and event type. The schema array defines the additional
# fields expected for each valid event type.

LOG_LINE_PATTERN = '([\dT\.:-]+) (\w+) psiphonv: (\w+) (.+)'

LOG_ENTRY_COMMON_FIELDS = ('timestamp', 'host_id')

LOG_EVENT_TYPE_SCHEMA = {
    'started' :         ('server_id',),
    'handshake' :       ('server_id',
                         'client_region',
                         'propagation_channel_id',
                         'sponsor_id',
                         'client_version'),
    'discovery' :       ('server_id',
                         'client_region',
                         'propagation_channel_id',
                         'sponsor_id',
                         'client_version',
                         'discovery_server_id',
                         'client_unknown'),
    'connected' :       ('server_id',
                         'client_region',
                         'propagation_channel_id',
                         'sponsor_id',
                         'client_version',
                         'relay_protocol',
                         'session_id'),
    'failed' :          ('server_id',
                         'client_region',
                         'propagation_channel_id',
                         'sponsor_id',
                         'client_version',
                         'relay_protocol',
                         'error_code'),
    'download' :        ('server_id',
                         'client_region',
                         'propagation_channel_id',
                         'sponsor_id',
                         'client_version'),
    'disconnected' :    ('relay_protocol',
                         'session_id')}

# Additional stat tables that don't correspond to log line entries. Currently
# this is the session table, which is populated in post-processing that links
# connected and disconnected events.

ADDITIONAL_TABLES_SCHEMA = {
    'session' :         ('host_id',
                         'server_id',
                         'client_region',
                         'propagation_channel_id',
                         'sponsor_id',
                         'client_version',
                         'relay_protocol',
                         'session_id',
                         'session_start_timestamp',
                         'session_end_timestamp'),
    'outbound' :        ('host_id',
                         'server_id',
                         'client_region',
                         'propagation_channel_id',
                         'sponsor_id',
                         'client_version',
                         'relay_protocol',
                         'session_id',
                         'day',
                         'domain',
                         'protocol',
                         'port',
                         'flow_count',
                         'outbound_byte_count')}


def init_stats_db(db):

    # Create (if doesn't exist) a database table for each event type with
    # a column for every expected field. The primary key constaint includes all
    # table columns and transparently handles the uniqueness logic -- duplicate
    # log lines are discarded. SQLite automatically creates an index for this.

    for (event_type, event_fields) in LOG_EVENT_TYPE_SCHEMA.items() + ADDITIONAL_TABLES_SCHEMA.items():
        # (Note: won't work right if ADDITIONAL_TABLES_SCHEMA has key in LOG_EVENT_TYPE_SCHEMA)
        if LOG_EVENT_TYPE_SCHEMA.has_key(event_type):
            field_names = LOG_ENTRY_COMMON_FIELDS + event_fields
        else:
            field_names = event_fields
        command = textwrap.dedent('''
            create table if not exists %s
                (%s,
                constraint pk primary key (%s) on conflict ignore)''') % (
            event_type,
            ', '.join(['%s text' % (name,) for name in field_names]),
            ', '.join(field_names))
        db.execute(command)


def pull_stats(db, error_file, host):

    print 'pull stats from host %s...' % (host.Host_ID,)

    server_ip_address_to_id = {}
    for server in psi_db.get_servers():
        server_ip_address_to_id[server.IP_Address] = server.Server_ID

    line_re = re.compile(LOG_LINE_PATTERN)

    ssh = psi_ssh.SSH(
            host.IP_Address, host.SSH_Port,
            host.SSH_Username, host.SSH_Password,
            host.SSH_Host_Key)

    # Download each log file from the host, parse each line and insert
    # log entries into database.

    dirlist = ssh.list_dir(HOST_LOG_DIR)
    for filename in dirlist:
        if re.match(HOST_LOG_FILENAME_PATTERN, filename):
            print 'processing %s...' % (filename,)
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            temp_file.close()
            try:
                file = None
                ssh.get_file(
                    posixpath.join(HOST_LOG_DIR, filename), temp_file.name)
                if filename.endswith('.gz'):
                    # Older log file archives are in gzip format
                    file = gzip.open(temp_file.name)
                else:
                    file = open(temp_file.name)
                    for line in file.read().split('\n'):
                        match = line_re.match(line)
                        if (not match or
                            not LOG_EVENT_TYPE_SCHEMA.has_key(match.group(3))):
                            err = 'unexpected log line pattern: %s' % (line,)
                            error_file.write(err + '\n')
                            continue
                        timestamp = match.group(1)
                        host_id = match.group(2)
                        event_type = match.group(3)
                        event_values = match.group(4).split()
                        event_fields = LOG_EVENT_TYPE_SCHEMA[event_type]
                        if len(event_values) != len(event_fields):
                            err = 'invalid log line fields %s' % (line,)
                            error_file.write(err + '\n')
                            continue
                        field_names = LOG_ENTRY_COMMON_FIELDS + event_fields
                        field_values = [timestamp, host_id] + event_values
                        # Replace server IP addresses with server IDs in
                        # stats to keep IP addresses confidental in reporting.
                        assert(len(field_names) == len(field_values))
                        for index, name in enumerate(field_names):
                            if name.find('server_id') != -1:
                                field_values[index] = server_ip_address_to_id[
                                                        field_values[index]]
                        # SQL injection note: the table name isn't parameterized
                        # and comes from log file data, but it's implicitly
                        # validated by hash table lookups
                        command = 'insert into %s (%s) values (%s)' % (
                            event_type,
                            ', '.join(field_names),
                            ', '.join(['?']*len(field_values)))
                        db.execute(command, field_values)
            finally:
                # Always delete temporary downloaded log file
                if file:
                    file.close()
                os.remove(temp_file.name)
    ssh.close()


def iso8601_to_utc(timestamp):
    localized_datetime = datetime.datetime.strptime(timestamp[:24], '%Y-%m-%dT%H:%M:%S.%f')
    timezone_delta = datetime.timedelta(
                                hours = int(timestamp[-6:-3]),
                                minutes = int(timestamp[-2:]))
    return (localized_datetime - timezone_delta).strftime('%Y-%m-%dT%H:%M:%S.%fZ')


def reconstruct_sessions(db):
    # Populate the session table. For each connection, create a session. Some
    # connections will have no end time, depending on when the logs are pulled.
    # Find the end time by selecting the 'disconnected' event with the same
    # host_id and session_id soonest after the connected timestamp.

    # Note: this order of operations -- deleting all the sessions -- is to avoid
    # duplicate session entries in the case where a previous pull created
    # sessions with no end.

    db.execute('delete from session')

    field_names = ADDITIONAL_TABLES_SCHEMA['session']
    cursor = db.cursor()
    cursor.execute('select * from connected')
    for row in cursor:

        # Check for a corresponding disconnected event
        # Timestamp is string field, but ISO 8601 format has the
        # lexicographical order we want.
        # The timestamp string also includes a timezone, and the
        # lexicographical compare still works because we are only
        # comparing records from the same host (ie. same timezone).
        disconnected_row = db.execute(textwrap.dedent('''
                    select timestamp from disconnected
                    where timestamp > ?
                    and host_id = ?
                    and relay_protocol = ?
                    and session_id = ?
                    order by timestamp asc limit 1'''),
                    [row[0], row[1], row[7], row[8]]).fetchone()
        session_end_timestamp = disconnected_row[0] if disconnected_row else None

        command = 'insert into session (%s) values (%s)' % (
            ', '.join(field_names),
            ', '.join(['?']*len(field_names)))
        # Note: dependent on column orders in schema definitions
        connected_field_names = LOG_ENTRY_COMMON_FIELDS + LOG_EVENT_TYPE_SCHEMA['connected']
        assert(connected_field_names[0] == 'timestamp' and
               connected_field_names[1] == 'host_id' and
               connected_field_names[8] == 'session_id')
        # Note: We convert timestamps here to UTC to ease matching of outbound statistics
        #       (and any other records that may not have consistent timezone info) to sessions.
        session_start_utc = iso8601_to_utc(row[0])
        session_end_utc = iso8601_to_utc(session_end_timestamp) if session_end_timestamp else None
        db.execute(command, list(row[1:])+[session_start_utc, session_end_utc])


class SessionIndex:

    def __init__(self, db, host_id):

        SessionInfo = collections.namedtuple(
            'SessionInfo',
            'host_id, server_id, client_region, propagation_channel_id, sponsor_id, '+
            'client_version, relay_protocol, session_id, '+
            'session_start_timestamp, session_end_timestamp')

        class SortedArrayIndex:
            def __init__(self):
                self.keys = []
                self.data = []

        self.session_end_index = collections.defaultdict(SortedArrayIndex)
        self.session_start_index = collections.defaultdict(SortedArrayIndex)

        for sort_field, output_index in [
            ('session_end_timestamp', self.session_end_index),
            ('session_start_timestamp', self.session_start_index)]:

            cursor = db.execute(
                textwrap.dedent(
                '''select
                   host_id, server_id, client_region, propagation_channel_id, sponsor_id,
                   client_version, relay_protocol, session_id,
                   substr(session_start_timestamp,1,19), substr(session_end_timestamp,1,19)
                   from session
                   where host_id = ? and relay_protocol == 'VPN'
                   order by substr(%s,1,19) asc''' % sort_field),
                [host_id])

            for row in cursor:
                session_info = SessionInfo(*row)
                sorted_array_index = output_index[session_info.session_id]
                sorted_array_index.keys.append(getattr(session_info,sort_field))
                sorted_array_index.data.append(session_info)

    def find_session_ending_on_or_after(self, session_id, flow_end_timestamp):

        # bisect usage from:
        # http://docs.python.org/library/bisect.html#searching-sorted-lists
        # http://docs.python.org/library/bisect.html#other-examples

        def find_ge(a, x):
            'Find leftmost item greater than or equal to x'
            array_index = bisect.bisect_left(a, x)
            if array_index != len(a):
                return array_index
            return None

        sessions = self.session_end_index.get(session_id)
        if not sessions:
            return None
        array_index = find_ge(sessions.keys, flow_end_timestamp)
        return sessions.data[array_index] if array_index else None

    def find_latest_started_session(self, session_id):
        sessions = self.session_start_index.get(session_id)
        if not sessions:
            return None
        return sessions.data[-1]


def process_vpn_outbound_stats(db, error_file, csv_file, host_id):

    print 'processing vpn outbound stats from host %s...' % (host_id,)

    # Create an in-memory index for fast lookup of session start/end used
    # to map flows to sessions (to get region, prop channel etc. attributes)
    session_index = SessionIndex(db, host_id)

    db.execute("delete from outbound where relay_protocol = 'VPN' and host_id = '%s'" % (host_id,))

    def to_iso8601(timestamp):
        return datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%dT%H:%M:%S')

    # CSV format
    #
    # HEADER:
    # ts,te,td,sa,da,
    # sp,dp,pr,flg,fwd,stos,ipkt,ibyt,opkt,obyt,in,out,
    # sas,das,smk,dmk,dtos,dir,nh,nhb,svln,dvln,ismc,odmc,idmc,osmc,
    # mpls1,mpls2,mpls3,mpls4,mpls5,mpls6,mpls7,mpls8,mpls9,mpls10,ra,eng
    #
    # SAMPLE ROW:
    # 2011-07-04 16:09:14,2011-07-04 16:09:14,0.351,10.1.0.2,208.69.58.58,
    # 4046,80,TCP,.AP.SF,0,0,6,686,0,0,117,100,
    # 0,0,0,0,0,0,0.0.0.0,0.0.0.0,0,0,00:00:00:00:00:00,00:00:00:00:00:00,00:00:00:00:00:00,00:00:00:00:00:00,
    # 0-0-0,0-0-0,0-0-0,0-0-0,0-0-0,0-0-0,0-0-0,0-0-0,0-0-0,0-0-0,0.0.0.0,0/0
    #
    # Note that there is no timezone info given in ts and te.  These timestamps
    # are reported in UTC.
    #
    # To compare netflow timestamps (which don't have millisecond resolution)
    # to session timestamps, we truncate the session timestamps milliseconds
    # and timezone info.
    # There is a small chance that multiple sessions will occur on the same
    # session_id (client vpn ip address) in the same second so that a flow
    # occuring in a single second will match both sessions.
    # TODO: investigate nf_dump -o extended millisecond resolution

    outbound_reader = csv.reader(csv_file)
    for row in outbound_reader:
        # Stop reading at the Summary row
        if 'Summary' in row:
            break

        # Skip blank rows
        if not len(row):
            continue

        # First find the earliest session that ends after the netflow end timestamp.
        session = session_index.find_session_ending_on_or_after(row[3], to_iso8601(row[1]))

        if not session:
            # If we couldn't find a session end timestamp on or after the netflow end timestamp,
            # then the netflow must belong to the latest (or currently active) session.
            session = session_index.find_latest_started_session(row[3])

        if not session:
            err = 'no session for outbound netflow on host %s: %s' % (host_id, str(row))
            error_file.write(err + '\n')
            # See CSV format above
            field_values = [host_id, '0', '0', '0', '0', '0', '0', row[], 
                            row[0][0:10], row[4], row[7], row[6], '1', row[14]]
        else:
            field_values = list(session)[0:-2] + [
                            row[0][0:10], row[4], row[7], row[6], '1', row[14]]

        field_names = ADDITIONAL_TABLES_SCHEMA['outbound']
        matching_record = db.execute(textwrap.dedent(
            '''
            select flow_count, outbound_byte_count from outbound
            where host_id = ?
            and server_id = ?
            and client_region = ?
            and propagation_channel_id = ?
            and sponsor_id = ?
            and client_version = ?
            and relay_protocol = ?
            and session_id = ?
            and day = ?
            and domain = ?
            and protocol = ?
            and port = ?
            '''), field_values[0:-2]).fetchone()

        if matching_record:
            field_values[-2] = str(int(matching_record[0][0]) + 1)
            field_values[-1] = str(int(matching_record[0][1]) + int(row[14]))

        command += 'insert or replace into outbound (%s) values (%s)' % (
            ', '.join(field_names),
            ', '.join(['?']*len(field_names)))
        db.execute(command, field_values)


if __name__ == "__main__":

    if not os.path.exists(STATS_ROOT):
        os.makedirs(STATS_ROOT)
    db = sqlite3.connect(STATS_DB_FILENAME)

    # Note: truncating error file
    error_file = open('pull_stats.err', 'w')

    try:
        init_stats_db(db)
        hosts = psi_db.get_hosts()

        # Pull stats from each host

        for host in hosts:
            pull_stats(db, error_file, host)

        # Compute sessions from connected/disconnected records

        reconstruct_sessions(db)

        # Pull netflows from each host and process them

        for host in hosts:
            csv_file_path = pull_netflows(host)
            with open(csv_file_path, 'rb') as vpn_outbound_stats_csv:
                process_vpn_outbound_stats(db, error_file, vpn_outbound_stats_csv, host.Host_ID)

    except:
        traceback.print_exc()
    finally:
        error_file.close()
        db.commit()
        db.close()
