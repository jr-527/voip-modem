#include "../common_algorithms/hamming.cpp"
#include <iostream>

int main() {
    for (uint8_t i = 0; i < 16; i++) {
        uint32_t tmp = 0;
        for (int j = 0; j < 8; j++) {
            tmp = tmp << 4;
            tmp += i;
        }
        quartets_32 q = quartets_32(tmp);
        septets_56 s = encode_hamming7_4(q);
        uint8_t x[7];
        bitsetToBytes<7>(s, x);
        septets_56 s2 = bytesToBitset<7>(x);
        if (s2 != s) {
            printf("Error on byte conversion\n");
            std::cout << "right: " << s << std::endl;
            std::cout << "array: ";
            for (int j = 0; j < 7; j++) {
                printf("%x ", x[j]);
            }
            printf("\n");
            std::cout << "wrong: " << s2 << std::endl;
        }
        quartets_32 q2 = decode_hamming7_4(s);
        if (q != q2) {
            printf("Error!\n");
        }
        for (int flipped_bit = 0; flipped_bit < 7; flipped_bit++) {
            s = encode_hamming7_4(q);
            for (int which_sept = 0; which_sept < 8; which_sept++) {
                s.flip(which_sept*7 + flipped_bit);
            }
            q2 = decode_hamming7_4(s);
            if (q != q2) {
                printf("Error on flipped bit: %d\n", flipped_bit);
                return -1;
            }
        }
    }
    printf("all tests done\n");
    return 0;
}