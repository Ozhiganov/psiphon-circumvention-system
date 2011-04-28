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

//==== includes ===============================================================

#include "stdafx.h"
#include "psiclient.h"
#include "vpnmanager.h"


//==== layout =================================================================

// TODO: Calculate instead of using magic constants

const int BUTTON_SIZE = 80;
const int BANNER_X = BUTTON_SIZE + 10;
const int BANNER_Y = 3;
const int BANNER_WIDTH = 200;
const int BANNER_HEIGHT = 80;
const int TOOLBAR_HEIGHT = BUTTON_SIZE + 16;
const int WINDOW_WIDTH = BUTTON_SIZE + BANNER_WIDTH + 30;
const int WINDOW_HEIGHT = 160;


//==== Win32 boilerplate ======================================================

#define MAX_LOADSTRING 100

// Global Variables
HINSTANCE hInst;
TCHAR szTitle[MAX_LOADSTRING];
TCHAR szWindowClass[MAX_LOADSTRING];

// Forward declarations of functions included in this code module:
ATOM                MyRegisterClass(HINSTANCE hInstance);
BOOL                InitInstance(HINSTANCE, int);
LRESULT CALLBACK    WndProc(HWND, UINT, WPARAM, LPARAM);
INT_PTR CALLBACK    About(HWND, UINT, WPARAM, LPARAM);

int APIENTRY _tWinMain(HINSTANCE hInstance,
                     HINSTANCE hPrevInstance,
                     LPTSTR    lpCmdLine,
                     int       nCmdShow)
{
    UNREFERENCED_PARAMETER(hPrevInstance);
    UNREFERENCED_PARAMETER(lpCmdLine);

     // TODO: Place code here.
    MSG msg;
    HACCEL hAccelTable;

    // Initialize global strings
    LoadString(hInstance, IDS_APP_TITLE, szTitle, MAX_LOADSTRING);
    LoadString(hInstance, IDC_PSICLIENT, szWindowClass, MAX_LOADSTRING);
    MyRegisterClass(hInstance);

    // Perform application initialization:
    if (!InitInstance (hInstance, nCmdShow))
    {
        return FALSE;
    }

    hAccelTable = LoadAccelerators(hInstance, MAKEINTRESOURCE(IDC_PSICLIENT));

    // Main message loop:
    while (GetMessage(&msg, NULL, 0, 0))
    {
        if (!TranslateAccelerator(msg.hwnd, hAccelTable, &msg))
        {
            TranslateMessage(&msg);
            DispatchMessage(&msg);
        }
    }

    return (int) msg.wParam;
}

ATOM MyRegisterClass(HINSTANCE hInstance)
{
    WNDCLASSEX wcex;

    wcex.cbSize = sizeof(WNDCLASSEX);

    wcex.style            = CS_HREDRAW | CS_VREDRAW;
    wcex.lpfnWndProc    = WndProc;
    wcex.cbClsExtra        = 0;
    wcex.cbWndExtra        = 0;
    wcex.hInstance        = hInstance;
    wcex.hIcon            = LoadIcon(hInstance, MAKEINTRESOURCE(IDI_PSICLIENT));
    wcex.hCursor        = LoadCursor(NULL, IDC_ARROW);
    wcex.hbrBackground    = (HBRUSH)(COLOR_WINDOW+1);
    //wcex.lpszMenuName    = MAKEINTRESOURCE(IDC_PSICLIENT);
    wcex.lpszMenuName    = 0;
    wcex.lpszClassName    = szWindowClass;
    wcex.hIconSm        = LoadIcon(wcex.hInstance, MAKEINTRESOURCE(IDI_SMALL));

    return RegisterClassEx(&wcex);
}

HWND g_hWnd;

BOOL InitInstance(HINSTANCE hInstance, int nCmdShow)
{
   HWND hWnd;
   RECT rect = {0, 0, WINDOW_WIDTH, WINDOW_HEIGHT};

   hInst = hInstance; // Store instance handle in our global variable

   SystemParametersInfo(SPI_GETWORKAREA, 0, &rect, 0);

   hWnd = CreateWindowEx(
            //WS_EX_TOPMOST|WS_EX_TOOLWINDOW,
            WS_EX_TOPMOST|WS_EX_TOOLWINDOW,
            szWindowClass,
            szTitle,
            //WS_OVERLAPPEDWINDOW & ~WS_SYSMENU,
            WS_OVERLAPPEDWINDOW,
            // CW_USEDEFAULT, 0, CW_USEDEFAULT, 0,
            rect.right - WINDOW_WIDTH, rect.bottom - WINDOW_HEIGHT, WINDOW_WIDTH, WINDOW_HEIGHT,
            NULL, NULL, hInstance, NULL);

   if (!hWnd)
   {
      return FALSE;
   }

   g_hWnd = hWnd;

   ShowWindow(hWnd, nCmdShow);
   UpdateWindow(hWnd);

   return TRUE;
}


