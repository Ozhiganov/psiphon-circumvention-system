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
#include "transport.h"
#include "sessioninfo.h"


/******************************************************************************
 ITransport
******************************************************************************/

ITransport::ITransport()
    : m_systemProxySettings(NULL)
{
}

void ITransport::Connect(
                    SessionInfo sessionInfo, 
                    SystemProxySettings* systemProxySettings,
                    const bool& stopSignalFlag)
{
    m_sessionInfo = sessionInfo;
    m_systemProxySettings = systemProxySettings;
    assert(m_systemProxySettings);

    if (!IWorkerThread::Start(stopSignalFlag))
    {
        throw TransportFailed();
    }
}

bool ITransport::DoStart()
{
    try
    {
        TransportConnect(m_sessionInfo, m_systemProxySettings);
    }
    catch(...)
    {
        return false;
    }

    return true;
}

void ITransport::DoStop()
{
    Cleanup();
    m_systemProxySettings = 0;
}
