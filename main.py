from pipe_setup import run_pipe
from defs import timestamp
from argparse import ArgumentParser

def main(args):
    print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
    print("@\n@")
    print("@ %s Starting voip-modem" % timestamp())
    print("@\n@")
    print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
    files = ["record/"+args.record, "demodulate/"+args.demod, "decode/"+args.decode,
        "protocol/"+args.protocol, "encode/"+args.encode, "modulate/"+args.mod,
        "play/"+args.play
    ]
    run_pipe(files)
    print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
    print("@\n@")
    print("@ %s voip-modem done" % timestamp())
    print("@\n@")
    print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")


if __name__ == "__main__":
    parser = ArgumentParser(prog="main.py", description="Runs the voip-modem")
    parser.add_argument("-record", default="test.py")
    parser.add_argument("-demod", default="test.py")
    parser.add_argument("-decode", default="test.py")
    parser.add_argument("-protocol", default="test.py")
    parser.add_argument("-encode", default="test.py")
    parser.add_argument("-mod", default="test.py")
    parser.add_argument("-play", default="test.py")
    args = parser.parse_args()
    main(args)
