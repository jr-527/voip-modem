from piped_worker import PipedWorker
from cli import UserInterface, UIenum, UIMessage, DummyUI, gen_timestamp
import sys
import os
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import packet
import threading
import time
from enum import Enum
import traceback
from queue import Queue
# import json

senders = {
    74:"James"
}
localsender = 74
int32_min = -2147483647
to_ack_limit = 50

# if we send this many packets without receiving anything, the connection is dead
heartbeat_timeout = 45

def gen_syn(seq_num):
    return packet.into_packet(localsender, False, "\0\0\0", False, True,
                                    False, seq_num, 0, b"")


class Protocol(PipedWorker):
    def __init__(self, interface: UserInterface, timeout_count=10, restart=False,
                 packet_period=4096/48000):
        self.packet_period = packet_period
        self.stop = False
        self.tick = 0
        self.last_hb = None
        self.ui = interface
        self.timeout_count = timeout_count
        if not restart:
            self.ui.write_system_message("Protocol initializing", 
                                         "modem", gen_timestamp())
        self.highest_seq_sent: int = 0
        self.highest_ack_received: None|int = None
        self.next_ack: None|int = None
        self.to_ack: dict[int, dict] = {} # seq_num -> (datatype, payload, fin)
        self.next_type: str = "syn"
        # sent seq_num -> (tick, pkt) for which we have not received an ack
        # seq_num: The sequence number of this packet
        # tick: The tick on which we sent this packet
        # pkt: The bytes of the packet (for easy re-sending)
        self.sent: dict[int, tuple] = {}
        # data_to_send is data that the user wants us to send, (filetype, eof, data)
        # filetype: string of length 3
        # eof: Is this the end of a file (true for chat messages)
        # data: The payload for this packet. Length should be <= packet.PACKET_SIZE
        self.data_to_send = Queue()
        self.first_ack: None|int = None
        self.second_ack: None|int = None
        self.third_ack: None|int = None

    def _writer_iteration(self):
        try:
            self.tick += 1
            # if we have a connection but haven't received any packets in a while,
            # we consider the connection dead and reset.
            if self.last_hb is not None and (self.tick-self.last_hb) > heartbeat_timeout:
                self.ui.write_system_message("Lost connection (timed out)",
                                             "modem", gen_timestamp())
                self.__init__(self.ui, self.timeout_count, restart=True)
            # if we don't have a connection, we just broadcast SYN packets, waiting
            # for somebody to reply
            if self.last_hb is None:
                data = packet.encode(packet.into_packet(sender=localsender,
                        eof=True, datatype="...", ack=False, syn=True, fin=False,
                        seq_num=self.highest_seq_sent, ack_num=0, payload=b""))
                # We don't bother adding this to self.sent, and send the same packet
                # each time, to simplify our logic.
                # self.ui.write_system_message("sending SYN")
                self.target.push(data)
                return
            # If the oldest entry in self.sent is too old, we resend it
            if self.highest_ack_received is not None:
                tmp = self.sent.get(self.highest_ack_received+1, (self.tick, None))
                if tmp[0] + self.timeout_count < self.tick:
                    self.target.push(tmp[1])
                    return
            # In the case of triple duplicate acks, we resend the sequence number above
            # that ack. I'm not sure if this is necessary, because we can just use the
            # timeout.
            # if self.first_ack == self.second_ack == self.third_ack != None:
            #     if self.first_ack+1 in self.sent: # type: ignore
            #         tmp = self.sent[self.first_ack+1][1] # type: ignore
            #         self.target.push(tmp[1])

            # otherwise we act normally
            filetype, eof, payload = "...", True, b""
            if not self.data_to_send.empty():
                filetype, eof, payload = self.data_to_send.get()
            if self.next_ack is None:
                raise RuntimeError("No ack available")
            ack = True
            ack_num = self.next_ack
            syn = False
            if self.next_ack == "syn-ack":
                self.next_type = "ack"
                syn = True
            fin = False
            self.highest_seq_sent += 1
            seq_num = self.highest_seq_sent
            # system_message = f"Sending ack={ack_num}"
            # if syn:
            #     system_message += " [SYN]"
            # self.ui.write_system_message(system_message)
            data = packet.encode(packet.into_packet(sender=localsender, eof=eof,
                    datatype=filetype, ack=ack, syn=syn, fin=fin, seq_num=seq_num,
                    ack_num=ack_num, payload=payload))
            self.sent[seq_num] = (self.tick, data)
            self.target.push(data)
        except Exception as e:
            print(traceback.format_exc())

    def _handle_payload(self, pkt: dict):
        try:
            if len(pkt["datatype"]) == 0:
                # chat message
                msg = pkt["payload"].decode("utf-8").split("\x7F")
                sender = msg[0]
                body = msg[1]
                timestamp = None
                if len(msg) == 3:
                    ts_bytes = msg[2] # should be 3 bytes
                    h = str(ord(ts_bytes[0]))
                    mm = str(ord(ts_bytes[1])).rjust(2, '0')
                    ss = str(ord(ts_bytes[2])).rjust(2, '0')
                    timestamp = h + ':' + mm + ':' + ss
                self.ui.write_chat_message(body, sender, timestamp)
            elif pkt["datatype"] == "...": # empty packet used to keep the connection up
                pass
            else:
                pass # not implemented
        except Exception as e:
            print(traceback.format_exc())
            # malformed, not sure what to do

    def _writer_thread(self):
        start_time = time.monotonic()
        prev = start_time
        delay = self.packet_period
        while not self.stop:
            now = time.monotonic()
            if now - prev >= 2*self.packet_period:
                errmsg="Execution too slow! Took %f s to execute (has to execute in %f s)"
                errmsg %= (now-prev, delay)
                raise RuntimeError(errmsg)
            prev = now
            self._writer_iteration()
            time.sleep(delay - ((time.monotonic() - start_time) % delay))
        self.ui.write_system_message("Modem shutting down", "modem", gen_timestamp())
            

    def push(self, data: bytes):
        decoded = packet.decode(data) # remove ECC
        pkt = packet.split_packet(decoded)
        if pkt is None:
            # print("received invalid packet")
            return
        # print("received valid packet")
        if pkt["syn"] and not pkt["ack"]:
            self.next_type = "syn-ack"
        # message_summary = f"Received seq: {pkt["seq_num"]}"
        # if pkt["syn"]:
        #     message_summary += f" [syn]"
        # if pkt["ack"]:
        #     message_summary += f" ack: {pkt["ack_num"]}"
        # self.ui.write_system_message(message_summary)
        self.last_hb = self.tick
        # figure out which seq numbers have been acked so far
        if pkt["ack"]:
            self.third_ack = self.second_ack
            self.second_ack = self.first_ack
            seq_num: int = pkt["ack_num"]
            self.first_ack = seq_num
            if not self.highest_ack_received:
                self.highest_ack_received = seq_num
            if seq_num > self.highest_ack_received:
                self.highest_ack_received = seq_num
                for k in list(self.sent.keys()):
                    if k <= self.highest_ack_received:
                        self.sent.pop(k)
            seq_num = max(seq_num, self.highest_ack_received)
        elif pkt["syn"]:
            self.next_type = "syn-ack"

        # figure out which ack number we have to send next
        ack_num = pkt["seq_num"] # This is our ack number, so their sequence number
        if self.next_ack is None: # initializing
            self.ui.write_system_message("Connection established","modem",gen_timestamp())
            self.next_ack = ack_num
            self._handle_payload(pkt)
            return
        if ack_num <= self.next_ack or ack_num in self.to_ack: # already received
            return
        self.to_ack[ack_num] = pkt
        length = len(self.to_ack)
        new_next_ack = self.next_ack
        for i in range(1, length+1):
            if self.next_ack+i not in self.to_ack:
                break
            self._handle_payload(self.to_ack.pop(self.next_ack+i))
            new_next_ack += 1
        self.next_ack = new_next_ack

    
    def transmit(self, data: bytes, datatype: str):
        if len(data) == 0:
            return
        payloads = [data[i:i+packet.PACKET_SIZE]
                    for i in range(0, len(data), packet.PACKET_SIZE)]
        for payload in payloads[:-1]:
            self.data_to_send.put((datatype, False, payload))
        self.data_to_send.put((datatype, True, payloads[-1]))


    def run(self):
        self.stop = False
        t = threading.Thread(target=self._writer_thread, daemon=True)
        t.start()


