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

#include "stdafx.h"
#include "httpsrequest.h"
#include "psiclient.h"
#include <Winhttp.h>
#include <WinCrypt.h>

HTTPSRequest::HTTPSRequest(void)
{
}

HTTPSRequest::~HTTPSRequest(void)
{
}

bool HTTPSRequest::GetRequest(
        bool& cancel,
        const TCHAR* serverAddress,
        int serverWebPort,
        const TCHAR* requestPath,
        string& response)
{
    // TODO:
    // Use asynchronous mode for cleaner and more effectively cancel functionality:
    // http://msdn.microsoft.com/en-us/magazine/cc716528.aspx
    // http://msdn.microsoft.com/en-us/library/aa383138%28v=vs.85%29.aspx
    // http://msdn.microsoft.com/en-us/library/aa384115%28v=VS.85%29.aspx

    BOOL bRet = FALSE;
    CERT_CONTEXT *pCert = {0};
    HCERTSTORE hCertStore = NULL;
    DWORD dwRet = 0;
    DWORD dwLen = 0;
    DWORD dwStatusCode;
    DWORD dwFlags = SECURITY_FLAG_IGNORE_CERT_CN_INVALID |
				    SECURITY_FLAG_IGNORE_CERT_DATE_INVALID |
				    SECURITY_FLAG_IGNORE_UNKNOWN_CA;
    LPVOID pBuffer = NULL;

    AutoHINTERNET hSession =
                WinHttpOpen(
                    _T("Mozilla/4.0 (compatible; MSIE 5.22)"),
	                WINHTTP_ACCESS_TYPE_DEFAULT_PROXY,
	                WINHTTP_NO_PROXY_NAME,
	                WINHTTP_NO_PROXY_BYPASS,
                    0 );

    if (NULL == hSession)
    {
	    my_print(false, _T("WinHttpOpen failed (%d)"), GetLastError());
        return false;
    }

    if (cancel)
    {
        return false;
    }

    AutoHINTERNET hConnect =
            WinHttpConnect(
                hSession,
	            serverAddress,
	            serverWebPort,
	            0);

    if (NULL == hConnect)
    {
	    my_print(false, _T("WinHttpConnect failed (%d)"), GetLastError());
        return false;
    }

    if (cancel)
    {
        return false;
    }

    AutoHINTERNET hRequest =
            WinHttpOpenRequest(
                    hConnect,
	                _T("GET"),
	                requestPath,
	                NULL,
	                WINHTTP_NO_REFERER,
	                WINHTTP_DEFAULT_ACCEPT_TYPES,
	                WINHTTP_FLAG_SECURE); 

    if (NULL == hRequest)
    {
	    my_print(false, _T("WinHttpOpenRequest failed (%d)"), GetLastError());
        return false;
    }

    if (cancel)
    {
        return false;
    }

    bRet = WinHttpSetOption(
	            hRequest,
	            WINHTTP_OPTION_SECURITY_FLAGS,
	            &dwFlags,
	            sizeof(DWORD));

    if (FALSE == bRet)
    {
	    my_print(false, _T("WinHttpSetOption failed (%d)"), GetLastError());
        return false;
    }

    if (cancel)
    {
        return false;
    }

    bRet = WinHttpSendRequest(
                hRequest,
	            WINHTTP_NO_ADDITIONAL_HEADERS,
	            0,
	            WINHTTP_NO_REQUEST_DATA,
	            0,
	            0,
	            0);

    if (FALSE == bRet)
    {
	    my_print(false, _T("WinHttpSendRequest failed (%d)"), GetLastError());
        return false;
    }

    if (cancel)
    {
        return false;
    }

    bRet = WinHttpReceiveResponse(hRequest, NULL);

    if (FALSE == bRet)
    {
	    my_print(false, _T("WinHttpReceiveResponse failed (%d)"), GetLastError());
        return false;
    }

    if (cancel)
    {
        return false;
    }

    dwLen = sizeof(dwStatusCode);

    bRet = WinHttpQueryHeaders(
                    hRequest, 
                    WINHTTP_QUERY_STATUS_CODE | WINHTTP_QUERY_FLAG_NUMBER,
                    NULL, 
                    &dwStatusCode, 
                    &dwLen, 
                    NULL);

    if (FALSE == bRet)
    {
	    my_print(false, _T("WinHttpQueryHeaders failed (%d)"), GetLastError());
        return false;
    }

    if (200 != dwStatusCode)
    {
	    my_print(false, _T("Bad HTTP GET request status code: %d"), dwStatusCode);
        return false;
    }

    if (cancel)
    {
        return false;
    }

    bRet = WinHttpQueryDataAvailable(hRequest, &dwLen);

    if (FALSE == bRet)
    {
	    my_print(false, _T("WinHttpQueryDataAvailable failed (%d)"), GetLastError());
        return false;
    }

    if (cancel)
    {
        return false;
    }

    pBuffer = HeapAlloc(GetProcessHeap(), HEAP_ZERO_MEMORY, dwLen);

    if (!pBuffer)
    {
        my_print(false, _T("HeapAlloc failed"));
        return false;
    }
    
    bRet = WinHttpReadData(hRequest, pBuffer, dwLen, &dwLen);

    if (FALSE == bRet)
    {
	    my_print(false, _T("WinHttpReadData failed (%d)"), GetLastError());
        HeapFree(GetProcessHeap(), 0, pBuffer);
        return false;
    }

    // NOTE: response data may be binary; some relevant comments here...
    // http://stackoverflow.com/questions/441203/proper-way-to-store-binary-data-with-c-stl

    response = string(string::const_pointer(pBuffer), string::const_pointer((char*)pBuffer + dwLen + 1));

    // TODO: remove this or set DEBUG to true
    my_print(false, _T("got: %s"), NarrowToTString(response).c_str());

    HeapFree(GetProcessHeap(), 0, pBuffer);

    dwLen = sizeof(pCert);

    if (cancel)
    {
        return false;
    }

    bRet = WinHttpQueryOption(
	            hRequest,
	            WINHTTP_OPTION_SERVER_CERT_CONTEXT,
	            &pCert,
	            &dwLen);

    if (NULL == pCert)
    {
	    my_print(false, _T("WinHttpQueryOption failed (%d)"), GetLastError());
        return false;
    }

    if (cancel)
    {
        return false;
    }

    my_print(false, _T("cert encoding %d %d"), pCert->dwCertEncodingType, pCert->cbCertEncoded);

    return true;
}
