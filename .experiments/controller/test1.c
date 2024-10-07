#include <stdio.h>
#include <stdint.h>

int8_t buf[2048];
int main() {
    for (int i = 0; i < 2048; i++) {
        // buf[i] = 12;
        buf[i] = i%128;
    }
    int num_written = 0;
    while (num_written < 2048) {
        num_written += fwrite(buf+num_written, 1, 2048-num_written, stdout);
        // fprintf(stderr, "num_written: %d\n", num_written);
    }
    fflush(stdout);
    fprintf(stderr, "test1.c: done writing\n");
    return 0;
}
