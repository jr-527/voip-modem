from sockets import SocketEnum, Client
data = "Hello, would you like to buy one million toothpicks for $2000?"

s = Client(SocketEnum.TEST_SOCKET)
s.send(bytes(data, 'utf-8'))