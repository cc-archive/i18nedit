#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" PDF file parser

    This module exports the PDFFile class which provides access
    to a PDF file's object tree. PDFFile instances have a Root
    dictionary attribute which is the file's "document catalog"
    object tree.  You really need to have the PDF reference book
    at hand to understand its structure (free to download from
    Adobe.com).

    All objects in the tree are wrapped in the Object class so as
    to permit 'lazy loading'. Call the value() method on Objects
    to get the underlying pythonized object. For lists and dictionaries,
    normal [] access is implemented accordingly. Note that Name
    objects look like strings, which is generally what you want.

    All non-image filters have been implemented, and encrypted
    documents with either empty or supplied user password are
    supported.  Only revision 2 standard encryption is fully
    implemented.  External file streams are not supported.

    This module is not particualrly efficient at accessing the PDF
    document, so I wouldn't recommend using it as the basis of a
    file transformer or viewer. Instead, it is probably most useful
    as a way of accessing information about PDF documents, such as
    the TOC, or the security bits.

    References:

    [1] Adobe Systems Incorporated, 'PDF reference: Adobe portable 
        document format version 1.4', 3rd ed., Addison-Wesley, 
        Boston. December 2001.

    David Leonard, 2003. Public domain. Provided 'as is'; no warranties.
"""

__author__ = 'David Leonard, 2003'
__version__ = "1.1"

import sys, operator, exceptions, struct
import zlib, md5, codecs

class Error(exceptions.Exception):
    """All exceptions from the PDF module"""
    pass

#------------------------------------------------------------
# Streams

class ByteStream:
    """ The abstract byte stream class. Tokenisers use this.  """
    def __init__(self, dict=None):
	self.dict = dict
	self.rewind()
    def getchar(self):
	"""getchar() -> char or ''."""
	return self.read(1)
    def substream(self, start, len = None):
	"""substream(start[, len]) -> ByteStream. Create independent stream."""
	raise AbstractError
    def read(self, len):
	"""read(len) -> string. Read up to len bytes"""
	raise AbstractError
    def tell(self):
	"""tell() -> int. Current file position as byte offset."""
	raise AbstractError
    def seek(self, pos):
	"""seek(pos) -> None. Move to new stream position"""
	raise AbstractError
    def rewind(self):
	"""rewind() -> None. Reset the stream and seek to position 0"""
	self.seek(0)
    def end(self):
	"""end() -> int. byte offset after end of file or None if unknown"""
	return None

class FileByteStream(ByteStream):
    """A byte stream interface to a python file object."""
    def __init__(self, f, offset = 0, len = None):
	self.f = f
	self.offset = offset
	if len is None:
	    #-- compute the file's size by seeking to the end
	    f.seek(0, 2)
	    len = f.tell()
	self.len = len
	self.f.seek(0)
	self._physpos = 0
	ByteStream.__init__(self)
    def _read(self, physpos, datalen):
	if self._physpos != physpos:
	    self.f.seek(physpos)
	    self._physpos = physpos
	data = self.f.read(datalen)
	#print "@%d %s" % (self._physpos, repr(data))
	self._physpos += len(data)
	return data
    def read(self, bytes):
	if self.len is not None and self.pos + bytes > self.len:
	    bytes = self.len - self.pos
	data = self._read(self.pos + self.offset, bytes)
	self.pos += len(data)
	return data
    def substream(self, start, len = None):
	if start < 0 or (self.len is not None and len is not None
	  and start + len > self.len):
	    raise Error('substream exceeds parent stream bounds')
	return FileByteSubStream(self, start, len)
    def tell(self):
	return self.pos
    def seek(self, pos):
	if pos < 0 or (len is not None and pos >= len):
	    raise IOError("Invalid seek")
	self.pos = pos  #-- error occurs only on next read
    def end(self):
	return self.len
    def __repr__(self):
	if self.offset:
	    return '<FileStream %s @%d>' % (repr(self.f), self.offset)
	else:
	    return '<FileStream %s>' % repr(self.f)

class FileByteSubStream(FileByteStream):
    """A substream of a FileByteStrem. This is what is normally
       created when a 'stream' keyword is encounterred."""
    def __init__(self, parent, offset, len):
	self.parent = parent
	self.offset = parent.offset + offset
	self.len = len
	ByteStream.__init__(self)
    def _seek(self, physpos):
	self.parent._seek(physpos)
    def _read(self, pos, datalen):
	return self.parent._read(pos, datalen)
    def __repr__(self):
	return '<FileSubstream %s @%s>' % (repr(self.parent), repr(self.offset))

#class HTTPByteStream(ByteStream):
#    """(Unimplemented) HTTP byte stream.
#       This class should fetch reasonable chunks of the PDF URL 
#       on demand, buffering the chunks."""
#    pass

class FilteredByteStream(ByteStream):
    """ Abstract class for stream that applies self.filter() 
	to the data from an underlying stream. seek() is not available,
	but rewind is: it resets the filter and the underlying stream. """
    chunksize = 1024 
    def __init__(self, under, dict={}):
	self._under = under
	self._remain = ''
	ByteStream.__init__(self, dict)
    def read(self, datalen):
	while len(self._remain) < datalen:
	    #-- filter chunks until we get the data len we wanted
	    data = self._under.read(self.chunksize)
	    self._remain += self.filter(data)
	    if data == '':
		#-- if the underlying stream was at EOF, then the
		#   filter would have been called with data=''
		#   and so should also be finished.
		datalen = len(self._remain)
	result, self._remain = self._remain[:datalen], self._remain[datalen:]
	self._pos += len(result)
	return result
    def tell(self):
	return self._pos
    def rewind(self):
	self._pos = 0
	self._under.rewind()
    def seek(self, pos):
	if pos != 0:
	    raise Error("Cannot seek() on a filtered stream")
    def end(self):
	raise Error("Cannot determine end() of a filtered stream")
    def substream(self):
	raise Error("Cannot create a substream() on a filtered stream")
    def filter(self, data):
	""" filter(string) -> string
	    The filter method can return as much data as it can. 
	    It is usually fed data in chunks of up to 1024 bytes.
	    It will be given data='' when underlying stream is exhausted.
	    It should return '' when no more data can be generated.
	"""
	raise AbstractError

#------------------------------------------------------------
# PDF tokeniser

