import socket
from socketserver import UnixStreamServer, StreamRequestHandler, ThreadingMixIn
import os, os.path
import sys

class SocketEnum:
    PRO_ENC_SOCK = "/tmp/james_voip_modem_pe.socket"
    ENC_MOD_SOCK = "/tmp/james_voip_modem_em.socket"
    MOD_AUD_SOCK = "/tmp/james_voip_modem_ma.socket"
    AUD_DEM_SOCK = "/tmp/james_voip_modem_ad.socket"
    DEM_DEC_SOCK = "/tmp/james_voip_modem_dd.socket"
    DEC_PRO_SOCK = "/tmp/james_voip_modem_dp.socket"
    TEST_SOCKET = "/tmp/james_void_modem_test.socket"

def _socket_is_valid(socket_type: str) -> bool:
    for item in dir(SocketEnum):
        if getattr(SocketEnum, item) == getattr(SocketEnum, item):
            return True
    return False

class Host:
    def __init__(self, socket_type: str):
        """Initialize the host. Blocks until a client connects."""
        if not _socket_is_valid(socket_type):
            raise ValueError("%s is not a legal socket" % socket_type)
        self._socket_name = socket_type
        if os.path.exists(socket_type):
            os.remove(socket_type)
        server = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
        server.bind(socket_type)
        server.listen(20)
        self._conn, _ = server.accept()
        print("Connected to socket %s as host" % socket_type, file=sys.stderr)
    
    def __del__(self):
        print("Closing socket %s as host" % self._socket_name, file=sys.stderr)
        try:
            self._conn.close()
        except:
            pass
        os.remove(self._socket_name)
    
    def __repr__(self):
        return "Host(%s)"%self._socket_name
    
    def get(self, max_bytes: int) -> bytes:
        """Get up to max_bytes of data from the socket"""
        return self._conn.recv(max_bytes)


class Client:
    def __init__(self, socket_type: str):
        if not _socket_is_valid(socket_type):
            raise ValueError("%s is not a legal socket" % socket_type)
        self._socket_name = socket_type
        self._client = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
        self._client.connect(socket_type)
        print("Connected to socket %s as client" % socket_type, file=sys.stderr)


    def __del__(self):
        print("Closing socket %s as client" % self._socket_name, file=sys.stderr)
        self._client.close()
    
    def __repr__(self):
        return "Client(%s)"%self._socket_name
    
    def send(self, data: bytes):
        self._client.send(data)