from subprocess import Popen, PIPE
import platform

def exe(filename):
    if platform.system() == "Linux":
        return "./%s"%filename
    elif platform.system() == "Windows":
        return "%s.exe"%filename
    else:
        raise RuntimeError("OS not supported")
        # apple is "Darwin" but not supported


p1 = Popen(['python', 'test1.py'], stdout=PIPE)
p2 = Popen(['python', 'test2.py'], stdin=p1.stdout)
p1.stdout.close() # enable write error
out, err = p2.communicate()

p1 = Popen([exe('test1')], stdout=PIPE)
p2 = Popen([exe('test2')], stdin=p1.stdout)
p1.stdout.close() # enable write error
out, err = p2.communicate()