class Tokeniser:
    """PDF tokenizer class. 

       This class reads a byte stream and breaks it into tokens.
       get_token() should be called to get the next token on the stream.
       - if get_token() returns '/' then get_name() should be called to get
	 the rest of the name.
       - if get_token() returns '(' then get_string() should be called to get
	 the rest of the string.
       - if get_token() returns '<' then get_hexstring() should be called to
	 get the rest of the (hex) string.
       - if get_token() returns a 'stream' keyword, then get_stream() should 
         be called next - it will return a substream object.
       - otherwise get_token() returns keywords and ignores comments/whitespace

       get_header() parses the header comment of the PDF file and should
       be called first if at all

       get_xref() is useful for finding byte offsets of the xref table
         after an 'xref' keyword.

       """

    Whitespace = '\x00\x09\x0a\x0c\x0d\x20'
    Delimiters = '()<>[]{}/%'
    NonRegular = Whitespace + Delimiters
    EOF = ''
    EscapeMap = { 'n':'\x0a', 'r':'\x0d', 't':'\x0a', 'b':'\x08',
		  'f':'\x0c' }
    OctalDigits = "01234567"

    def __init__(self, stream):
	self.stream = stream
	self.version = "1.4"
	self.seek(0)

    def seek(self, pos):
	"""Seek and prime the lookahead"""
	self.stream.seek(pos)
	self.nextch = self.stream.getchar()	#-- prime the nextch lookahead

    def get_state(self):
	"""Return current tokeniser state"""
	return self.stream.tell(), self.nextch
    def set_state(self, (pos, nextch)):
	"""Restore tokeniser state"""
	self.stream.seek(pos)
	self.nextch = nextch

    def get_header(self):
	"""get_header() -> version or None
	   Read the %PDF-x.y first line and return 'x.y'.
	   Returns None if the header line was not found.
	"""
	#-- consume the '%PDF-' prefix
	if self.nextch != '%':
		return None
	for k in '%PDF-':
	    if self.nextch != k:
		#-- bad character - skip to end of comment
	        while self.nextch not in ('', '\n', '\r'):
		    self.nextch = self.stream.getchar()
		return None
	    self.nextch = self.stream.getchar()
	version = ''
	#-- pull out the version number following '%PDF-'
	while 1:
	    if self.nextch == '' or self.nextch in self.Whitespace:
		break
	    version = version + self.nextch
	    self.nextch = self.stream.getchar()
	#-- skip to the next newline character
        while not self.nextch in ('', '\n', '\r'):
	    self.nextch = self.stream.getchar()
	self.version = version
	return version

    def get_xref(self):
	"""get_xref() -> (startid, nentries, offset)
	   Special access for reading the integers after an xref keyword.
	   returns the two integers and then the byte position of the first
	   20-character entry. seek position is indeterminate afterwards"""
	startid = self.get_token()
	nentries = self.get_token()
	#-- skip whitespace
	while 1:
	    if self.nextch == '': raise EOFError
	    if self.nextch not in self.Whitespace: break
	    self.nextch = self.stream.getchar()
	firstpos = self.stream.tell() - 1
	#print "*** FIRSTPOS", firstpos
	#-- XXX some stupid PDF writers write the first line
	#   incorrectly. (they make it 19 bytes long instead of 20)
	#   so we read 20 bytes to check on this
	testline = self.nextch + self.stream.read(19)
	if testline[19].isdigit():
	    firstpos -= 1
	return int(startid), int(nentries), firstpos

    def get_token(self):
	"""get_token() -> string
	   Return next delimiter or token composed of regular characters,
	   or EOF.  Comments and whitespace are ignored.
	   Tokens returned are:
		( < [ ] { } / << >> regularseq
	"""
	while 1:
	    c, self.nextch = self.nextch, self.stream.getchar()
	    if c == '%':
		#-- recognise %%EOF
		for k in "%EOF":
		    if self.nextch != '%':
			break
		    self.nextch = self.stream.getchar()
		else:
		    return '%%EOF'
		#-- skip comments
		while 1:
		    c, self.nextch = self.nextch, self.stream.getchar()
		    if c in ('', '\r', '\n'):
			break
	    if c == '':
		return self.EOF
	    #-- skip whitespace
	    if c not in self.Whitespace:
		break
	if c in self.Delimiters:
	    if c == self.nextch and c in "<>":
		#-- recognise << and >> as separate tokens
		self.nextch = self.stream.getchar()
		return c+c
	    return c
	token = c
	while 1:
	    #-- return a regular sequence
	    n = self.nextch
	    if n == '' or n in self.NonRegular:
		return token
	    token += self.nextch
	    self.nextch = self.stream.getchar()

    def get_string(self):
	"""get_string() -> string
	   Return the expanded string after having read the '(',
	   consuming the trailing ')' as well.
	   Will raise EOFError on EOF."""
	parens = 0
	s = ''
	while 1:
	    c, self.nextch = self.nextch, self.stream.getchar()
	    if c == '':
		raise EOFError
	    elif c == ')':
		if parens == 0:
		    return s
		s += c
		parens -= 1
	    elif c == '(':
		s += c
		parens += 1
	    elif c == '\\':
		#-- interpret backslash-escaped chars
		c, self.nextch = self.nextch, self.stream.getchar()
		if c == '':
		    raise EOFError
		elif c in self.OctalDigits:
		    #-- interpret \ddd octal escapes
		    if self.nextch in self.OctalDigits:
			c,self.nextch = c+self.nextch, self.stream.getchar()
		        if self.nextch in self.OctalDigits:
			    c,self.nextch = c+self.nextch, self.stream.getchar()
		    s += chr(int(c, 8))
		elif c == '\r':
		    #-- escaped DOS/Mac newline
		    if self.nextch == '\n':
			self.nextch = self.stream.getchar()
		elif c == '\n':
		    #-- escaped Unix newline
		    pass
		else:
		    s += self.EscapeMap.get(c) or c
	    elif c == '\r':
		#-- convert DOS/Mac newlines into Unix newlines \n
		if self.nextch == '\n':
		    self.nextch = self.stream.getchar()
		s += '\n'
	    else:
		s += c

    def get_hexstring(self):
	"""get_hexstring() -> string
	   Return the expanded hex string after reading an '<',
	   consuming the trailing '>' as well. Raises EOFError on EOF.
	   Raises ValueError if the string is invalid"""
	s = ''
	while 1:
	    while 1:
		#-- skip whitespace
		c1, self.nextch = self.nextch, self.stream.getchar()
		if c1 == '':
		    raise EOFError
		if c1 not in self.Whitespace:
		    break
	    if c1 == '>':
		return s
	    while 1:
		#-- skip whitespace
		c2, self.nextch = self.nextch, self.stream.getchar()
		if c2 == '':
		    raise EOFError
		if c2 not in self.Whitespace:
		    break
	    if c2 == '>':
		#-- missing final digit is assumed to be '0'
		return s + chr(int(c1+'0', 16))
	    s += chr(int(c1 + c2, 16))

    def get_name(self):
	"""get_name() -> string
	   Return the name immediately following a / token. """
	s = ''
	while 1:
	    if self.nextch == '' or self.nextch in self.NonRegular:
		break
	    if self.nextch == '#' and self.version > "1.1":
		#-- expand #xx character escapes in names (>= PDF1.2)
		c1 = self.stream.getchar()
		if c1 == '': raise EOFError
		c2 = self.stream.getchar()
		if c2 == '': raise EOFError
		s += chr(int(c1+c2, 16))
	    else:
		s += self.nextch
	    self.nextch = self.stream.getchar()
	return s

    def get_stream(self, length_hint = None, search_for_endstream = False):
	"""get_stream([length_hint = None [, search = False]) -> substream
	    Return a substream object, for the stream immediately
	    following the 'stream' keyword. Parser should expect to
	    read an endstream keyword after this if length_hint is given.
	    If search is True, then the endstream keyword is scanned for.
	    Otherwise if length_hint is None, then the substream is given
	    an unbounded length."""
	if self.nextch == '\r':
	    self.nextch = self.stream.getchar()
	if self.nextch == '':
	    raise EOFError
	if self.nextch != '\n':
	    raise Error("stream keyword not followed by \\n")
	pos = self.stream.tell()
	if search_for_endstream:
	    #-- search, in 8kB read chunks, for the endstream keyword
	    while 1:
		datapos = self.stream.tell()
		data = self.stream.read(8192)
		if data == '':
		    raise Error("missing endstream")
		e = data.find("endstream")
		if e != -1: break
	    endpos = datapos + e
	    length_hint = endpos - pos
	substream = self.stream.substream(pos, length_hint)
	if length_hint is not None:
	    self.stream.seek(pos + length_hint)
	return substream

