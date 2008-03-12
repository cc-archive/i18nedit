"""
Usage:

split_po.py [source_dir] [output_dir]
"""

import os
import sys
import codecs
import string

import babel.messages.pofile

def message_fn(msg):
    """Return the file path used to store this message value."""

    ID_PATH_CHARS = string.ascii_letters + '. '

    # calculate the filename
    id_src = "".join([n for n in msg.id if n in ID_PATH_CHARS]).lower()
    words = id_src.split()

    if len(words) == 1:
        return words[0] + '.txt'
    
    filename = "-".join([''] + words[:4] + [str(abs(hash(msg.id)))])
    filename += ".txt"

    return filename

if __name__ == '__main__':

    src_dir = sys.argv[-2]
    dest_dir = sys.argv[-1]

    for root, dirs, files in os.walk(src_dir):

        # skip .svn dirs
        if '.svn' in dirs:
            del dirs[dirs.index('.svn')]

        mid_dir = root[len(src_dir):]

        if not os.path.exists(os.path.join(dest_dir, mid_dir)):
            os.makedirs(os.path.join(dest_dir, mid_dir))

        for fn in files:
            if fn[-3:] == '.po':
                # process this file
                catalog = babel.messages.pofile.read_po(
                    file(os.path.join(root, fn), 'r'))

                for msg in catalog:
                    codecs.open(os.path.join(dest_dir, mid_dir, message_fn(msg)), 
                                'w', 'utf-8').write(msg.string)


