#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""completely insecure encryption"""

from cgi import escape
import base64

def encryptandescape(plaintext, key):
  ciphertext = encrypt(plaintext, key)
  linelength = 70
  escapedtext = ""
  for linestart in range(0,len(ciphertext),linelength):
    line = ciphertext[linestart:linestart+linelength-1]
    escapedtext += escape(line) + "\n"
  return escapedtext

def sumstr(value):
  c = 0
  for ch in value:
    c += ord(ch) % 256
  return c

def encrypt(plaintext, key):
  # This is not a secure encryption function, it's just to prevent prying eyes
  output = ""
  key = key.lower()
  m = -1
  iv = sumstr(key)
  for n in range(len(plaintext)):
    m += 1
    if m >= len(key): m = 0
    a = ord(plaintext[n])
    b = ord(key[m])
    M, N = m + 1, n + 1
    c = N * (N-M+3)
    z = (a + (b*c) + iv) % 256
    while z < 0:
      z += 256
    iv = (iv + a + z) % 256
    output += chr(z)
  return base64.encodestring(output).strip()

def decrypt(cryptext, key):
  # This is not a secure encryption function, it's just to prevent prying eyes
  output = ""
  key = key.lower()
  if len(cryptext) > 0:
    cryptext = base64.decodestring(cryptext)

  m = -1
  iv = sumstr(key)
  for n in range(len(cryptext)):
    m += 1
    if m >= len(key): m = 0
    a = ord(cryptext[n])
    b = ord(key[m])
    M, N = m + 1, n + 1
    c = N * (N-M+3)
    z = (a - (b*c) - iv) % 256
    while z < 0:
      z += 256
    iv = (iv + a + z) % 256
    output += chr(z)
  return output.strip()

def testencryption(value,key):
  ciphertext = encrypt(value,key)
  plaintext = decrypt(ciphertext,key)
  return value == plaintext

def test():
  if not testencryption('test','test'): return 0
  if not testencryption('a long value','short'): return 0
  if not testencryption('short','a long value'): return 0
  return 1

if __name__ == '__main__':
  if test():
    print "tests passed"
  else:
    print "tests failed"

