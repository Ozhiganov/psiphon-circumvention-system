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

#include <tchar.h>

static const TCHAR* PLONK_EXE_NAME = _T("psiphon3-plonk.exe");
static const TCHAR* POLIPO_EXE_NAME = _T("psiphon3-polipo.exe");
static const TCHAR* PLONK_SOCKS_PROXY_PORT = _T("1080");
static const TCHAR* POLIPO_HTTP_PROXY_PORT = _T("8080");
static const TCHAR* VPN_CONNECTION_NAME = _T("Psiphon3");
static const TCHAR* LOCAL_SETTINGS_REGISTRY_KEY = _T("Software\\Psiphon3");
static const TCHAR* SPLIT_TUNNELING_FILE_NAME = _T("psiphon.route");
static const char* LOCAL_SETTINGS_REGISTRY_VALUE_SERVERS = "Servers";
static const char* LOCAL_SETTINGS_REGISTRY_VALUE_SKIP_VPN = "SkipVPN";
static const char* LOCAL_SETTINGS_REGISTRY_VALUE_USER_SKIP_VPN = "UserSkipVPN";
static const char* LOCAL_SETTINGS_REGISTRY_VALUE_USER_SKIP_BROWSER = "UserSkipBrowser";
static const char* LOCAL_SETTINGS_REGISTRY_VALUE_USER_SKIP_PROXY_SETTINGS = "UserSkipProxySettings";
static const TCHAR* HTTP_HANDSHAKE_REQUEST_PATH = _T("/handshake");
static const TCHAR* HTTP_CONNECTED_REQUEST_PATH = _T("/connected");
static const TCHAR* HTTP_STATUS_REQUEST_PATH = _T("/status");
static const TCHAR* HTTP_SPEED_REQUEST_PATH = _T("/speed");
static const TCHAR* HTTP_FAILED_REQUEST_PATH = _T("/failed");
static const TCHAR* HTTP_DOWNLOAD_REQUEST_PATH = _T("/download");

static int VPN_CONNECTION_TIMEOUT_SECONDS = 20;
static int SSH_CONNECTION_TIMEOUT_SECONDS = 20;