//==== The VPN Manager ========================================================

VPNManager g_vpnManager;


//==== toolbar ================================================================

// http://msdn.microsoft.com/en-us/library/bb760446%28v=VS.85%29.aspx


HWND g_hToolBar = NULL;
HIMAGELIST g_hToolbarImageList = NULL;

void CreateToolbar(HWND hWndParent)
{
    // Define some constants.
    const int ImageListID = 0;
    const int numButtons = 1;
    const DWORD buttonStyles = BTNS_AUTOSIZE;
    const int bitmapSize = BUTTON_SIZE;

    // Create the toolbar.
    g_hToolBar = CreateWindowEx(
                            0, TOOLBARCLASSNAME, NULL, 
                            WS_CHILD | TBSTYLE_WRAPABLE,
                            0, 0, 0, 0,
                            hWndParent, NULL, hInst, NULL);
    if (g_hToolBar == NULL)
    {
        return;
    }

    // Create image list from bitmap

    g_hToolbarImageList = ImageList_LoadImage(
        hInst, MAKEINTRESOURCE(IDB_TOOLBAR_ICONS),
        bitmapSize, numButtons, CLR_DEFAULT, // GetSysColor(COLOR_BTNFACE),
        IMAGE_BITMAP, LR_CREATEDIBSECTION);

    // TODO: transparency

    // Set the image list.
    SendMessage(
        g_hToolBar, TB_SETIMAGELIST, (WPARAM)ImageListID, 
        (LPARAM)g_hToolbarImageList);

    // Initialize button info.
    TBBUTTON tbButtons[numButtons] = 
    {
        { MAKELONG(0, ImageListID), IDM_TOGGLE, TBSTATE_ENABLED, 
          buttonStyles, {0}, 0, (INT_PTR)L"" }
    };

    // Add buttons.
    SendMessage(
        g_hToolBar, TB_BUTTONSTRUCTSIZE, 
        (WPARAM)sizeof(TBBUTTON), 0);
    SendMessage(
        g_hToolBar, TB_ADDBUTTONS, (WPARAM)numButtons, 
        (LPARAM)&tbButtons);

    // Add banner child control.
    HWND hWndBanner = CreateWindow(
                            L"Static", 0,
                            WS_CHILD | WS_VISIBLE | SS_CENTERIMAGE | SS_BITMAP,
                            BANNER_X, BANNER_Y, BANNER_WIDTH, BANNER_HEIGHT,
                            g_hToolBar, NULL, hInst, NULL);
    HBITMAP hBanner = LoadBitmap(hInst, MAKEINTRESOURCE(IDB_BANNER));
    SendMessage(hWndBanner, STM_SETIMAGE, (WPARAM)IMAGE_BITMAP, (LPARAM)hBanner);

    // Tell the toolbar to resize itself, and show it.
    SendMessage(g_hToolBar, TB_AUTOSIZE, 0, 0); 
    ShowWindow(g_hToolBar, TRUE);
}

void UpdateButton(void)
{
    TBBUTTONINFO info;
    info.cbSize = sizeof(info);
    info.dwMask = TBIF_IMAGE;
    static int g_nextAnimationIndex = 0;

    VPNState state = g_vpnManager.GetVPNState();
    if (state == VPN_STATE_STOPPED) info.iImage = 0;
    else if (state == VPN_STATE_CONNECTED) info.iImage = 1;
    else info.iImage = 2 + (g_nextAnimationIndex++)%4;
    
    SendMessage(g_hToolBar, TB_SETBUTTONINFO, IDM_TOGGLE, (LPARAM)&info);
}


//==== my_print (logging) =====================================================

HWND g_hListBox = NULL;
bool g_bShowDebugMessages = false;

void my_print(bool bDebugMessage, const TCHAR* format, ...)
{
    if (!bDebugMessage || g_bShowDebugMessages)
    {
        TCHAR* debugPrefix = _T("DEBUG: ");
        size_t debugPrefixLength = _tcsclen(debugPrefix);
        TCHAR* buffer = NULL;
        va_list args;
        va_start(args, format);
        int length = _vsctprintf(format, args) + 1;
        if (bDebugMessage)
        {
            length += debugPrefixLength;
        }
        buffer = (TCHAR*)malloc(length * sizeof(TCHAR));
        if (!buffer) return;
        if (bDebugMessage)
        {
            _tcscpy_s(buffer, length, debugPrefix);
            _vstprintf_s(buffer + debugPrefixLength, length - debugPrefixLength, format, args);
        }
        else
        {
            _vstprintf_s(buffer, length, format, args);
        }
        va_end(args);
        SendMessage(g_hListBox, LB_ADDSTRING, NULL, (LPARAM)buffer);
        free(buffer);
        SendMessage(g_hListBox, LB_SETCURSEL,
        SendMessage(g_hListBox, LB_GETCOUNT, NULL, NULL)-1, NULL);
    }
}