#------------------------------------------------------------
# Objects

class Object:
    """ Abstract Object class for wrapping PDF file objects """

    #-- this variable makes __repr__ methods recurse through
    #   their values.. not recommended since it usually blows
    #   the stack as some objects have cyclic references.
    repr_expand = False

    def __init__(self):
	self._id = None
    def set_id(self, id, gen):
	self._id = (id,gen)
    def value(self):
	raise Error("No value for this object")
    def __repr__(self):
	raise AbstractError
    def is_dict(self):
	return False
    def is_int(self):
	return False
    def is_string(self):
	return False
    def is_stream(self):
	return False
    def is_array(self):
	return False
    def id(self):
	return self._id
    def __cmp__(self, other):
	if isinstance(other, Object):
	    if self._id and other._id == self._id:
	        return 1
	    return cmp(self.value(), other.value())
	else:
	    return cmp(self.value(), id(other))
    def __nonzero__(self):
	if self.value(): return 1
	else: return 0

class LiteralObject(Object):
    """ Generic objects that have python-equivalent values """
    def __init__(self, value):
	self._value = value
	Object.__init__(self)
    def value(self):
	return self._value
    def __str__(self):
	return str(self._value)
    def __unicode__(self):
	return unicode(self._value)
    def __repr__(self):
	return '<' + repr(self._value) + '>'
    def is_int(self):
	return isinstance(self._value, int)
    def is_dict(self):
	return isinstance(self._value, dict)
    def __int__(self):
	return int(self.value())
    def __float__(self):
	return float(self.value())

class NullObject(Object):
    """ The special 'null' class """
    def value(self):
	return None
    def __repr__(self):
	return '<null>'
    def __nonzero__(self):
	return 0

NullObj = NullObject()

class StringObject(LiteralObject):
    """ Strings """
    def __init__(self, value):
	#-- 3.8.1: if the string starts with U+FEFF then treat as unicode
	if value.startswith('\xfe\ff') or value.startswith('\xff\xfe'):
		value = value.decode('utf16')
	LiteralObject.__init__(self, value)
    def is_string(self):
	return True

class StreamObject(Object):
    """ Streams. Use str() or .value() to access the stream content. """
    def __init__(self, stream, dict={}):
	Object.__init__(self)
	self._content = None
	self.dict = dict
	self._stream = stream
    def value(self):
	return self._stream
    def __str__(self):
	"""Read and cache the whole stream contents and treat as string"""
	if self._content is None:
	    self._content = ''
	    self._stream.rewind()
	    while 1:
		data = self._stream.read(8192)
		if data == '': break
		self._content += data
	return self._content
    def is_string(self):
	return True
    def is_stream(self):
	return True
    def __repr__(self):
	if self.repr_expand:
	    return '<Stream %s>' % repr(str(self))
	else:
	    return '<Stream %s>' % repr(self._stream)

class ArrayObject(LiteralObject):
    """ Heterogeneous arrays """
    def __getitem__(self, index):
	return self._value[index]
    def __len__(self):
	return len(self._value)
    def is_array(self):
	return True

class DictObject(LiteralObject):
    """ Dictionarys. All keys must be strings. """
    def __getitem__(self, key):
	"""Return NullObj for non-existent keys"""
	return self.get(key)
    def get(self, key):
	"""Return NullObj for non-existent keys"""
	v = self._value.get(key)
	if v is None: return NullObj
	else:         return v
    def has_key(self, key):
	return self._value.has_key(key)
    def items(self):
	return self._value.items()

class Boolean(Object):
    """ The two Boolean objects """
    def __init__(self, value):
	self._value = bool(value)
	Object.__init__(self)
    def value(self):
	return self._value
    def __repr__(self):
	if self._value: return '<True>'
	else:           return '<False>'
    def __unicode__(self):
	if self._value: return u'true'
	else:           return u'false'
    def __str__(self):
	if self._value: return 'true'
	else:           return 'false'
    def __int__(self):
	return self._value

TrueObj = Boolean(True)
FalseObj = Boolean(False)

class IndirectObject(Object):
    """ Indirect object. 
	This is a reference to some other object in the file.
	Call value() to get to the real object, or
	use int(), str(), float(), or [] to automatically dereference."""
    def __init__(self, key, deref):
	Object.__init__(self)
	self._deref = deref
	self._key = key
	self._id = key
    def value(self):
	"""Returns None if the value has not yet been seen"""
	return self._deref(self._key)
    def __repr__(self):
	if Object.repr_expand:
	    return repr(self.value())
	return '<%d %d R>' % self._key
    def __nonzero__(self):
	return 1			# XXX

    def __getitem__(self, key):
	return self.value()[key]
    def __int__(self):
	return int(self.value())
    def __str__(self):
	return str(self.value())
    def __unicode__(self):
	return unicode(self.value())
    def __float__(self):
	return float(self.value())
    def get(self, key):
	return self.value().get(key)

class Name(Object):
    """ A '/Name' object - act as labels in the PDF file """
    def __init__(self, name):
	if type(name) is not unicode:
	    name = name.decode('utf8') #-- 3.2.4 recommends UTF8 interpret
	self._name = name
	Object.__init__(self)
    def value(self):
	return self._name
    def __repr__(self):
	if type(self._name) is unicode:
	    return '/' + repr(self._name)[2:-1]	# skip the "u'" leader
	else:
	    return '/' + repr(self._name)[1:-1]	# skip the "'" leader
    def __str__(self):
	return str(self._name)
    def __unicode__(self):
	return self._name

class Mark(Object):
    """ Various kinds of marks used to delimit things pushed
	on the stack while parsing the PDF file in a postscript
	interpreter-like way. These are temporary and should
	never be encountered outside this module. """
    def __init__(self, type):
	self._type = type
	Object.__init__(self)
    def __repr__(self):
	return '<Mark:%s>' % self._type

DictMark = Mark('dict')		# <<
ArrayMark = Mark('array')	# [
ObjMark = Mark('obj')		# obj
InUseMark = Mark('in-use')	# n
FreeMark = Mark('free')		# f
TrailerMark = Mark('trailer')	# trailer

