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
import urllib2
import subprocess
import time
import random
import copy
from functools import wraps
try:
    import win32ui
    import win32con
    import _winreg
    REGISTRY_ROOT_KEY = _winreg.HKEY_CURRENT_USER
except ImportError as error:
    print error
    print 'NOTE: Running client tests will not be available.'

import psi_ops_build_windows


# Check usage restrictions here before using this service:
# http://www.whatismyip.com/faq/automation.asp

# Local service should be in same GeoIP region; local split tunnel will be in effect (not proxied)
# Remote service should be in different GeoIP region; remote split tunnel will be in effect (proxied)
CHECK_IP_ADDRESS_URL_LOCAL = 'http://automation.whatismyip.com/n09230945.asp'
CHECK_IP_ADDRESS_URL_REMOTE = 'http://automation.whatismyip.com/n09230945.asp'

# if psi_build_config.py exists, load it and use psi_build_config.DATA_ROOT as the data root dir

if os.path.isfile('psi_data_config.py'):
    import psi_data_config
    CHECK_IP_ADDRESS_URL_LOCAL = psi_data_config.CHECK_IP_ADDRESS_URL_LOCAL
    CHECK_IP_ADDRESS_URL_REMOTE = psi_data_config.CHECK_IP_ADDRESS_URL_REMOTE


REGISTRY_PRODUCT_KEY = 'SOFTWARE\\Psiphon3'
REGISTRY_TRANSPORT_VALUE = 'Transport'
REGISTRY_SPLIT_TUNNEL_VALUE = 'SplitTunnel'


def retry_on_exception_decorator(function):
    @wraps(function)
    def wrapper(*args, **kwds):
        for i in range(4):
            try:
                if i > 0:
                    time.sleep(20)
                return function(*args, **kwds)
            except Exception as e:
                print str(e)
                pass
        raise e
    return wrapper


@retry_on_exception_decorator
def __test_web_server(ip_address, web_server_port, propagation_channel_id, web_server_secret):
    print 'Testing web server at %s...' % (ip_address,)
    get_request = 'https://%s:%s/handshake?propagation_channel_id=%s&sponsor_id=0&client_version=1&server_secret=%s&relay_protocol=SSH' % (
                    ip_address, web_server_port, propagation_channel_id, web_server_secret)
    # Reset the proxy settings (see comment below)
    urllib2.install_opener(urllib2.build_opener(urllib2.ProxyHandler()))
    response = urllib2.urlopen(get_request, timeout=10).read()
    return ('SSHPort: ' in response and
            'SSHUsername: ' in response and
            'SSHPassword: ' in response and
            'SSHHostKey: ' in response and
            'SSHObfuscatedPort: ' in response and
            'SSHObfuscatedKey: ' in response and
            'PSK: ' not in response)


