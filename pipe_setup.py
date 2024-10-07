from subprocess import Popen, PIPE
import platform
import time

from defs import timestamp

def _exe(filename: str) -> list[str]:
    if len(filename) > 3 and filename[-3:] == ".py":
        return ["python", filename]
    if platform.system() == "Linux":
        return ["./%s"%filename]
    elif platform.system() == "Windows":
        return ["%s.exe"%filename]
    else:
        raise RuntimeError("OS not supported")
        # apple is "Darwin" but not supported

def run_pipe(program_list: list[str]) -> bytes:
    """
    Usage: pipe([file1, file2, ...])
    """
    programs = [_exe(filename) for filename in program_list]
    name_str = " | ".join((" ".join(x) for x in programs))
    t = timestamp()
    print("[%s]------------------------------------------"%t)
    print("[%s]run_pipe running:\n[%s]  %s" % (t,name_str,t))
    print("[%s]------------------------------------------"%t)
    if len(programs) == 1:
        process = Popen(programs[0])
        out, err = process.communicate()
        t = timestamp()
        print("[%s]------------------------------------------"%t)
        print("[%s]run_pipe done with:\n[%s]  %s" % (t,t,name_str))
        print("[%s]------------------------------------------"%t)
        return out
    else:
        print("[%s]  initializing %s" % (timestamp(), " ".join(programs[0])))
        prev = Popen(programs[0], stdout=PIPE)
    for filename in programs[1:-1]:
        print("[%s]  initializing %s" % (timestamp(), " ".join(filename)))
        cur = Popen(filename, stdin=prev.stdout, stdout=PIPE)
        prev = cur
    print("[%s]  initializing %s" % (timestamp(), " ".join(programs[-1])))
    last = Popen(programs[-1], stdin=prev.stdout)
    out, err = last.communicate()
    t = timestamp()
    print("[%s]------------------------------------------"%t)
    print("[%s]run_pipe done with:\n[%s]  %s" % (t,t,name_str))
    print("[%s]------------------------------------------"%t)
    return out

def main():
    run_pipe(["test0.py"])
    run_pipe(["test1.py", "test2.py"])
    run_pipe(["test1", "test2"])

if __name__ == "__main__":
    main()
