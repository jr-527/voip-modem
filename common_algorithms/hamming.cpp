#include "../defs.c"
#include <bitset>
#include <iostream>

typedef std::bitset<56> septets_56;
typedef std::bitset<32> quartets_32;
typedef std::bitset<7> septet;
typedef std::bitset<4> quartet;

template<size_t numBytes>
std::bitset<numBytes * 8> bytesToBitset(uint8_t data[numBytes]) {
    std::bitset<numBytes * 8> b;
    for (size_t i = 0; i < numBytes; ++i) {
        (b <<= 8) |= data[i];
    }
    return b;
}

template<size_t numBytes>
void bitsetToBytes(std::bitset<numBytes*8> bitset, uint8_t data[numBytes]) {
    for (size_t byte = 0; byte < numBytes; byte++) {
        data[byte] = 0;
        for (size_t bit = 0; bit < 8; bit++) {
            bool this_bit = bitset[(numBytes-byte-1)*8 + bit];
            uint8_t as_byte = this_bit ? 1 : 0;
            data[byte] |= as_byte << bit;
        }
    }
}

quartet decode_hamming7_4(septet code) {
    int p1 = code[0] ^ code[2] ^ code[4] ^ code[6];
    int p2 = code[1] ^ code[2] ^ code[5] ^ code[6];
    int p3 = code[3] ^ code[4] ^ code[5] ^ code[6];
    int incorrect_bit = (p3 << 2) | (p2 << 1) | p1;
    if (incorrect_bit) {
        code[incorrect_bit-1] = code[incorrect_bit-1] ^ 1;
    }
    quartet out;
    out[0] = code[2];
    out[1] = code[4];
    out[2] = code[5];
    out[3] = code[6];
    return out;
}

septet encode_hamming7_4(quartet data) {
    septet code;
    code[2] = data[0];
    code[4] = data[1];
    code[5] = data[2];
    code[6] = data[3];

    code[0] = code[2] ^ code[4] ^ code[6];
    code[1] = code[2] ^ code[5] ^ code[6];
    code[3] = code[4] ^ code[5] ^ code[6];
    return code;
}

quartets_32 decode_hamming7_4(septets_56 code) {
    quartets_32 out;
    for (int i = 0; i < 8; i++) {
        septet s;
        for (int j = 0; j < 7; j++) {
            s[j] = code[7*i + j];
        }
        quartet q = decode_hamming7_4(s);
        for (int j = 0; j < 4; j++) {
            out[4*i + j] = q[j];
        }
    }
    return out;
}

septets_56 encode_hamming7_4(quartets_32 data) {
    septets_56 out;
    for (int i = 0; i < 8; i++) {
        quartet q;
        for (int j = 0; j < 4; j++) {
            q[j] = data[4*i + j];
        }
        septet s = encode_hamming7_4(q);
        for (int j = 0; j < 7; j++) {
            out[7*i + j] = s[j];
        }
    }
    return out;
}

quartet uint8_t_to_quartet(uint8_t n) {
    quartet out;
    out[0] = n & 1;
    out[1] = (n & 2) >> 1;
    out[2] = (n & 4) >> 2;
    out[3] = (n & 8) >> 3;
    return out;
}

