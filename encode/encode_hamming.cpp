#include "../defs.c"
#include "../common_algorithms/hamming.cpp"
#include <iostream>

int main() {
    uint8_t decoded[4];
    uint8_t encoded[7];
    while (read_pipe((char*)&decoded, 4) != -1) {
        quartets_32 q = bytesToBitset<4>(decoded);
        septets_56 s = encode_hamming7_4(q);
        bitsetToBytes<7>(s, encoded);
        write_pipe((char*)encoded, 7);
    }
    log("encode (hamming v1) reached EOF\n");
}