class Date(Object):
    """ PDF dates from section 3.8.2.
	If no timezone is specified, the date is treated as UTC,
	and the 'approximate' attribute is set to True. """
    def __init__(self, s, ref=None):
	if not s.startswith('D:'):
	    raise Error('Bad date format %s' % repr(s))
	mon,day,hour,min,sec,o,tzh,thm = 1,1,0,0,0,None,0,0
	year = int(s[2:6])
	if len(s) >= 8:
	 mon = int(s[6:8])
	 if len(s) >= 10:
	  day = int(s[8:10])
	  if len(s) >= 12:
	   hour = int(s[10:12])
	   if len(s) >= 14:
	    min = int(s[12:14])
	    if len(s) >= 16:
	     sec = int(s[14:16])
	     if len(s) >= 17:
	      o = s[16]
	      if o not in "Z-+": raise Error('Bad format %s' % repr(s))
	      if len(s) >= 20:
	       if o == 'Z': raise Error('Bad format %s' % repr(s))
	       tzh = int(s[17:19])
	       if s[19] != "'": raise Error('Bad format %s' % repr(s))
	       if len(s) >= 23:
	        tzm = int(s[20:22])
	        if s[22] != "'": raise Error('Bad format %s' % repr(s))
	if o == '-': tzh,tzm = -tzh,-tzm
	t = time.mktime((year,mon,day,hour,min,sec,0,0,0)) - time.timezone
	if o in "-+":
	    t += tzh * 3600 + tzm * 60
	self.approximate = o is None
	self._t = t
    def value(self):
	return self._t
    def __repr__(self):
	return '<Date %s>' % str(self)
    def __str__(self):
	year,mon,day,hour,min,sec,_,_,_ = time.gmtime(self._t)
	if self.approximate: z = ''
	else:                z = 'Z'
	return 'D:%04d%02d%02d%02d%02d%02d%s' % (year,mon,day,hour,min,sec,z)
    def __int__(self):
	return self.value()

#------------------------------------------------------------
# Cross-reference table

class XREF:
    """A caching XREF table.
       Each instance represents an xref section in the PDF file,
       used for translating object IDs into file byte positions,
       rather than having to pre-parse the whole file."""

    def __init__(self, tok, startid, nentries, offset):
	self.tok = tok
	self.startid = startid
	self.nentries = nentries
	self.offset = offset
	self.cache = {}

    def lookup(self, id):
	"""lookup(id) -> (offset, generation, 'n'|'f') or None
	   Returns an entry in the XREF table, or None if doesnt exist.
	"""
	if self.cache.has_key(id):
	    return self.cache[id]
	if id < self.startid or id >= self.startid + self.nentries:
	    return None
	state = self.tok.get_state()
	self.tok.stream.seek(self.offset + (id - self.startid) * 20)
	data = self.tok.stream.read(20)
	self.tok.set_state(state)
	ret = int(data[:10],10), int(data[11:16],10), data[17]
	#print "XREF",id,"->",repr(data),"->",ret
	self.cache[id] = ret
	return ret

    def __repr__(self):
	return '<XREF %d-%d>' % (self.startid, self.startid + self.nentries-1)

#------------------------------------------------------------
# Security and encryption

class SecurityHandler:
    """ Abstract class for handling encryption and security 
	operations on the file.
	The properties 'printable', 'modify', and 'copy'
	are set to values reflecting the document security permissions.
	"""
    def __init__(self, encrypt_dict=None, trailers=None, password=''):
	P = int(encrypt_dict['P'])
	printable = []
	if P & (1<<3): printable.append('low-quality')
	if P & (1<<12): printable.append('high-quality')
	self.printable = tuple(printable)
	modify = []
	if P & (1<<9): modify.append('forms')
	if P & (1<<6): modify.append('annotations')
	if P & (1<<11): modify.append('assembly')
	if P & (1<<4): modify.append('misc')
	self.modify = tuple(modify)
	copy = []
	if P & (1<<5): copy.extend(["text","graphics"])
	if P & (1<<10): copy.append("accessible")
	self.copy = tuple(copy)
    def decrypt_string(self, id, s):
	raise AbstractError
    def decrypt_stream(self, id, s):
	raise AbstractError
    def __repr__(self):
	return '<%s: %s>' % (
		self.__class__.__name__,
		self._authinfo())
    def _authinfo(self):
	return 'printable:(%s) modify:(%s) copy:(%s)' % (
		','.join(self.printable),
		','.join(self.modify),
		','.join(self.copy))

class NullSecurityHandler(SecurityHandler):
    """ Default, not-encrypted handler. Permits everything
	and treats strings and streams as plain text. """
    def __init__(self, encrypt_dict=None, trailers=None, password=''):
	SecurityHandler.__init__(self, {'P': -4})
    def decrypt_string(self, id, s):
	return s
    def decrypt_stream(self, id, s):
	return s

def hexstr(s):
    """hexstr(string) -> nice-string
       Handy utility function for displaying hex strings nicely"""
    return ":".join(map(lambda c:'%02x'%ord(c), s))

class StandardSecurityHandler(SecurityHandler):
    """ Standard PDF encryption handler """
    PasswordPad = "\x28\xBF\x4E\x5E\x4E\x75\x8A\x41\x64\x00\x4E" + \
		  "\x56\xFF\xFA\x01\x08\x2E\x2E\x00\xB6\xD0\x68" + \
		  "\x3E\x80\x2F\x0C\xA9\xFE\x64\x53\x69\x7A"
    def __init__(self, encrypt, trailers, password=''):
	SecurityHandler.__init__(self,encrypt,trailers,password)
	self.V = int(encrypt['V'])	#-- key flags
	self.R = int(encrypt['R'])	#-- revision
	self.U = str(encrypt['U'])	#-- user crypt
	self.O = str(encrypt['O'])	#-- owner crypt
	self.P = int(encrypt['P'])	#-- permission flags
	if self.V < 1 or self.V >= 3:
	    raise Error('Standard encryption: V flag unknown %d' % self.V)
	if (self.V == 2 or self.V == 3) and encrypt.has_key('Length'):
	    self.Length = int(encrypt['Length']) / 8  # bit length
	else:
	    self.Length = 40 / 8
	self.id1 = str(trailers[0]['ID'][0])

	#print	"Standard Encryption"
	#print	"	V = %d" % self.V
	#print	"	R = %d" % self.R
	#print	"	U = %s" % hexstr(self.U)
	#print	"	O = %s" % hexstr(self.O)
	#print	"	P = %d (%x)" % (self.P, self.P)
	#print	"	Length = %d (%d bits)" % (self.Length, self.Length * 8)

	self._keycache = {}
	self._key = self.compute_encryption_key(password)
	if self._key is None:
	    raise Error('PDF file encrypted or password mismatch')

    def compute_encryption_key(self, password = ""):
	"""Algorithm 3.2. Compute the key used to decode strings
	   and streams. Returns None if the user password does not
	   pass the simple password test."""

	password = (password + self.PasswordPad)[:32]
	m = md5.md5()
	m.update(password)
	m.update(self.O)
	P = struct.pack("<L", self.P)
	m.update(P)
	m.update(self.id1)
	x = m.digest()
	if self.R == 3:
	    for i in range(50):
		x = md5.md5(x).digest()
        key = x[:self.Length]

	#-- if this key is right, then ecrypting the pad string will
	#   yield the U value.
	Ucheck = RC4(key).crypt(self.PasswordPad)
	if Ucheck != self.U:
	    # try skipping steps 3 4 and 5.
	    key = md5.md5(password).digest()[:5]
	    Ucheck = RC4(key).crypt(self.PasswordPad)
	    if Ucheck != self.U:
		return None
	return key

    def make_rc4key(self, id):
	"""Return the RC4 key for an object given its id/generation"""
	key = self._keycache.get(id)
	if key is None:
            k = self._key + struct.pack("<L", id[0])[:3] + \
			    struct.pack("<L", id[1])[:2]
	    m = md5.md5()
	    m.update(k)
	    key = m.digest()[:len(self._key)+5]
	    #print "* rc4key", `id`, "->", hexstr(k), "->", hexstr(key)
	    self._keycache[id] = key
	return key
    def decrypt_string(self, id, s):
	return RC4(self.make_rc4key(id)).crypt(s)
    def decrypt_stream(self, id, s):
	return RC4DecryptedByteStream(s, self.make_rc4key(id))

    def __repr__(self):
	return '<%s: %s key=%s>' % (
		self.__class__.__name__,
		self._authinfo(),
		hexstr(self._key))

