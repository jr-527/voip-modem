#include <stdio.h>
#include "sockets.c"

int main() {
    HostSocket s = Host(TEST_SOCKET);
    char buf[4096];
    int n = Host_get(s, buf, 4095);
    buf[n] = '\0';
    printf("Received %d bytes: '%s'\n", n, buf);
    Host_close(s);
    return 0;
}