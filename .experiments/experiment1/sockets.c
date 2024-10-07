#ifndef SOCKET_C
#define SOCKET_C
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <sys/un.h>
#include <unistd.h>

#define PRO_ENC_SOCK "/tmp/james_voip_modem_pe.socket"
#define ENC_MOD_SOCK "/tmp/james_voip_modem_em.socket"
#define MOD_AUD_SOCK "/tmp/james_voip_modem_ma.socket"
#define AUD_DEM_SOCK "/tmp/james_voip_modem_ad.socket"
#define DEM_DEC_SOCK "/tmp/james_voip_modem_dd.socket"
#define DEC_PRO_SOCK "/tmp/james_voip_modem_dp.socket"
#define TEST_SOCKET "/tmp/james_void_modem_test.socket"

typedef int Socket;
// typedef int HostSocket;
typedef struct HostSocket {
    Socket s;
    char name[252];
} HostSocket;
typedef struct ClientSocket {
    Socket s;
    char name[252];
} ClientSocket;

/**
 * @param socket_name Name of the socket. Use a name from sockets.c
 * @return (The host end of) a unix socket
 */
HostSocket Host(const char* socket_name) {
    unlink(socket_name);
    Socket connection_socket = socket(AF_UNIX, SOCK_SEQPACKET, 0);
    if (connection_socket == -1) {
        perror("socket");
        exit(EXIT_FAILURE);
    }
    struct sockaddr_un name;
    memset(&name, 0, sizeof(name));
    name.sun_family = AF_UNIX;
    strncpy(name.sun_path, socket_name, sizeof(name.sun_path)-1);
    if (bind(connection_socket, (const struct sockaddr*) &name, sizeof(name)) == -1) {
        perror("bind");
        exit(EXIT_FAILURE);
    }
    if (listen(connection_socket, 20) == -1) {
        perror("listen");
        exit(EXIT_FAILURE);
    }
    Socket data_socket = accept(connection_socket, NULL, NULL);
    if (data_socket == -1) {
        perror("accept");
        exit(EXIT_FAILURE);
    }
    fprintf(stderr, "Connected to socket %s as host\n", socket_name);
    HostSocket out;
    out.s = data_socket;
    strncpy(out.name, socket_name, 252);
    return out;
}

/**
 * @param host_sock The socket to read from
 * @param buf Buffer to write to
 * @param buf_size size of buf
 * @return Number of bytes written to buf
 */
int Host_get(HostSocket host_sock, char* buf, size_t buf_size) {
    Socket connection_socket = host_sock.s;
    int bytes_read = read(connection_socket, buf, buf_size);
    if (bytes_read == -1) {
        perror("read");
        exit(EXIT_FAILURE);
    }
    return bytes_read;
}

void Host_close(HostSocket host_sock) {
    fprintf(stderr, "Closing socket %s as host\n", host_sock.name);
    close(host_sock.s);
    unlink(host_sock.name);
}

/**
 * @param socket_name Name of the socket. Use a name from sockets.c
 * @return (The client end of) a unix socket
 */
ClientSocket Client(const char* socket_name) {
    Socket data_socket = socket(AF_UNIX, SOCK_SEQPACKET, 0);
    if (data_socket == -1) {
        perror("socket");
        exit(EXIT_FAILURE);
    }
    struct sockaddr_un addr;
    memset(&addr, 0, sizeof(addr));
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, socket_name, sizeof(addr.sun_path) - 1);
    if (connect(data_socket, (const struct sockaddr*)&addr, sizeof(addr)) == -1) {
        fprintf(stderr, "Receiver is not up.\n");
        exit(EXIT_FAILURE);
    }
    fprintf(stderr, "Connected to socket %s as client\n", socket_name);
    ClientSocket out;
    out.s = data_socket;
    strncpy(out.name, socket_name, 252);
    return out;
}

/**
 * @param client_sock The socket to write to
 * @param buf Buffer to read from
 * @param bytes_to_send Number of bytes to read (ie size of buf)
 */
void Client_send(ClientSocket client_sock, const char* buf, size_t bytes_to_send) {
    Socket data_socket = client_sock.s;
    int bytes_sent = 0;
    while ((size_t)bytes_sent < bytes_to_send) {
        bytes_sent += write(data_socket, buf+bytes_sent, bytes_to_send-bytes_sent);
    }
}

void Client_close(ClientSocket client_sock) {
    fprintf(stderr, "Closing socket %s as client\n", client_sock.name);
    close(client_sock.s);
}

#endif