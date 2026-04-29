import ctypes
from ctypes import wintypes
import sys

user32 = ctypes.WinDLL('user32', use_last_error=True)
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
psapi = ctypes.WinDLL('psapi', use_last_error=True)

EnumWindows = user32.EnumWindows
EnumWindows.restype = wintypes.BOOL
# WNDENUMPROC type: BOOL CALLBACK EnumWindowsProc(HWND hwnd, LPARAM lParam)
WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
EnumWindows.argtypes = [WNDENUMPROC, wintypes.LPARAM]
GetWindowTextW = user32.GetWindowTextW
GetWindowTextW.restype = ctypes.c_int
GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
GetClassNameW = user32.GetClassNameW
GetClassNameW.restype = ctypes.c_int
GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
IsWindowVisible = user32.IsWindowVisible
IsWindowVisible.restype = wintypes.BOOL
GetWindowRect = user32.GetWindowRect
GetWindowRect.restype = wintypes.BOOL
GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
GetWindowThreadProcessId = user32.GetWindowThreadProcessId
GetWindowThreadProcessId.restype = wintypes.DWORD
GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]

OpenProcess = kernel32.OpenProcess
OpenProcess.restype = wintypes.HANDLE
OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]

QueryFullProcessImageNameW = kernel32.QueryFullProcessImageNameW
QueryFullProcessImageNameW.restype = wintypes.BOOL
QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]

CloseHandle = kernel32.CloseHandle

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

results = []

def enum_proc(hwnd, lParam):
    buf = ctypes.create_unicode_buffer(512)
    GetWindowTextW(hwnd, buf, 512)
    title = buf.value
    cls = ctypes.create_unicode_buffer(256)
    GetClassNameW(hwnd, cls, 256)
    visible = bool(IsWindowVisible(hwnd))
    rect = wintypes.RECT()
    try:
        GetWindowRect(hwnd, ctypes.byref(rect))
    except Exception:
        rect = None
    pid = wintypes.DWORD()
    GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    pid_val = pid.value
    exe = ''
    if pid_val:
        hProc = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid_val)
        if hProc:
            size = wintypes.DWORD(1024)
            exe_buf = ctypes.create_unicode_buffer(1024)
            ok = QueryFullProcessImageNameW(hProc, 0, exe_buf, ctypes.byref(size))
            if ok:
                exe = exe_buf.value
            CloseHandle(hProc)
    results.append((hwnd, title, cls.value, visible, rect, pid_val, exe))
    return True

EnumWindows(WNDENUMPROC(enum_proc), 0)

for hwnd, title, cls, vis, rect, pid, exe in results:
    print('HWND:', hex(hwnd))
    print('  Title:', repr(title))
    print('  Class:', repr(cls))
    print('  Visible:', vis)
    if rect:
        print('  Rect:', (rect.left, rect.top, rect.right, rect.bottom))
    print('  PID:', pid)
    print('  EXE:', exe)
    print('')

# Also print any python.exe processes
try:
    import psutil
    print('Python processes:')
    for p in psutil.process_iter(['pid','name','exe','cmdline']):
        if p.info['name'] and 'python' in p.info['name'].lower():
            print(p.info)
except Exception:
    pass