"""
Process for sending packets (not including syn packets):
if deque is full: count that as timeout, oldest packet needs to be resent
Send a packet with next sequence number
put packet onto end of deque

When we receive an ack:
1. Remove all deque elements with sequence number <= ack number
2. Set prev_ack = this ack, count += 1
3. If count is 3 (subject to change), next packet is lost, resend
"""

def easy_packet(n):
    rs = "\x7F"
    timestamp = chr(10) + chr(51) + chr(n)
    chat_msg = "bob" + rs + "this message has ack number " + str(n) + rs + timestamp
    x = packet.into_packet(0, True, "\0\0\0", True, False, False, n, 0,
                           bytes(chat_msg, "utf-8"))
    return packet.encode(x)


if __name__ == "__main__":
    ui = UserInterface()
    dummy_ui = DummyUI()
    p = Protocol(ui)
    p2 = Protocol(dummy_ui)
    p.set_target(p2)
    p2.set_target(p)
    p.run()
    time.sleep(1)
    p2.run()
    time.sleep(.5)
    rs = "\x7F"
    timestamp = chr(10) + chr(51) + chr(3)
    # print("Sending chat message")
    chat_msg = bytes("bob" + rs + "hello, how are you" + rs + timestamp, "utf-8")
    p2.transmit(chat_msg, "\0\0\0")
    time.sleep(3)
    print("p2 stopping")
    p2.stop = True
    try:
        while 1:
            time.sleep(.1)
    except KeyboardInterrupt:
        pass
