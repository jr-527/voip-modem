#ifndef DEFS_C
#define DEFS_C
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#ifdef _WIN32
#include <io.h>
#include <fcntl.h>
int stdin_is_initialized = 0;
#endif // #ifdef _WIN32

#define log(...) fprintf(stderr, __VA_ARGS__)

/**
 * Reads up to max_bytes from stdin.
 * @param buf Buffer where read bytes will be placed
 * @param max_bytes Maximum number of bytes to place in buf
 * @return Returns number of bytes read, EOF in the event of EOF.
 */
int short_read_pipe(char* buf, size_t max_bytes) {
    #ifdef _WIN32
    if (!stdin_is_initialized) {
        _setmode(_fileno(stdin), _O_BINARY);
        stdin_is_initialized = 1;
    }
    #endif
    size_t num_read = fread(buf, 1, max_bytes, stdin);
    if (feof(stdin)) {
        return EOF;
    }
    if (ferror(stdin)) {
        perror("Error reading from stdin");
        exit(1);
    }
    return num_read;
}

/**
 * Reads num_bytes bytes from stdin, blocking until complete.
 * @param buf Buffer to place bytes into
 * @param num_bytes Number of bytes to read
 * @return Returns 0 on success, -1 on failure.
 */
int read_pipe(char* buf, size_t num_bytes) {
    #ifdef _WIN32
    if (!stdin_is_initialized) {
        _setmode(_fileno(stdin), _O_BINARY);
        stdin_is_initialized = 1;
    }
    #endif
    size_t num_read = 0;
    while (num_read == 0) {
        num_read += fread(buf+num_read, 1, num_bytes-num_read, stdin);
        if (feof(stdin)) {
            return EOF;
        }
        if (ferror(stdin)) {
            perror("Error reading from stdin");
            exit(1);
        }
    }
    return num_read;
}

int write_pipe(char* buf, size_t num_bytes) {
    size_t num_written = 0;
    while (num_written < num_bytes) {
        num_written += fwrite(buf+num_written, 1, num_bytes-num_written, stdout);
    }
    fflush(stdout);
    return 0;
}
#endif // #ifndef DEFS_C