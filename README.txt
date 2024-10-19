Plan:

Structure (each box is a process)
 _________________________________
|                                 |
|              main.py            |
|  _____________________________  |
| |           protocol          | |
| |    (1024-byte TCP-like)     | |
| |_____________________________| |
|     |                     A     |
|  packets                  |     |
|     |                  packets  |
|  ___V_________   _________|___  |
| |   encode    | |    decode   | |
| |Hamming(7,4)?| |Hamming(7,4)?| |
| |_____________| |_____________| |
|     |                     A     |
| bits w/ ECC               |     |
|     |               bits w/ ECC |
|  ___V________     ________|___  |
| |  modulate  |   | demodulate | |
| |    OFDM?   |   |    OFDM?   | |
| |____________|   |____________| |
|     |                     A     |
| digital signal            |     |
|     |            digital signal |
|  ___V___              ____|___  |
| |       |            |        | |
| | play  |            | record | |
| |_______|            |________| |
|    |                      A     |
|____|______________________|_____|
     |                      |
   audio                    |
     |                    audio
     V                      |
outside world (presumably discord)


main.py handles starting and stopping starts all the other components and piping
their outputs together. It's called as follows:
    python main.py -record=recorder -demod=demodulator -decode=decoder.py \
    -protocol=protocol.py -encoder=encoder -mod=modulator -play=sound_player

Here, there's an executable file called "recorder.exe" in the record folder, an
executable called "demodulator.exe" in the demod folder, a Python script called
"decoder.py" in the decode folder, etc.

Each component should be either a Python 3 script or an executable. The
executables' names should end in ".exe" on Windows, ie "sound_player.exe", and
have no further extension on Linux, ie "sound_player".

Each component (other than record) should accept input via stdin, and each
process (other than play) should give its output via stdout. Maybe the protocol
should also be able to take user input in some other way, so that you can give
the system commands while it's running, as stdin is already taken.

Here is what each component does:

record: Record audio and output it as a digital signal. The output should use
one 32-bit float per sample. It doesn't particularly matter what the sample
rate is, as long as the "play" component uses the same sample rate.

demodulate: Demodulate the digital signal. The "modulate" component should use
the same algorithm in reverse. It should output bytes.

decode: Remove any ECC.

protocol: Uses a custom packet format that's kinda like a minimized TCP.  Add
headers/metadata, handle ACKs/handshakes, resend dropped packets, etc. Should
probably use COBS.

encode: Apply ECC.

modulate: Modulate bytes to a digital signal. Should be the inverse of the
"demod" component.

play: Play the digital signal as audio. Should be the inverse of the "play"
component. If no data is available, it should be silent and wait.

I made a read_pipe and write_pipe function in defs.c and defs.py. The C
read_pipe function blocks until it reads the desired number of bytes. The Python
one returns however many bytes it finds. Both write_pipe functions block until
they've sent out their entire input.

I also made a log function in defs.c and defs.py. In C, log(...) is equivalent
to fprintf(stderr, ...), and the Python one has an identical call signature to
the C one, although newlines are automatically appended.
