"""Original Linux socket-denial filter, applied after MPI initialization."""
import ctypes,errno,platform,socket

def deny_network():
 if platform.machine()!='x86_64':raise RuntimeError('Unsupported isolation architecture')
 class F(ctypes.Structure):_fields_=[('code',ctypes.c_ushort),('jt',ctypes.c_ubyte),('jf',ctypes.c_ubyte),('k',ctypes.c_uint)]
 class P(ctypes.Structure):_fields_=[('len',ctypes.c_ushort),('filter',ctypes.POINTER(F))]
 ins=[(0x20,0,0,4),(0x15,1,0,0xc000003e),(0x06,0,0,0x80000000),(0x20,0,0,0)]
 for n in [41,42,43,44,45,49,50,288,299,307]:ins.extend([(0x15,0,1,n),(0x06,0,0,0x50000|errno.EPERM)])
 ins.append((0x06,0,0,0x7fff0000));arr=(F*len(ins))(*(F(*r) for r in ins));p=P(len(ins),arr);lib=ctypes.CDLL(None,use_errno=True)
 if lib.prctl(38,1,0,0,0)!=0 or lib.prctl(22,2,ctypes.byref(p),0,0)!=0:raise RuntimeError('Isolation failed')
 try:socket.socket(socket.AF_INET,socket.SOCK_STREAM)
 except OSError as e:
  if e.errno!=errno.EPERM:raise
 else:raise RuntimeError('IP socket unexpectedly available')
