from os import _exit

import time
import argparse
import traceback

# my modules
from cli import (UserInterface, UIenum, UIMessage, reset, color_magenta,
    help_text, color_yellow
    )
from protocol import Protocol
from play import PlaybackWorker, PipedConsumer
from piped_worker import DummyPipedWorker
from modulate import ModulateOFDM
from demodulate import DemodulateOFDM
import initialize

should_exit = False


def exit_callback():
    # sys.exit isn't powerful enough
    _exit(0)


def main():
    # get device indices
    parser = argparse.ArgumentParser(prog="voip-modem 0.2.0")
    parser.add_argument("-i", "--input", type=int)
    parser.add_argument("-o", "--output", type=int)
    parser.add_argument("-l", "--log", action="store_true")
    args = parser.parse_args()
    input_idx = args.input # -1 for no input
    output_idx = args.output # -1 for no output
    if (args.input is None) or (args.output is None):
        try:
            input_idx, output_idx = initialize.main()
        except KeyboardInterrupt:
            return
    ui = UserInterface(exit_callback=exit_callback, log_to_file=args.log)
    protocol = Protocol(ui)
    modulator = ModulateOFDM()
    demodulator = DemodulateOFDM()
    player: PipedConsumer
    if output_idx is not None and output_idx != -1:
        player = PlaybackWorker(output_idx, samples_per_buffer=3840)
    else:
        player = DummyPipedWorker()
    modulator.set_target(player)
    # modulator.set_target(demodulator)
    demodulator.set_target(protocol)
    protocol.set_target(modulator)
    protocol.run()
    ui.run(protocol)
    player.run()
    try:
        while not should_exit:
            time.sleep(.103)
    except Exception:
        print("uncaught exception:")
        print(traceback.format_exc())
    except KeyboardInterrupt:
        ui.stop = True
        print(reset)
        print(color_magenta + "Exiting" + reset)


if __name__ == "__main__":
    main()