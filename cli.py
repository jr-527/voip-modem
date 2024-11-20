import time
from datetime import datetime
import sys
from os import system, get_terminal_size, getlogin, path
import threading
from typing import Callable, Any
from enum import Enum
import logging
from socket import gethostname
import traceback
# Windows-specific stuff, I think:
system("")

esc = "\x1b["
color_red = esc + "31m"
color_green = esc + "32m"
color_yellow = esc + "33m"
color_blue = esc + "34m"
color_magenta = esc + "35m"
color_cyan = esc + "36m"
color_gray = esc + "90m"
color_reset = esc + "39m"
font_bold = esc + "1m"
font_no_bold = esc + "22m"
font_underline = esc + "4m"
font_no_underline = esc + "24m"
reset = esc + "0m"
UP_ONE = esc + "1A"
clear_line = esc + "2K"

def gen_timestamp(dt: datetime|None = None) -> str:
    if dt is None:
        dt = datetime.now()
    minute = str(dt.minute).rjust(2, '0')
    second = str(dt.second).rjust(2, '0')
    return f'{dt.hour}:{minute}:{second}'


def write(message: str):
    print("\x1b[s\x1b[1A\x1b[999D\x1b[1S\x1b[L"+message+"\x1b[u", end="",flush=True)


def write_chat_message(contents: str, sender="user", timestamp=None):
    if not contents.isprintable():
        # We don't allow people to mess with formatting by sending escape
        # codes or whatever other nonsense.
        contents = color_yellow + "[invalid message]" + color_reset
    out = []
    out2 = []
    if timestamp is not None:
        out.append(color_gray + f'{timestamp}')
        out2.append(f"{timestamp} ")
    out.append(color_blue + f'[{sender}]')
    out2.append(f"[{sender}]")
    write(''.join(out) + color_reset + contents)
    logging.info(f''.join(out2) + contents)


def write_system_message(contents: str, sender="SYSTEM", timestamp=None):
    out = [color_magenta]
    out2 = []
    if timestamp is not None:
        out.append(f'{timestamp} ')
        out2.append(f"{timestamp} ")
    write(''.join(out) + f'[{sender}]' + contents + color_reset)
    logging.info("system message"+ f" ({sender}):" + contents)



class UIenum(Enum):
    valid_chat = 0
    invalid = 1
    change_name = 2
    not_implemented = 3
    no_op = 4
    exit = 5



class UIMessage:
    type: UIenum
    msgval: Any
    def __init__(self, msgtype: UIenum, msgval:Any=None):
        self.type = msgtype
        self.val = msgval



def init_term():
    lines = get_terminal_size().lines
    print("\n"*(lines-1))


intro_text = color_yellow + """Type a message that doesn't start with / to send a chat message.
To type a command, type something that starts with /, such as /help.
Type /quit or press ctrl+c to quit (you may have to press ctrl+shift+c)
"""[:-1] + color_reset

help_text = color_yellow + """List of commands:
/exit                   Exit
/help                   Show the list of commands
/quit                   Exit
/upload filename        Send that file to other people using the voip-modem
/username new_username  Set your username to new_username
"""[:-1] + color_reset