class RC4DecryptedByteStream(FilteredByteStream):
    """ A stream filtered through the RC4 cipher """
    def __init__(self, under, key):
	self._key = key
	FilteredByteStream.__init__(self, under)
    def filter(self, data):
	return self._rc4.crypt(data)
    def rewind(self):
	FilteredByteStream.rewind(self)
	self._rc4 = RC4(self._key)

class RC4:
    """RC4 symmetric cipher (slow!)"""
    def __init__(self, key):
	"""Initialise the symmetric cipher with a non-empty key"""
	perm = range(256)
	j = 0
	keylen = len(key)
	key = struct.unpack("%dB" % keylen, key)
	for i in range(256):
	    j = (j + perm[i] + key[i % keylen]) % 256
	    perm[i],perm[j] = perm[j],perm[i]
	self.perm = perm
	self.state = 0, 0
	#print "after init, perm=", perm
    def crypt(self, data):
	"""crypt(string) -> string
	   Decrypt/Encrypt string"""
	perm = self.perm
	index1,index2 = self.state
	datalen = len(data)
	fmt = '%dB' % datalen
	data = struct.unpack(fmt, data)
	res = [fmt]
	for c in data:
	    index1 = (index1 + 1) % 256
	    index2 = (index2 + perm[index1]) % 256
	    perm[index1],perm[index2] = perm[index2],perm[index1]
	    j = perm[index1] + perm[index2]
	    res.append(c ^ perm[j % 256])
	#print "res =",res
	self.state = index1,index2 
	return apply(struct.pack, tuple(res))
    def __repr__(self):
	return '<RC4 %d %d>' % self.state

SecurityHandlerMap = {
	None:		NullSecurityHandler,
	'Standard': 	StandardSecurityHandler,
}

#------------------------------------------------------------
# PDF File parser

