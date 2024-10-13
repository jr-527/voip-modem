#include "../defs.c"
#include "../common_algorithms/hamming.cpp"
// #include <iostream>

int main() {
    log("Decode (Hamming) Initializing\n");
    uint8_t encoded[7];
    uint8_t decoded[4];
    while (read_pipe((char*)encoded, 7) != -1) {
        septets_56 s = bytesToBitset<7>(encoded);
        quartets_32 q = decode_hamming7_4(s);
        bitsetToBytes<4>(q, decoded);
        write_pipe((char*)&decoded, 4);
    }
    log("Decode (Hamming) reached EOF\n");
}