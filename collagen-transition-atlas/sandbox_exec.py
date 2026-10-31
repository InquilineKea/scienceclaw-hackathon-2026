"""Original Linux worker wrapper: drop privileges and deny Internet sockets."""
import ctypes
import errno
import os
import platform
import socket
import sys

if platform.machine()!='x86_64':raise RuntimeError('Reviewed syscall filter is x86_64 only')
class Filter(ctypes.Structure):_fields_=[('code',ctypes.c_ushort),('jt',ctypes.c_ubyte),('jf',ctypes.c_ubyte),('k',ctypes.c_uint)]
class Program(ctypes.Structure):_fields_=[('length',ctypes.c_ushort),('filter',ctypes.POINTER(Filter))]
# Linux seccomp_data: syscall nr offset 0, architecture 4, first argument 16.
# Permit UNIX sockets (needed by numerical runtimes), deny IPv4 and IPv6 sockets.
rules=[(0x20,0,0,4),(0x15,1,0,0xc000003e),(0x06,0,0,0x80000000),
       (0x20,0,0,0),(0x54,0,0,0x3fffffff),(0x15,0,4,41),(0x20,0,0,16),
       (0x15,1,0,2),(0x15,0,1,10),(0x06,0,0,0x00050000|errno.EPERM),(0x06,0,0,0x7fff0000)]
filters=(Filter*len(rules))(*[Filter(*x) for x in rules]);program=Program(len(rules),filters)
libc=ctypes.CDLL(None,use_errno=True)
if os.getuid()==0:os.setgroups([]);os.setgid(65534);os.setuid(65534)
if libc.prctl(38,1,0,0,0)!=0:raise OSError(ctypes.get_errno(),'no_new_privileges failed')
if libc.prctl(22,2,ctypes.byref(program),0,0)!=0:raise OSError(ctypes.get_errno(),'network restriction failed')
for family in [socket.AF_INET,socket.AF_INET6]:
 try:
  opened=socket.socket(family);opened.close();raise RuntimeError('Internet sockets were not blocked')
 except PermissionError:pass
print('ISOLATION verified: unprivileged worker; IPv4/IPv6 sockets denied; minimal environment',flush=True)
os.execv(sys.executable,[sys.executable,'-I',*sys.argv[1:]])
