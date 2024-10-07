// #include <stdio.h>
#include "sockets.c"

int main() {
    char data[] = "Hello, would you like to buy one million toothpicks for $2000?";
    ClientSocket s = Client(TEST_SOCKET);
    Client_send(s, data, sizeof(data));
    Client_close(s);
    return 0;
}
