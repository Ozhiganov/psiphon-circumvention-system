/*
 * Copyright (c) 2012, Psiphon Inc.
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

package com.psiphon3;

import android.os.Build;

public interface PsiphonConstants
{
    public final static String TAG = "Psiphon";
    
    public final static String SERVER_ENTRY_FILENAME = "psiphon_server_entries.json";

    public final static int CLIENT_SESSION_ID_SIZE_IN_BYTES = 16;
    
    public final static int SOCKS_PORT = 1080;
    
    public final static String POLIPO_EXECUTABLE = "polipo";
    
    public final static int HTTP_PROXY_PORT = 8080;

    public final static String POLIPO_ARGUMENTS = "proxyPort=8080 diskCacheRoot=\"\" disableLocalInterface=true socksParentProxy=127.0.0.1:1080 logLevel=1";

    public final int SESSION_ESTABLISHMENT_TIMEOUT_MILLISECONDS = 20000;
    
    public final static String RELAY_PROTOCOL = "OSSH";
    
    public final static String PLATFORM = "Android_" + Build.VERSION.RELEASE.replaceAll(" ", "-");
    
    public final static int HTTPS_REQUEST_TIMEOUT = 20000;
}
