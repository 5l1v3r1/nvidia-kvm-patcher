# File: patcher.py
# Author: SK1080
# Date: 6/29/2016
# License: Do whatever the fuck you want with this source code, at your own risk

# Note: This Script is Fugly
# Note: This Script Requires Python 3, Because You should be using it Anyway
# Note: This Python Script is really a glorified Batch File
# Note: Only Tested on versions 361.91 and 368.39
# Note: Targeted at Windows 10 X64, Fix Tool Paths for Testsigning and /os: option in Inf2Cat to support other OS
# Note: The test signing Script is BS and probably won't work on your system.

import sys
import subprocess
import os

# TODO: Wildcard Search
PATCHES = {
    "41FF978804000085C0": "31C0909090909085C0",  # 361.91 - 368.39
    "41FF97B804000085C0": "31C0909090909085C0",  # 372.54
}


def testsign_failed():
    print('[!] Testsigning Failed, Please Test Sign Driver Manually or Load via disabling enforcement')
    sys.exit(0)


if len(sys.argv) != 2:
    print('Usage: patcher.py [/path/to/Display.Driver/Folder]')
    sys.exit(-1)

print('[+] Unpacking nvlddmkm.sys')

driver_path = sys.argv[1]

sys_szdd_path = driver_path + '/nvlddmkm.sy_'
sys_path = driver_path + '/nvlddmkm.sys'

if not os.path.isfile(sys_szdd_path):
    print('Failed to find nvlddmkm.sy_')
    sys.exit(-1)

subprocess.call(["expand", sys_szdd_path, sys_path])

if not os.path.isfile(sys_path):
    print('Failed to expand nvlddmkm.sy_')
    sys.exit(-1)

#os.rename(sys_szdd_path, sys_szdd_path + ".orig")

driver_data = open(sys_path, 'rb').read()

print('[+] Patching KVM CPUID Check and unintentionally killing Vendor ID Check [FU NVIDIA]')
for pattern, patch in PATCHES.items():
    pattern = bytes.fromhex(pattern)
    patch = bytes.fromhex(patch)
    driver_data = driver_data.replace(pattern, patch)

print('[+] Writing Patched Driver')
open(sys_path, 'wb').write(driver_data)

print ('[+] Modifying Installer Config to Use Extracted Driver')
installer_config_path = driver_path + '/DisplayDriver.nvi'
data = open(installer_config_path, 'rb').read()
data = data.replace(b'nvlddmkm.sy_', b'nvlddmkm.sys')
open(installer_config_path, 'wb').write(data)

print('[+] Attempting to Test Sign Driver')

print(' [+] Generating Security Catalog')
inf2cat = 'C:/Program Files (x86)/Windows Kits/10/bin/x86/Inf2Cat.exe'
if not os.path.isfile(inf2cat):
    print('[!] Failed to find Inf2Cat, Please Install Windows 10 WDK or Correct Path in Script')
    testsign_failed()

subprocess.call([inf2cat, '/driver:' + driver_path, '/os:10_X64'])

print(' [+] Generating and Installing TestSign Certificate')
subprocess.call(["C:\\WINDOWS\\system32\\WindowsPowerShell\\v1.0\\powershell.exe",
                      "-ExecutionPolicy", "Unrestricted",
                      ". ./gencert.ps1", "-directory", os.path.dirname(os.path.realpath(__file__))],
                     stdout=sys.stdout)


print(' [+] Signing Catalog File')
signtool = 'C:/Program Files (x86)/Windows Kits/10/Tools/bin/i386/signtool.exe'
if not os.path.isfile(signtool):
    print('[!] Failed to find signtool, Please Install Windows 10 WDK or Correct Path in Script')
    testsign_failed()

catalog_path = driver_path + './nv_disp.cat'
subprocess.call([signtool, 'sign', '/v', '/n', 'SKSoftware', '/t', 'http://timestamp.verisign.com/scripts/timstamp.dll', catalog_path])