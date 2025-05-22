import sys


def isWin11():
    """Check if the system is Windows 11

    Returns:
        bool: True if the system is Windows 11, False otherwise
    """
    return sys.platform == "win32" and sys.getwindowsversion().build >= 22000
