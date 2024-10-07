#!/usr/bin/python3
from sockets import SocketEnum, Host

s = Host(SocketEnum.TEST_SOCKET)
data = s.get(4095)
print(str(data))