class UserInterface:
    username: str = getlogin() + "@" + gethostname()
    stop = False
    def __init__(self, exit_callback: Callable[[], None]=lambda:None, log_to_file=False):
        """
        input_callback: A function. Whenver the user inputs something,
        this will call input_callback(user_input).
        """
        self.exit_callback = exit_callback
        if log_to_file:
            logging.basicConfig(format="%(message)s", filename="log.log", filemode='w',
                                level=logging.DEBUG)
            logging.info("Starting at: " + str(datetime.now()))
        # else:
        #     logging.basicConfig(format="%(message)s", filename="log.log", filemode='w',
        #                         level=logging.ERROR)


    def user_input_thread(self):
        try:
            while not self.stop:
                sys.stdout.flush()
                user_input = input().replace("\t", " "*4)
                if len(user_input) == 0:
                    print(UP_ONE + "\r" + esc + "2K", end='')
                    continue
                if not user_input.isprintable():
                    msg = "Your message was not sent because it contains nonprintable characters."
                    print(UP_ONE + "\r" + color_yellow + msg + color_reset)
                    continue
                logging.info(gen_timestamp() + "<self>" + user_input)
                retval = self.user_input(user_input)
                if retval.type == UIenum.valid_chat:
                    print(UP_ONE + "\r" + color_gray + gen_timestamp() + color_red, end='')
                    print(f"[{self.username}]" + color_reset + user_input)
                elif retval.type == UIenum.invalid:
                    # out = UP_ONE + "\r" + color_yellow + "Invalid"
                    out = "\r" + color_yellow + "Invalid"
                    if retval.val is not None:
                        out += ": " + retval.val
                    out += color_reset
                    print(out)
                    logging.info(out[len("\r"+color_yellow):-len(color_reset)])
                elif retval.type == UIenum.change_name:
                    self.username = retval.val # type: ignore
                    print(UP_ONE + clear_line + color_yellow + "Username changed" + reset)
                elif retval.type == UIenum.no_op:
                    continue
                elif retval.type == UIenum.exit:
                    print(color_magenta + "Goodbye" + reset)
                    self.exit_callback()
                    sys.exit()
        except KeyboardInterrupt:
            print(color_magenta + "Goodbye" + reset)
            self.exit_callback()
            sys.exit()
        except Exception:
            print(traceback.format_exc())
            sys.exit()


    def write_chat_message(self, contents: str, sender="user", timestamp=None):
        write_chat_message(contents, sender, timestamp)


    def write_system_message(self, contents: str, sender="SYSTEM", timestamp=None):
        write_system_message(contents, sender, timestamp)


    def run(self, protocol):
        self.protocol = protocol
        lines = get_terminal_size().lines
        print("\n"*(lines-1-intro_text.count('\n')))
        print(intro_text)
        t = threading.Thread(target=self.user_input_thread, daemon=True)
        t.start()


    def user_input(self, msg: str) -> UIMessage:
        try:
            if msg[0] == "/":
                if msg[1:10] == "username ":
                    new_username = msg[10:]
                    if not 1 <= len(new_username) <= 20:
                        return UIMessage(UIenum.invalid,
                                        "username too long (must be 1-20 chars)")
                    return UIMessage(UIenum.change_name, new_username)
                if msg[1:5] == "help":
                    print(help_text)
                    return UIMessage(UIenum.no_op)
                if msg[1:5] in ("exit", "quit"):
                    return UIMessage(UIenum.exit)
                if msg[1:8] == "upload ":
                    filename = msg.split()[1]
                    if not path.exists(filename):
                        return UIMessage(UIenum.invalid, f"file {filename} not found")
                    print(color_yellow + "sending files is not implemented yet" + reset)
                    return UIMessage(UIenum.not_implemented)
                return UIMessage(UIenum.invalid, "not a valid command")
            else:
                now = datetime.now()
                timestamp = chr(now.hour) + chr(now.minute) + chr(now.second)
                payload = self.username + '\x7f' + msg + '\x7f' + timestamp
                self.protocol.transmit(payload.encode("utf-8"), "\0\0\0")
                return UIMessage(UIenum.valid_chat)
        except:
            return UIMessage(UIenum.invalid)


class DummyUI(UserInterface):
    def __init__(self):
        pass

    def write_chat_message(self, contents: str, sender="user", timestamp=None):
        pass

    def write_system_message(self, contents: str, sender="SYSTEM", timestamp=None):
        pass

    def run(self, protocol):
        pass

if __name__ == "__main__":
    try:
        ui = UserInterface()
        class dummyprotocol:
            def transmit(*args, **kwargs):
                print("\ntransmit!!!1\n")
        ui.run(dummyprotocol())
        while True:
            time.sleep(1)
    except:
        pass