class PDFFile:
    """A PDF file parser/accessor.
       This class provides on-demand parsing of the PDF object
       content.
    """

    def __init__(self):
	self._reset()

    def _reset(self):
	self.tokeniser = None
	self.stack = []
	self.refdict = {}
	self.xrefs = []
        self.Security = NullSecurityHandler()
	self.Root = NullObj
	self.Trailers = []
	self.ID = NullObj

    def load_file(self, filename, password=''):
	self._load(Tokeniser(FileByteStream(file(filename,'rb'))), password)

    def _load(self, tokr, password=''):
	self._reset()
	self.tokeniser = tokr
	self.version = tokr.get_header()
	if self.version is None:
	    sys.stderr.write("*** No header found - file probably not PDF\n")

	#-- read the last block of the file and find %%EOF
	filesize = tokr.stream.end()
	lastblocksize = min(filesize, 2048)
	tokr.stream.seek(filesize - lastblocksize)
	lastblock = tokr.stream.read(lastblocksize)
	p = lastblock.rfind('%%EOF')
	if p == -1:
	    raise Error('cannot find %%EOF - truncated file?')

	#-- find the startxref just before %%EOF
	p = lastblock.rfind('startxref', 0, p)
	if p == -1:
	    raise Error('cannot find startxref')
	p += filesize - lastblocksize
	tokr.seek(p)

	#-- read the integer that follows startxref
	t = self.read_token()
	if t != 'startxref': raise Error('exepected startxref at '+`t`)
	p = self.read_token().value()

	while 1:
	    #-- now seek to that integer and read an xref table
	    tokr.seek(p)
	    t = self.read_token()
	    if t != 'xref': raise Error('expected xref at '+`t`)
	    self.exec_xref()

	    #-- a trailer dictionary should follow the xref table
	    trailer = self.read_trailer()
	    self.Trailers.append(trailer)

	    #-- If the trailer has a Prev entry, then we recurse
	    if not trailer.value().has_key('Prev'): break
	    p = trailer['Prev'].value()

	self.Root = self.Trailers[0]['Root']
	self.Info = self.Trailers[0]['Info']
	self.ID = self.Trailers[0]['ID']

	#-- instantiate a security handler.
	Encrypt = self.Trailers[0].get('Encrypt')
	if Encrypt is not NullObj:
	    handler = str(Encrypt['Filter'])
	else:
	    handler = None
	if not SecurityHandlerMap.has_key(handler):
	    Error("unknown security handler /%s" % handler)
	self.Security = SecurityHandlerMap[handler](Encrypt,
		self.Trailers, password)
		
    def read_object(self, id=None):
	"""Expects to read a tagged object up to endobj"""
	idtok = self.read_token()
	gentok = self.read_token()
	tok = self.read_token()
	if tok != 'obj':
		raise Error('expected obj')
	oldstack, self.stack = self.stack, [idtok, gentok]
	try:
	    self.exec_obj()
	    if id is not None:
	      if idtok.value() != id[0]:
		raise Error('expected object id %d not %s' % 
			(id[0], repr(idtok)))
	      if gentok.value() != id[1]:
		raise Error('expected object generation %d not %s' % 
			(id[1], repr(gentok)))
	    #-- loop, reading tokens until the endobj consumes everything
	    while self.stack:
		tok = self.read_token(id)
		if tok is None: 
		    raise Error('EOF before endobj?')
		self.exec_token(tok)
	finally:
	    self.stack = oldstack	#-- restore the stack saved previously

    def read_trailer(self):
	"""read_trailer() -> dictionary
	   Read and return the trailer dictionary."""
	t = self.read_token()
	if t != 'trailer': raise Error('expected trailer at '+`t`)
	oldstack, self.stack = self.stack, []
	try:
	    while 1:
		tok = self.read_token()
		if tok == 'startxref': break
		if tok is None: 
		    raise Error('EOF before startxref?')
		self.exec_token(tok)
	    if len(self.stack) != 1:
		raise Error('wrong number of objects before startxref')
	    dict = self.stack[0]
	finally:
	    self.stack = oldstack
	return dict

    def read_token(self, id=None):
	"""Reads some tokens from the stream and returns either
	   an Object, a string keyword or None for EOF."""
	tok = self.tokeniser.get_token()
	if tok == '/':
	    return Name(self.tokeniser.get_name())
	elif tok == '(':
	    s = self.tokeniser.get_string()
	    return StringObject(self.Security.decrypt_string(id, s))
	elif tok == '<':
	    s = self.tokeniser.get_hexstring()
	    return StringObject(self.Security.decrypt_string(id, s))
	elif tok == 'stream':
	    #-- extract the Length field of last dictionary
	    if not self.stack[-1].is_dict():
		raise Error('stream follows non-dictionary (%s)' %
			repr(self.stack[-1]))
	    length_hint = self.stack[-1].get('Length')
	    if not length_hint:
		s = self.tokeniser.get_stream(None, True)
	    else:
		s = self.tokeniser.get_stream(int(length_hint), False)
	    return StreamObject(self.Security.decrypt_stream(id, s))
	elif tok is self.tokeniser.EOF:
	    return None
	else:
	    if tok[0] in '.-+0123456789':
		#-- looks like a number!
		try: # integer
		    return LiteralObject(int(tok, 10))
		except ValueError: pass
		try: # real
		    return LiteralObject(float(tok))
		except ValueError: pass
	    return tok

    def exec_token(self, tok):
	""" Execute a token """
	if isinstance(tok, Object):
	    self.stack.append(tok)
	else:
	    action = self.execmap.get(tok)
	    if action is None:
	       raise Error('unknown token %s' % tok)
	    elif isinstance(action, Object):
		self.stack.append(action)
	    else:
		action(self)

    def exec_enddict(self):
	""" called when executing '>>' """
	dict = {}
	while 1:
	    s = self.stack.pop()
	    if s is DictMark:
		break
	    n = self.stack.pop()
	    if not isinstance(n, Name):
		raise Error('Non-name used for dictionary key')
	    dict[n._name] = s
	self.stack.append(DictObject(dict))

    def exec_endarray(self):
	""" called when executing ']' """
	array = []
	while 1:
	    s = self.stack.pop()
	    if s is ArrayMark:
		break
	    array.insert(0, s)
	self.stack.append(ArrayObject(array))

    def exec_obj(self):
	""" called when executing 'obj' """
	if not self.stack[-1].is_int() or not self.stack[-2].is_int():
	    raise Error('obj must be preceeded by two integers')
	self.stack.append(ObjMark)

    def exec_endobj(self):
	""" called when executing 'endobj' """
	obj = self.stack.pop()
	mark = self.stack.pop()
	if mark is not ObjMark:
		raise Error('too many objects after "obj"? %s %s %s'
			% (repr(self.stack), repr(obj), repr(mark)))
	generation = self.stack.pop()
	id = self.stack.pop()
	key = (id.value(), generation.value())
	obj.set_id(key[0], key[1])
	self.refdict[key] = obj

    def exec_R(self):
	""" called when executing 'R' - pushes an indirect R object """
	generation = self.stack.pop()
	id = self.stack.pop()
	if not generation.is_int() or not id.is_int():
	   raise Error('expected two integers before R but got %s %s' % 
			(repr(id), repr(generation)))
	self.stack.append(IndirectObject((id.value(), generation.value()),
		self.deref_obj))

    def deref_obj(self, key):
	""" called when value() method called on an R object.
	    It is also useful when debugging a PDF file, to be
	    able to pull out an object by its (id,gen) key.
	    Returns NullObj if the object is not in the file."""
	if self.refdict.has_key(key):
	    return self.refdict[key]
	for xref in self.xrefs:
	    v = xref.lookup(key[0])
	    if v is None: continue
	    if v[1] == key[1] and v[2] == 'n':
		save_state = self.tokeniser.get_state()
		self.tokeniser.seek(v[0])
		self.read_object(key)
		#-- by this time, exec_endobj() has been called
		self.tokeniser.set_state(save_state)
		return self.refdict[key]
	self.refdict[key] = NullObj
	return NullObj

    def exec_xref(self):
	"""Called when xref is encountered. Also skips the table."""
	(startid, nentries, offset) = self.tokeniser.get_xref()
	#-- seek to the supposed whitespace at the end of the index
	self.tokeniser.seek(offset + 20 * nentries - 2)
	self.xrefs.insert(0, XREF(self.tokeniser, startid, nentries, offset))

    def exec_endstream(self):
	"""Called when we have on the stack a dictionary and a stream"""
	stream = self.stack.pop().value()
	dict = self.stack.pop()
	if not dict.is_dict():
	    raise Error('Stream not preceeded by a dictionary')
	#print "endstream: dict is", repr(dict)
	filter = dict.get('Filter')
	if filter:
	  if not filter.is_array():
	    filter = [filter]
	  for f in filter:
	    f = str(f)
	    if Filtermap.has_key(f):
		filtclass = Filtermap.get(str(f))
		if filtclass:
		    stream = filtclass(stream, dict)
	    else:
		raise UnknownFilterError("/%s" % f)
	stream = StreamObject(stream, dict=dict)
	self.stack.append(stream)

    def PrettyPrint(self, object, indent=0, out=sys.stdout, seen={}):
	indent = indent % 80
	id = object.id()
        if id is not None:
	    if seen.has_key(id): 
		out.write('%d %d R' % id)
		return
	    seen[id] = object
	pp = self.PrettyPrint
	#out.write('*%s*' % object.__class__.__name__)
	if isinstance(object, IndirectObject):
	    pp(object.value(), indent, out)
	elif isinstance(object, DictObject):
	    l = '<< '
	    for k,v in object.items():
		out.write(l)
		keyname = str(k)
		out.write(keyname + ' ')
		pp(v, indent + 3 + len(keyname) + 1, out)
		l = '\n' + ' '*(indent+3)
	    out.write(' >>')
	elif isinstance(object, ArrayObject):
	    l = '[ '
	    for e in object.value():
	        out.write(l)
		pp(e, indent+2, out)
		l = '\n' + ' '*(indent+2)
	    out.write(' ]')
	elif isinstance(object, Name):
	    out.write('/'+str(object))
	elif isinstance(object, StringObject):
	    s = str(object)
	    s = repr(s)[1:-1].\
		replace('(',r'\(').\
		replace(')',r'\)')
	    out.write('('+s+')')
	elif isinstance(object, StreamObject):
	    s = str(object)
	    out.write('stream\n')
	    out.write(s)
	    out.write('\nendstream')
	else:
	    out.write(str(object))
	if indent == 0:
	    out.write('\n')
	if id is not None:
	    del seen[id]

    #-- execution map: called from exec()
    execmap = {
	'true':		TrueObj,
	'false':	FalseObj,
	'null':		NullObj,
	'<<':		DictMark,
	'[':		ArrayMark,
	'obj':		exec_obj,
	'endobj':	exec_endobj,
	'>>':		exec_enddict,
	']':		exec_endarray,
	'R':		exec_R,
	'n':		InUseMark,
	'f':		FreeMark,
	'trailer':	TrailerMark,
	'xref':		exec_xref,
	'endstream':	exec_endstream,
    }

