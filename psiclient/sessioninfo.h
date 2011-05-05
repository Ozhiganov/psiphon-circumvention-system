/*
 * Copyright (c) 2011, Psiphon Inc.
 * All rights reserved.
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 */

#pragma once

#include <vector>
#include "vpnlist.h"
#include "tstring.h"

class VPNManager;

class SessionInfo
{
public:
    void Set(const ServerEntry& serverEntry);

    string GetServerAddress(void) {return m_serverEntry.serverAddress;}
    int GetWebPort(void) {return m_serverEntry.webServerPort;}
    string GetWebServerSecret(void) {return m_serverEntry.webServerSecret;}
    string GetUpgradeVersion(void) {return m_upgradeVersion;}
    string GetPSK(void) {return m_psk;}
    vector<string> GetHomepages(void) {return m_homepages;}
    vector<string> GetDiscoveredServerEntries(void) {return m_servers;}

    bool ParseHandshakeResponse(const string& response);

private:
    ServerEntry m_serverEntry;

    string m_upgradeVersion;
    string m_psk;
    vector<string> m_homepages;
    vector<string> m_servers;
};
