import bchlib
import math
import struct
bch = bchlib.BCH(12, m=12)

SYMBOL_BYTES = 480
PACKET_SIZE = SYMBOL_BYTES - math.ceil(bch.ecc_bits/8)

def encode(data: bytes) -> bytes:
    assert len(data) == PACKET_SIZE
    ecc = bch.encode(data)
    return data + ecc


def decode(symbol: bytes) -> bytes:
    assert len(symbol) == SYMBOL_BYTES
    payload = bytearray(symbol[:PACKET_SIZE])
    ecc = bytearray(symbol[PACKET_SIZE:])
    bch.decode(payload, ecc)
    bch.correct(payload, ecc)
    return bytes(payload)


def split_packet(packet: bytes) -> None|dict:
    assert len(packet) == PACKET_SIZE
    checksum = 0
    checksum = 0
    for i in range(PACKET_SIZE//2):
        checksum += struct.unpack("H", packet[2*i:2*i+2])[0]
    checksum = (~(checksum & 0xFFFF) + 1) & 0xFFFF
    if checksum != 0:
        # packet is corrupted
        return None
    out = {}
    filetype = []
    out["ack"] = (packet[0] & 128) != 0
    out["syn"] = (packet[1] & 128) != 0
    out["fin"] = (packet[2] & 128) != 0
    out["eof"] = (packet[3] & 128) != 0

    for i in range(4):
        x = packet[i] & 127
        if x:
            filetype.append(chr(x))
        else:
            break
    out["datatype"] = ''.join(filetype)
    out["sender"] = packet[5] & 0b0111_1111
    length = int(packet[4]) + 2 * (int(packet[5]) & 0b1000_0000)
    out["payload"] = packet[16:16+length]
    out["seq_num"] = struct.unpack("I", packet[8:12])[0]
    out["ack_num"] = struct.unpack("I", packet[12:16])[0]
    return out


def into_packet(sender: int, eof: bool, datatype: str, ack: bool, syn: bool, fin: bool,
                seq_num: int, ack_num: int, payload: bytes) -> bytes:
    assert len(datatype) <= 4
    assert 0 <= len(payload) <= PACKET_SIZE - 16
    # qword1 = bytearray(datatype, encoding="utf-8") + bytearray(4-len(datatype))
    # ascii is 0-127 so we can stuff an extra bit into the MSB
    packet = bytearray(PACKET_SIZE)
    packet[0:len(datatype)] = bytearray(datatype, encoding="utf-8")
    packet[0] |= ack << 7
    packet[1] |= syn << 7
    packet[2] |= fin << 7
    packet[3] |= eof << 7

    packet[4] = len(payload) & 255
    packet[5] = sender & 127
    packet[5] |= (len(payload) & 256) >> 1
    
    packet[8:12] = struct.pack("I", seq_num)
    packet[12:16] = struct.pack("I", ack_num)

    packet[16:16+len(payload)] = payload

    checksum = 0
    for i in range(PACKET_SIZE//2):
        checksum += struct.unpack("H", packet[2*i:2*i+2])[0]
    checksum = (~(checksum & 0xFFFF) + 1) & 0xFFFF
    packet[6:8] = struct.pack("H", checksum)
    return bytes(packet)

if __name__ == "__main__":
    packet = into_packet(15, False, "txt", True, False, False, 123, 10123, b"hello, how are you")
    packet = bytearray(packet)
    x = split_packet(packet)
    assert x is not None
    y = into_packet(**x)
    z = split_packet(y)
    assert z is not None
    for k, v in z.items():
        assert x[k] == v
    for k, v in x.items():
        assert z[k] == v