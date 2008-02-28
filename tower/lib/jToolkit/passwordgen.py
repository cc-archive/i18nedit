# -*- coding: utf-8 -*-
##
## passwd.py v0.1
##
## modified by David Fraser <davidf@sjsoft.com>, 2001-08-10
## based on pgenerate.py (Author and description below)
## simple func generates an english-looking lowercase word with no funny chars
##
## Randomly creates a password with specified length, or picks
## a password from a dictionary. Also randomly warps the characters,
## making passwords from a dictionary more or less readable but
## slightly more difficult to crack.
##
##
## Author: Rikard Bosnjakovic <bos@hack.org>, 2001-06-12
##
from whrandom import choice, randint

# choose your dictionary
dictionary_file = '/usr/share/dict/words'

def createpassword(min_chars = 6, max_chars = 8):
    """createpassword([min_chars = 6, max_chars = 8):
Picks a password from a dictionary and warps it, with minimum and maximum chars as specified (default 6,8)."""

    # Get a word from a dictionary with minimum [min_chars] and maximum [max_chars] characters.
    word  = ""
    words = open(dictionary_file, "r").readlines()
    while (len(word) < min_chars) or (len(word) > max_chars):
        word = choice(words)

    password = word.lower().strip()

    # Warps around the chars in the password.
    import string

    warps = {}
    # add the alphabet to the warplist
    for x in xrange(ord('a'), ord('z')+1):
        x = chr(x)
        warps[x] = [x]

    # add some specials
    specialchars = (("a", ["e", "y"]),
                    ("b", ["p", "m"]),
                    ("c", ["k", "s"]),
                    ("d", ["t", "n"]),
                    ("e", ["i"]),
                    ("f", ["v", "ph"]),
                    ("g", ["k", "ng"]),
                    ("i", ["y"]),
                    ("j", ["z"]),
                    ("k", ["g"]),
                    ("l", ["y"]),
                    ("m", ["b", "p"]),
                    ("n", ["d", "t"]),
                    ("o", ["u"]),
                    ("p", ["b", "m"]),
                    ("q", ["k"]),
                    ("s", ["z"]),
                    ("t", ["d", "n"]),
                    ("u", ["o", "a"]),
                    ("v", ["f"]),
                    ("x", ["k"]),
                    ("z", ["s"]))

    for (a,b) in specialchars:
      warps[a] += b

    warped_password = ""
    # warp the chars in the password
    for i in password:
        if i in warps.keys():
            warped = password.startswith(warped_password)
            # 50% probability if warped, 75% if as yet unwarped
            if (warped and randint(0, 3)) or ((not warped) and  randint(0, 1)):
                warped_password += choice(warps[i])
            else:
                warped_password += i
        else:
            warped_password += i

    return warped_password

