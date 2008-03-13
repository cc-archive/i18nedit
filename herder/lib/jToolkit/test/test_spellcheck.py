from jToolkit import spellcheck

class TestSpellCheck:
    disabled = not spellcheck.have_checker()
    def test_can_check_lang(self):
        assert spellcheck.can_check_lang()
        assert not spellcheck.can_check_lang("unknownlanguage")
        # repeat checks to make sure cache works
        assert spellcheck.can_check_lang()
        assert not spellcheck.can_check_lang("unknownlanguage")

    def test_english_check(self):
        assert not spellcheck.check("perfect spelling", "en")
        assert spellcheck.check("flawd speling", "en")