#------------------------------------------------------------
# filters

class FlateDecodeFilter(FilteredByteStream):
    def __init__(self, under, dict={}):
	FilteredByteStream.__init__(self, under)
    def rewind(self):
	FilteredByteStream.rewind(self)
	self._d = zlib.decompressobj()
    def filter(self, data):
	if self._d is None:
	    return ''
	#print "decompressing %d bytes: %s" % (len(data), repr(data))
	if data == '':
	    ret = self._d.flush()
	    self._d = None
	    return ret
	return self._d.decompress(data)

class ASCII85Decoder:
    """ This class decodes ASCII85 strings using the feed interface.
	It is not the filter. See below for the actual filter. """

    def __init__(self):
	self._out = []
	self._ateod = 0
	self._buf = []

    def feed(self, data):
	"""Accept some Base85 data and return the data parsed so far.
	   Feed an empty string to force end of data."""
	if self._ateod:
	    return ''
	if data == '':
	    self._ateod = 1
	    self._swallow()
	else:
	    for d in data:
		if d in Tokeniser.Whitespace:
		    continue
		elif d == '~':
		    self._ateod = 1
		    self._swallow()
		    break
		else:
		    self._chew(d)
	result = "".join(self._out)
	self._out = []
	return result

    def _chew(self, c):
	"""Accept a non-whitespace character"""
	if c == 'z' and not self._buf:
	    self._buf = [0,0,0,0,0]
	    self._swallow()
	elif not '!' <= c <= 'u':
	    raise Error('Base85Decode: bad character %s' % repr(c))
	else:
	    self._buf.append(ord(c)-33)
	    if len(self._buf) == 5:
	        self._swallow()
    def _swallow(self):
	"""Convert between 2 and 5 base 85 digits in self._buf
	   into chars and append them on to self._out"""
	buflen = len(self._buf)
	if buflen == 0:
	    return
	if buflen == 1:
	    raise Error('Base85Decode: short data')
	buf = (self._buf + [0,0,0,0])[:5]
	m = reduce(lambda s,(a,b):s+a*b, 
		zip(buf,[52200625, 614125, 7225, 85, 1]), 0)
	b = map(lambda y,m=m:chr((m>>y)&0xff), [24,16,8,0])
	#print "".join(map(lambda x:chr(x+33),self._buf)), "->",
	#print ":".join(map(lambda x:"%02x"%ord(x),b[:buflen-1]))
	self._out.extend(b[:buflen-1])
	self._buf = []

class ASCII85DecodeFilter(FilteredByteStream):
    def rewind(self):
	FilteredByteStream.rewind(self)
	self._decoder = ASCII85Decoder()
    def filter(self, data):
	return self._decoder.feed(data)

class ASCIIHexDecoder:
    Hexmap = { '0':0, '1':1, '2':2, '3':3, '4':4, '5':5, '6':6, '7':7,
	'8':8, '9':9, 'a':10, 'b':11, 'c':12, 'd':13, 'e':14, 'f':15,
	'A':10, 'B':11, 'C':12, 'D':13, 'E':14, 'F':15 }
    def __init__(self):
	self.msn = None	# most significant nibble!
	self.eod = False
    def feed(self, data):
	out = []
	if self.eod:
	    return ''
	for c in data:
	    if c in Tokeniser.Whitespace:
		continue
	    if c == '>':
		if self.msn is not None:
		    out.append(self.msn)
		self.eod = True
		break
	    v = self.Hexmap.get(c)
	    if v is None:
		raise Error('ASCIIHex: bad input character %s', `c`)
	    if self.msn is None:
		self.msn = v * 0x10
	    else:
		out.append(self.msn + v)
		self.msn = None
	return ''.join(map(chr, out))

class ASCIIHexDecodeFilter(FilteredByteStream):
    def rewind(self):
	FilteredByteStream.rewind(self)
	self._decoder = ASCIIHexDecoder()
    def filter(self, data):
	return self._decoder.feed(data)

class RunLengthDecoder:
    """Run length decoding filter.  Input consists of 'length' bytes
       followed by 0 or more data bytes.  A length byte of 128 means
       end of data.  A length byte less than 128 means that length+1
       bytes of literal data follows.  Otherwise, a single byte
       follows that is to be repeated 257-length times."""
    def __init__(self):
	self.state = -1
    def feed(self, data):
	pos = 0
	datalen = len(data)
	if datalen == 0 and self.state not in (None, -1):
	    raise Error('RunLengthDecodeFilter: short input')
	out = ''
	if self.state is not None:
	    while pos < datalen:
		if self.state == -1:
		    self.state = ord(data[pos])
		    pos += 1
		elif self.state < 128:
		    l = min(self.state + 1, datalen - pos)
		    out += data[pos:pos + l]
		    self.state -= l
		    pos += l
		elif self.state == 128:
		    self.state = None
		    break
		else: # 129..255
		    out += data[pos] * (257 - self.state)
		    pos += 1
		    self.state = -1
	return out

class RunLengthDecodeFilter(FilteredByteStream):
    def rewind(self):
	FilteredByteStream.rewind(self)
	self._decoder = RunLengthDecoder()
    def filter(self, data):
	return self._decoder.feed(data)

class LZWDecoder:
    """A Lempel-Ziv decoder based on the descripion in
       section 3.3.3 of the PDF Reference. The book mentions
       that the algorithm is patented, so you and I should
       never run this."""

    ClearTable = 256
    EndOfData = 257

    def __init__(self):
	self.inbuf = []
	self.eod = 0
	self.bitpos = 0
	self.lastcode = self.ClearTable
	self.clear()

    def clear(self):
	self.table = map(chr, range(256)) + ['']
	self.bits = 9

    def feed(self, data):
	self.inbuf += map(ord,data)
	out = ''
	while not self.eod:
	    code = self.nextcode()
	    if code == -1:
		break
	    elif code == self.EndOfData:
		self.eod = 1
	    else:
		self.eat(code)
	        out += self.table[code]
	return out

    def nextcode(self):
	"""nextcode() -> integer
	   Return the next 'self.bits'-long code from the input buffer,
	   or return -1 if not yet enough data"""
	nextbitpos = self.bitpos + self.bits
	if nextbitpos > 8 * len(self.inbuf):
	    return -1
	code = self.inbuf[0]
	if nextbitpos > 8:
	    code = code * 256 + self.inbuf[1]
	    if nextbitpos > 16:
		code = code * 256 + self.inbuf[2]
	#print "[%s]" % " ".join(map(lambda x:"%02x"%x, self.inbuf[:20]))
	#print "bitpos %d nextbitpos %d inbuf del %d" % (
	#	self.bitpos, nextbitpos, nextbitpos / 8)
	del self.inbuf[:nextbitpos / 8]
	nextbitpos %= 8
	code = (code >> ((8-nextbitpos)%8)) & ((1 << self.bits) - 1)
	self.bitpos = nextbitpos
	return code
    def eat(self, code):
	"""eat(code) -> None
	   Receive a code, and track the encoder state."""
	if code == self.ClearTable:
	    #print "%d -> clear table" % code
	    self.clear()
	else:
	    lastcode = self.lastcode
 	    #print `self.table[lastcode]`, code,
	    #print "adding code", len(self.table), "->",
	    if code == len(self.table):
		newstr = self.table[lastcode] + self.table[lastcode][0]
	    elif code > len(self.table):
		raise Error("LZWDecoder: bad input: code beyond table bounds")
	    else:
	        newstr = self.table[lastcode] + self.table[code][0]
	    #print " ".join(map(lambda x:"%d"%ord(x), newstr)), "=", `newstr`
	    self.table.append(newstr)
	    if len(self.table) == 511: self.bits = 10
	    if len(self.table) == 1023: self.bits = 11
	    if len(self.table) == 2047: self.bits = 12
	self.lastcode = code

