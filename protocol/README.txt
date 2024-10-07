Here, we use UDP with sequence numbers. The sequence numbers should be identical to TCP sequence numbers
                                                                      bit
       |0  |1  |2  |3  |4  |5  |6  |7  |8  |9  |10 |11 |12 |13 |14 |15 |16 |17 |18 |19 |20 |21 |22 |23 |24 |25 |26 |27 |28 |29 |30 |31 |
       |byte 0                         |byte 1                         |byte 2                         |byte 3                         |
_______|_______________________________|_______________________________|_______________________________|_______________________________|
dword 1|                       sender (4-bit chars)                    |EOF|msg type (5-bit chars, 0='\0', 1=a, 2=b, ___, 27-31 unused)|
_______|_______________:_______________:_______________:_______________|___|___________________:___________________:___________________|
dword 2|ACK|SYN|FIN|        message length                             |                           checksum                            |
_______|___|___|___|___________________________________________________|_______________________________________________________________|
dword 2|                                                        sequence number                                                        |
_______|_______________________________________________________________________________________________________________________________|
dword 3|                                                           ack number                                                          |
_______|_______________________________________________________________________________________________________________________________|

Sender: This can be anything as long as it's 2 bytes. Suggested encoding method is to use
4-bit characters:
0123456789abcdef
abdghiklmnorstvw
def to_four_bit(string):
    map = {
        "a":"a",
        "b":"b",
        "c":("s","k"), # "s" for soft c, "k" for hard c
        "d":"d",
        "e": "",
        "f":"v",
        "g":"g",
        "h":"h",
        "i":"i",
        "j":"i",
        "k":"k",
        "l":"l",
        "m":"m",
        "n":"n",
        "o":"o",
        "p":"b",
        "q":"k",
        "r":"r",
        "s":"s",
        "t":"t",
        "u":"v",
        "v":"v",
        "w":"w",
        "x":"k",
        "y":"i",
        "z":"s",
    }
    return [map[x] for x in string]


EOF: This bit should default to 1. If you're sending a message that takes multiple packets,
such as a jpg, EOF should be 0 for all but the last packet in the message.


msg type: File extension, ie "jpg" for a jpg image. Use all zero for chat messages.


ACK: If this bit is 1, it's an ack packet, just like in TCP


SYN: If this bit is 1, it's a syn packet, just like in TCP. If they're both 1 it's an ACK-SYN.


FIN: If this bit is 1, it's a fin packet, just like in TCP.


message length: 12 bit unsigned int. The packet itself should always be 1024 bytes (subject to change).
The message length can be less than that if we aren't using the entire packet.
The message length does not include the header.


checksum: Checksum of the entire packet. To calculate, set the checksum to 0 and do as follows:
char packet[bytes_in_packet];
...
packet[6] = 0;
packet[7] = 0;
uint16_t checksum = 0;
for (int i = 0; i < bytes_in_packet; i += 2) {
    checksum ^= *(uint16_t*)(packet+i);
}
To verify the checksum, do:
uint16_t checksum = 0;
for (int i = 0; i < bytes_in_packet; i += 2) {
    checksum ^= *(uint16_t*)(packet+i);
}
assert(checksum == 0);


Sequence number: Same as in TCP


Ack number: Same as in TCP