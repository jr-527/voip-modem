#include <stdio.h>
#include <stdint.h>
#ifdef _WIN32
#include <io.h>
#include <fcntl.h>
#endif

int8_t buf[2048];
int main() {
    #ifdef _WIN32
    _setmode(_fileno(stdin), _O_BINARY);
    #endif
    int num_read = 0;
    while (num_read < 2048) {
        int this_read = fread(buf+num_read, 1, 2048-num_read, stdin);
        num_read += this_read;
        if (this_read != 0) {
            printf("%d\n", num_read);
        }
    }
    printf("test2.c done\n");
}
