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

#include "resource.h"
#include <Winhttp.h>


//==== global constants ================================================

#define WM_PSIPHON_VPN_STATE_CHANGE    WM_USER + 100


//==== logging =========================================================

void my_print(bool bDebugMessage, const TCHAR* format, ...);
void my_print(bool bDebugMessage, const string& message);


//==== global helpers ==================================================

class AutoHANDLE
{
public:
    AutoHANDLE(HANDLE handle) {m_handle = handle;}
    ~AutoHANDLE() {CloseHandle(m_handle);}
    operator HANDLE() {return m_handle;}
private:
    HANDLE m_handle;
};

class AutoHINTERNET
{
public:
    AutoHINTERNET(HINTERNET handle) {m_handle = handle;}
    ~AutoHINTERNET() {WinHttpCloseHandle(m_handle);}
    operator HINTERNET() {return m_handle;}
private:
    HINTERNET m_handle;
};

class AutoMUTEX
{
public:
    AutoMUTEX(HANDLE mutex) {m_mutex = mutex; WaitForSingleObject(m_mutex, INFINITE);}
    ~AutoMUTEX() {ReleaseMutex(m_mutex);}
private:
    HANDLE m_mutex;
};