void my_print(bool bDebugMessage, const string& message)
{
    tstring tMessage(message.length(), _T(' '));
    std::copy(message.begin(), message.end(), tMessage.begin());
    my_print(bDebugMessage, tMessage.c_str());
}


//==== Main window function ===================================================

static UINT_PTR g_hTimer;

LRESULT CALLBACK WndProc(HWND hWnd, UINT message, WPARAM wParam, LPARAM lParam)
{
    int wmId, wmEvent;
    PAINTSTRUCT ps;
    HDC hdc;
    RECT rect;
    HGDIOBJ font;

    switch (message)
    {
    case WM_CREATE:

        CreateToolbar(hWnd);

        g_hListBox = CreateWindow(_T("listbox"),
                                _T(""),
                                WS_CHILD|WS_VISIBLE|WS_VSCROLL|
                                LBS_NOINTEGRALHEIGHT|LBS_DISABLENOSCROLL|LBS_NOTIFY,
                                0, 0, 1, 1,
                                hWnd, NULL, NULL, NULL);
        font = GetStockObject(DEFAULT_GUI_FONT);
        SendMessage(g_hListBox, WM_SETFONT, (WPARAM)font, NULL);

        // TODO: kill the timer when connected, restart when re-connecting
        g_hTimer = SetTimer(hWnd, IDT_BUTTON_ROTATION, 250, NULL);

        g_vpnManager.Toggle();

        break;

    case WM_TIMER:
        UpdateButton();
        break;

    case WM_SIZE:
        // make list box fill window client area
        GetClientRect(hWnd, &rect);
        if (g_hToolBar != NULL)
        {
            MoveWindow(
                g_hToolBar,
                0, 0,
                rect.right-rect.left, TOOLBAR_HEIGHT,
                TRUE);
        }
        if (g_hListBox != NULL)
        {
            MoveWindow(
                g_hListBox,
                0, TOOLBAR_HEIGHT,
                rect.right-rect.left, rect.bottom-rect.top - TOOLBAR_HEIGHT,
                TRUE);
        }
        break;

    case WM_COMMAND:

        wmId    = LOWORD(wParam);
        wmEvent = HIWORD(wParam);

        // Parse the menu selections:
        switch (wmId)
        {
        case IDM_TOGGLE:
            g_vpnManager.Toggle();
            break;
        case IDM_SHOW_DEBUG_MESSAGES:
            g_bShowDebugMessages = !g_bShowDebugMessages;
            my_print(false, _T("Show debug messages: %s"), g_bShowDebugMessages ? _T("Yes") : _T("No"));
            break;
        // TODO: remove about and exit?  The menu is currently hidden
        case IDM_HELP:
            // TODO: help?
            break;
        case IDM_ABOUT:
            DialogBox(hInst, MAKEINTRESOURCE(IDD_ABOUTBOX), hWnd, About);
            break;
        case IDM_EXIT:
            DestroyWindow(hWnd);
            break;
        default:
            return DefWindowProc(hWnd, message, wParam, lParam);
        }
        break;

    case WM_PSIPHON_VPN_STATE_CHANGE:
        g_vpnManager.VPNStateChanged((VPNState)wParam);
        UpdateButton();
        if (VPN_STATE_STOPPED == g_vpnManager.GetVPNState())
        {
            // This is printed here to avoid printing in the vpnconnection's callback thread
            // in case it is called after my_print is already gone (when the app quits).
            my_print(false, _T("Disconnected."));
        }
        break;

    case WM_PAINT:
        hdc = BeginPaint(hWnd, &ps);
        // TODO: Add any drawing code here...
        EndPaint(hWnd, &ps);
        break;

    case WM_DESTROY:
        // Stop VPN if running
        g_vpnManager.Stop();
        PostQuitMessage(0);
        break;

    default:
        return DefWindowProc(hWnd, message, wParam, lParam);
    }
    return 0;
}

// Message handler for about box.
INT_PTR CALLBACK About(HWND hDlg, UINT message, WPARAM wParam, LPARAM lParam)
{
    UNREFERENCED_PARAMETER(lParam);
    switch (message)
    {
    case WM_INITDIALOG:
        return (INT_PTR)TRUE;

    case WM_COMMAND:
        if (LOWORD(wParam) == IDOK || LOWORD(wParam) == IDCANCEL)
        {
            EndDialog(hDlg, LOWORD(wParam));
            return (INT_PTR)TRUE;
        }
        break;
    }
    return (INT_PTR)FALSE;
}