class LZWDecodeFilter(FilteredByteStream):
    def rewind(self):
	FilteredByteStream.rewind(self)
	self._decoder = LZWDecoder()
    def filter(self, data):
	return self._decoder.feed(data)

#-- Unimplemented filters: None means do not filter. Caller gets raw data.
CCITTFaxDecodeFilter = None
JBIG2DecodeFilter = None
DCTDecodeFilter = None

Filtermap = {
	'ASCIIHexDecode':	ASCIIHexDecodeFilter,
	'AHx':			ASCIIHexDecodeFilter,
	'ASCII85Decode':	ASCII85DecodeFilter,
	'A85':			ASCII85DecodeFilter,
	'LZWDecode':		LZWDecodeFilter,
	'LZW':			LZWDecodeFilter,
	'FlateDecode':		FlateDecodeFilter,
	'Fl':			FlateDecodeFilter,
	'RunLengthDecode':	RunLengthDecodeFilter,
	'RL':			RunLengthDecodeFilter,
	'CCITTFaxDecode':	CCITTFaxDecodeFilter,
	'CCF':			CCITTFaxDecodeFilter,
	'JBIG2Decode':		JBIG2DecodeFilter,
	'DCTDecode':		DCTDecodeFilter,
	'DCT':			DCTDecodeFilter,
}

class UnknownFilterError(Error):
	pass

#------------------------------------------------------------
# testing

def test_decoders():
    #-- this example from the reference manual
    #-- note that in the last line of the example in
    #   the reference, an extra 8 appears at the start!!
    print "Testing ascii85/lzw decoders"
    z = r"""
	J..)6T`?p&<!J9%_[umg"B7/Z7KNXbN'S+,*Q/&"OLT'F
	LIDK#!n`$"<Atdi`\Vn%b%)&'cA*VnK\CJY(sF>c!Jnl@
	RM]WM;jjH6Gnc75idkL5]+cPZKEBPWdR>FF(kj1_R%W_d
	&/jS!;iuad7h?[L-F$+]]0A3Ck*$I0KZ?;<)CJtqi65Xb
	Vc3\n5ua:Q/=0$W<#N3U;H,MQKqfg1?:lUpR;6oN[C2E4
	ZNr8Udn.'p+?#X+1>0Kuk$bCDF/(3fL5]Oq)^kJZ!C2H1
	'TO]Rl?Q:&'<5&iP!$Rq;BXRecDN[IJB`,)o8XJOSJ9sD
	S]hQ;Rj@!ND)bD_q&C\g:inYC%)&u#:u,M6Bm%IY!Kb1+
	":aAa'S`ViJglLb8<W9k6Yl\\0McJQkDeLWdPN?9A'jX*
	al>iG1p&i;eVoK&juJHs9%;Xomop"5KatWRT"JQ#qYuL,
	JD?M$0QP)lKn06l1apKDC@\qJ4B!!(5m+j.7F790m(Vj8
	l8Q:_CZ(Gm1%X\N1&u!FKHMB~>
	"""
    print "original stream:",z
    z2 = ASCII85Decoder().feed(z)
    print "after ascii85 decoding:", " ".join(map(lambda x:"%02x"%ord(x), z2))
    z3 = LZWDecoder().feed(z2)
    print "\nafter LZW decoding:", `z3`

    print "\nTesting Runlength"
    rld = RunLengthDecoder()
    for seg in ('\x01H', 'e\xFFl\x00o', '\x06', ', there\x80!', 'ignore', ''):
	print "\t",`seg`, '->', `rld.feed(seg)`

    print "\nTesting ASCIIHex decoding"
    ahd = ASCIIHexDecoder()
    for seg in ('  4 8 6', ' 56\n C 6c2c20 50 6f 7 ', ' ', ' > zzz! ', ''):
	print "\t",`seg`, '->', `ahd.feed(seg)`

def test_outline(f):
    """ Test the interpreter by printing the document's outline/TOC """
    #-- 3.6.1 Document Catalog ('Root')
    #-- 8.2.2 Document Outline
    ol = f.Root['Outlines']
    if ol is NullObj:
	print "No Outline (TOC) for file"
	return # no outline
    print "Outline tree (TOC) for the document:"
    last = ol['Last']
    item = ol['First']
    while 1:
	test_outline_item(item, 0)
	if item.id() == last.id(): break
	item = item['Next']

def test_outline_item(obj, depth):
    title = str(obj['Title']).replace('\r',' ').replace('\n',' ')
    if obj['F']:
	flags = int(obj['F'])
	if flags & (1 << 1): title = "<i>"+title+"</i>"
	if flags & (1 << 2): title = "<b>"+title+"</b>"
    print (' ' * (depth * 3)) + '+ ' + title
    if obj['First']:
	last = obj['Last']
	item = obj['First']
	while 1:
	    test_outline_item(item, depth + 1)
	    if item.id() == last.id(): break
	    item = item['Next']

def test_page_print(page):
    if page['Kids'].value() is not None:
        for kid in page['Kids'].value():
            print repr(kid['Contents'].value())
#            if kid['Contents'] is not NullObj:
#                stream = kid['Contents'].value()
#                print str(stream)
            test_page_print(kid)
	    
if __name__ == '__main__':
    if len(sys.argv) == 1:
        test_decoders()
    if len(sys.argv) > 1:
	f = PDFFile()
	for path in sys.argv[1:]:
	    print "loading", path, "..."
	    f.load_file(path)
	    #Object.repr_expand = True
	    #print "trailers: ", repr(f.Trailers)
	    #print "xrefs: ", repr(f.xrefs)
	    print "Root: ", repr(f.Root.value())
	    print "Info: ", repr(f.Info.value())
	    print "security: ", repr(f.Security)
	    #print "pretty-print:"
	    #f.PrettyPrint(f.Root)
	    #test_outline(f)
	    #print "Root.Pages: ", repr(f.Root['Pages'].value())
	    test_page_print(f.Root['Pages'])
	    print
