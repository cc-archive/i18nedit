import os
import sys
import time
from optparse import OptionParser

def tail_lines(fd, linesback = 10, avgcharsperline=75):
    # Contributed to Python Cookbook by Ed Pascoe (2003)
    while 1:
        try:
            fd.seek(-1 * avgcharsperline * linesback, 2)
        except IOError:
            fd.seek(0)

        if fd.tell() == 0:
            atstart = 1
        else:
            atstart = 0

        lines = fd.read().split("\n")
        if (len(lines) > (linesback+1)) or atstart:
            break

        avgcharsperline=avgcharsperline * 1.3

    if len(lines) > linesback:
        start = len(lines) - linesback - 1
    else:
        start = 0

    return lines[start:len(lines)-1]

def reduce_files_to_tail(files, linesback=10, avgcharsperline=75):
    if isinstance(files, str):
        files = [files]
    for fname in files:
        fd = open(fname, 'r')
        lines = tail_lines(fd, linesback, avgcharsperline)
        lines = [line + '\n' for line in lines]
        fd.close()
        print "Writing %d lines to %s" % (linesback, fname)
        fd = open(fname, 'w')
        fd.writelines(lines)
        fd.close()        

def handle_line(line):
    print line,


def do_tail(filename, lines, follow, func = handle_line):
    fd = open(filename, 'r')

    for line in tail_lines(fd, lines):
        func(line + "\n")

    if not follow:
        return

    while 1:
        where = fd.tell()
        line = fd.readline()
        if not line:
            fd_results = os.fstat(fd.fileno())
            try:
                st_results = os.stat(filename)
            except OSError:
                st_results = fd_results

            if st_results[1] == fd_results[1]:
                time.sleep(1)
                fd.seek(where)
            else:
                print "%s changed inode numbers from %d to %d" % (filename, fd_results[1], st_results[1])
                fd = open(filename, 'r')
        else:
            func(line)

def main(argv = sys.argv):
    parser = OptionParser()
    parser.add_option("-n", "--number", action="store", type="int", dest = "number", default=10)
    parser.add_option("-f", "--follow", action="store_true", dest = "follow", default=0)
    (options, args) = parser.parse_args()
    do_tail(args[0], options.number, options.follow, handle_line)

if __name__ == "__main__":
    try:
        main(sys.argv)
    except KeyboardInterrupt:
        pass

