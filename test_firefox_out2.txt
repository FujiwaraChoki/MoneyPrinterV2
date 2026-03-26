import subprocess
import os

def get_firefox_binary():
    try:
        cmd = ['powershell.exe', '-Command', "(Get-ItemProperty 'HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\firefox.exe' -ErrorAction SilentlyContinue).'(default)'"]
        out = subprocess.check_output(cmd).decode('utf-8').strip()
        if out and os.path.exists(out):
            return out
    except:
        pass
    
    try:
        cmd = ['powershell.exe', '-Command', "(Get-ItemProperty 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\firefox.exe' -ErrorAction SilentlyContinue).'(default)'"]
        out = subprocess.check_output(cmd).decode('utf-8').strip()
        if out and os.path.exists(out):
            return out
    except:
        pass
    return None

print(f"FOUND: {get_firefox_binary()}")
