#!/usr/bin/env python

from jToolkit import prefs
import os

class TestPrefs:
    def setup_method(self, method):
        """make sure we have a unique prefsfilename that doesn't exist"""
        self.prefsfilename = "%s.prefs" % method.__name__
        if os.path.exists(self.prefsfilename):
            os.remove(self.prefsfilename)

    def teardown_method(self, method):
        """remove the prefs file if it was created"""
        if os.path.exists(self.prefsfilename):
            os.remove(self.prefsfilename)

    def test_levels(self):
        """test we can set things on multiple levels"""
        p = prefs.PrefsParser()
        p.parse("one.two.three = 'block'")
        assert p.one.two.three == 'block'
        assert hasattr(p, "one.two.three")
        assert hasattr(p.one, "two.three")
        assert getattr(p, "one.two.three") == "block"
        assert getattr(p.one, "two.three") == "block"

    def test_missing(self):
        """tests missing values are missing"""
        p = prefs.PrefsParser()
        p.testvalue = "hello"
        p.savefile(self.prefsfilename)
        p2 = prefs.PrefsParser(self.prefsfilename)
        assert not hasattr(p2, "DBNAME")
        assert not hasattr(p2, "testvalue.missing")

    def test_save(self):
        """test we can save a file"""
        p = prefs.PrefsParser()
        p.testvalue = "hello"
        p.savefile(self.prefsfilename)
        p2 = prefs.PrefsParser(self.prefsfilename)
        assert p2.testvalue == "hello"

    def test_safe_save(self):
        """test we can safely save over a file"""
        p = prefs.PrefsParser()
        p.testvalue = "hello"
        p.savefile(self.prefsfilename)
        p2 = prefs.PrefsParser()
        p2.testvalue = "goodbye"
        p2.savefile(self.prefsfilename, safesave=True)
        prefsfiles = [x for x in os.listdir(os.curdir) if x.startswith(self.prefsfilename)]
        assert prefsfiles == [self.prefsfilename]
        p3 = prefs.PrefsParser(self.prefsfilename)
        assert p3.testvalue == "goodbye"

    def test_add_unicode_value(self):
        """test we can safely add a unicode value"""
        p = prefs.PrefsParser()
        unicodevalue = u'm\xd0\x9c\xd0\x91'
        p.unicodevalue = unicodevalue
        p.savefile(self.prefsfilename)
        p2 = prefs.PrefsParser(self.prefsfilename)
        assert p2.unicodevalue == unicodevalue

    def test_add_nonascii_key(self):
        """test we can safely add a none-ascii key"""
        p = prefs.PrefsParser()
        nonasciikey = u'm\xd0\x9c\xd0\x91'.encode("utf-8")
        setattr(p, nonasciikey, "test")
        p.savefile(self.prefsfilename)
        p2 = prefs.PrefsParser(self.prefsfilename)
        assert getattr(p2, nonasciikey) == "test"

    def test_add_unicode_key(self):
        """test we can safely add a unicode key"""
        # currently python doesn't seem to support actual unicode attributes
        # so we aren't using setattr, getattr directly here
        p = prefs.PrefsParser()
        testunicodekey = u'm\xd0\x9c\xd0\x91'
        # setattr(p, testunicodekey, "test")
        p.setvalue(testunicodekey, "test")
        p.savefile(self.prefsfilename)
        p2 = prefs.PrefsParser(self.prefsfilename)
        # assert getattr(p2, testunicodekey) == "test"
        assert p2.__getattr__(testunicodekey) == "test"

    def test_add_unicode_key_like_string(self):
        """test we can safely add an ascii unicode key and it works as a string too"""
        # currently python doesn't seem to support actual unicode attributes
        # so we aren't using setattr, getattr directly here
        p = prefs.PrefsParser()
        testunicodekey = 'normalascii'
        p.setvalue("parent." + testunicodekey, u"test")
        p.savefile(self.prefsfilename)
        p2 = prefs.PrefsParser(self.prefsfilename)
        parent = p2.parent
        assert parent.__hasattr__(unicode(testunicodekey))
        assert parent.__hasattr__(testunicodekey)
        assert parent.__getattr__(unicode(testunicodekey)) == u"test"
        assert parent.__getattr__(testunicodekey) == u"test"

    def test_add_unicode_key_child(self):
        """test we can safely add a child to a unicode key"""
        p = prefs.PrefsParser()
        testunicodekey = u'm\xd0\x9c\xd0\x91'
        p.setvalue(testunicodekey + ".node1", "test")
        p.savefile(self.prefsfilename)
        p2 = prefs.PrefsParser(self.prefsfilename)
        assert p2.__getattr__(testunicodekey + ".node1") == "test"
        p2.setvalue(testunicodekey + ".node2", u"test")
        p2.savefile()
        p3 = prefs.PrefsParser(self.prefsfilename)
        assert p2.__getattr__(testunicodekey + ".node2") == "test"

    def test_add_unicode_key_as_child(self):
        """test we can safely add a unicode key as a child of an existing node"""
        p = prefs.PrefsParser()
        testunicodekey = u'm\xd0\xd0'
        p.setvalue("node1.before", "trip")
        p.savefile(self.prefsfilename)
        p = prefs.PrefsParser(self.prefsfilename)
        assert p.node1.before == "trip"
        p.setvalue("node1." + testunicodekey, "test")
        p.savefile(self.prefsfilename)
        prefscontents = open(self.prefsfilename, "r").read()
        print prefscontents
        assert "u'" in prefscontents
        # p2 = prefs.PrefsParser(self.prefsfilename)
        p2 = p
        assert p2.__getattr__("node1." + testunicodekey) == "test"
        node1 = p2.node1
        assert node1.__hasattr__(testunicodekey)
        assert testunicodekey in node1.__dict__
        node1.__delattr__(testunicodekey)
        assert not node1.__hasattr__(testunicodekey)

    def test_import_module(self):
        """test we can use string values from imported modules"""
        # TODO: this shouldn't rely on an existing module's existice
        from jToolkit.data import ADOProviders
        assert isinstance(ADOProviders.OracleProvider, basestring)
        importsource = "importmodules:\n  ADOProviders = 'jToolkit.data.ADOProviders'\n"
        usesource = "test = ADOProviders.OracleProvider\n"
        open(self.prefsfilename, "w").write(importsource + usesource)
        p = prefs.PrefsParser()
        p.parsefile(self.prefsfilename)
        p.resolveimportmodules()
        if isinstance(p.test, prefs.UnresolvedPref):
          p.test = p.test.resolve()
        assert p.test == ADOProviders.OracleProvider