@retry_on_exception_decorator
def __test_server(executable_path, transport, expected_egress_ip_addresses):
    # test:
    # - spawn client process, which starts the VPN
    # - sleep 5 seconds, which allows time to establish connection
    # - determine egress IP address and assert it matches host IP address
    # - post WM_CLOSE to gracefully shut down the client and its connection

    has_remote_check = len(CHECK_IP_ADDRESS_URL_REMOTE) > 0
    has_local_check = len(CHECK_IP_ADDRESS_URL_LOCAL) > 0

    # Internally we refer to "OSSH", but the display name is "SSH+", which is also used
    # in the registry setting to control which transport is used.
    if transport == 'OSSH':
        transport = 'SSH+'
        
    # Split tunnelling is not implemented for VPN.
    # Also, if there is no remote check, don't use split tunnel mode because we always want
    # to test at least one proxied case.
    if transport == 'VPN' or not has_remote_check:
        split_tunnel_mode = False
    else:
        split_tunnel_mode = random.choice([True, False])

    print 'Testing egress IP addresses %s in %s mode (split tunnel %s)...' % (
            ','.join(expected_egress_ip_addresses), transport, 'ENABLED' if split_tunnel_mode else 'DISABLED')

    try:
        proc = None
        transport_value, transport_type = None, None
        split_tunnel_value, split_tunnel_type = None, None
        reg_key = _winreg.OpenKey(REGISTRY_ROOT_KEY, REGISTRY_PRODUCT_KEY, 0, _winreg.KEY_ALL_ACCESS)
        transport_value, transport_type = _winreg.QueryValueEx(reg_key, REGISTRY_TRANSPORT_VALUE)
        _winreg.SetValueEx(reg_key, REGISTRY_TRANSPORT_VALUE, None, _winreg.REG_SZ, transport)
        split_tunnel_value, split_tunnel_type = _winreg.QueryValueEx(reg_key, REGISTRY_SPLIT_TUNNEL_VALUE)
        # Enable split tunnel with registry setting
        _winreg.SetValueEx(reg_key, REGISTRY_SPLIT_TUNNEL_VALUE, None, _winreg.REG_DWORD, 1 if split_tunnel_mode else 0)
        
        proc = subprocess.Popen([executable_path])
        
        time.sleep(15)
    
        # In VPN mode, all traffic is routed through the proxy. In SSH mode, the
        # urlib2 ProxyHandler picks up the Windows Internet Settings and uses the
        # HTTP Proxy that is set by the client.
        urllib2.install_opener(urllib2.build_opener(urllib2.ProxyHandler()))

        if has_local_check:
            # Get egress IP from web site in same GeoIP region; local split tunnel is not proxied
    
            egress_ip_address = urllib2.urlopen(CHECK_IP_ADDRESS_URL_LOCAL, timeout=30).read().split('\n')[0]

            is_proxied = (egress_ip_address in expected_egress_ip_addresses)
    
            if (transport == 'VPN' or not split_tunnel_mode) and not is_proxied:
                raise Exception('Local case/VPN/not split tunnel: egress is %s and expected egresses are %s' % (
                                    egress_ip_address, ','.join(expected_egress_ip_addresses)))

            if transport != 'VPN' and split_tunnel_mode and is_proxied:
                raise Exception('Local case/not VPN/split tunnel: egress is %s and expected egresses are ANYTHING OTHER THAN %s' % (
                                    egress_ip_address, ','.join(expected_egress_ip_addresses)))
    
        if has_remote_check:
            # Get egress IP from web site in different GeoIP region; remote split tunnel is proxied

            egress_ip_address = urllib2.urlopen(CHECK_IP_ADDRESS_URL_REMOTE, timeout=30).read().split('\n')[0]
    
            is_proxied = (egress_ip_address in expected_egress_ip_addresses)

            if not is_proxied:
                raise Exception('Remote case: egress is %s and expected egresses are %s' % (
                                    egress_ip_address, ','.join(expected_egress_ip_addresses)))
        
    finally:
        if transport_type and transport_value:
            _winreg.SetValueEx(reg_key, REGISTRY_TRANSPORT_VALUE, None, transport_type, transport_value)
        if split_tunnel_value and split_tunnel_type:
            _winreg.SetValueEx(reg_key, REGISTRY_SPLIT_TUNNEL_VALUE, None, split_tunnel_type, split_tunnel_value)
        try:
            win32ui.FindWindow(None, psi_ops_build_windows.APPLICATION_TITLE).PostMessage(win32con.WM_CLOSE)
        except Exception as e:
            print e
        if proc:
            proc.wait()
            

def test_server(ip_address, capabilities, web_server_port, web_server_secret, encoded_server_list, version,
                expected_egress_ip_addresses, test_propagation_channel_id = '0', test_cases = None):

    local_test_cases = copy.copy(test_cases) if test_cases else ['handshake', 'VPN', 'OSSH', 'SSH']

    for test_case in copy.copy(local_test_cases):
        if not capabilities[test_case]:
            print 'Server does not support %s' % (test_case,)
            local_test_cases.remove(test_case)

    results = {}

    executable_path = None

    for test_case in local_test_cases:

        print 'test case %s...' % (test_case,)

        if test_case == 'handshake':
            try:
                result = __test_web_server(ip_address, web_server_port, test_propagation_channel_id, web_server_secret)
                results['WEB'] = 'PASS' if result else 'FAIL'
            except Exception as ex:
                results['WEB'] = 'FAIL: ' + str(ex)
            try:
                result = __test_web_server(ip_address, '443', test_propagation_channel_id, web_server_secret)
                results['443'] = 'PASS' if result else 'FAIL'
            except Exception as ex:
                results['443'] = 'FAIL: ' + str(ex)
        elif test_case in ['VPN', 'OSSH', 'SSH']:
            if not executable_path:
                executable_path = psi_ops_build_windows.build_client(
                                    test_propagation_channel_id,
                                    '0',        # sponsor_id
                                    None,       # banner
                                    encoded_server_list,
                                    '',         # remote_server_list_signature_public_key
                                    ('','',''), # remote_server_list_url
                                    '',   # info_link_url
                                    version,
                                    True)
            try:
                __test_server(executable_path, test_case, expected_egress_ip_addresses)
                results[test_case] = 'PASS'
            except Exception as ex:
                results[test_case] = 'FAIL: ' + str(ex)
    
    return results
