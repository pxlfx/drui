import os
import sys


def pid_exists(pid: int) -> bool:
    """
    Checks whether the process is alive.
    
    :param pid: process ID
    :return: True if the process exists, else False.
    """
    if sys.platform == 'win32':
        import ctypes
        kernel32 = ctypes.windll.kernel32

        handle = kernel32.OpenProcess(0x1000, False, pid)
        if not handle:
            handle = kernel32.OpenProcess(0x0400, False, pid)

        if handle:
            kernel32.CloseHandle(handle)
            return True
        else:
            last_error = kernel32.GetLastError()
            return last_error != 87
    else:
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        else:
            return True
        