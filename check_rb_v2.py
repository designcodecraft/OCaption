import os
import ctypes
from ctypes import wintypes

# This is a bit complex in pure Python without pywin32, 
# but I can use PowerShell from within Python and capture output more easily.
import subprocess

def get_rb_items():
    ps_cmd = """
    $rb = (New-Object -ComObject Shell.Application).Namespace(10);
    foreach ($item in $rb.Items()) {
        $o = $item.Parent.GetDetailsOf($item, 1);
        if ($o -like '*codebase*') {
            Write-Output "PATH:$($item.Path)|ORIG:$o"
        }
    }
    """
    proc = subprocess.Popen(["powershell", "-Command", ps_cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, err = proc.communicate()
    return out.strip().split('\n')

items = get_rb_items()
for item in items:
    if not item: continue
    print(item)
