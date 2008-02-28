from jToolkit.data import archiver
import datetime

class TestArchiver:
    def test_ConvertValue(self):
        """Tests the value conversion function, making sure it converts what it's meant to"""
        assert archiver.ConvertValue('None') == None
        assert archiver.ConvertValue('13') == 13
        assert archiver.ConvertValue('-13') == -13
        assert archiver.ConvertValue('1.#QNAN') == None
        assert archiver.ConvertValue('1.#INF') == None
        assert archiver.ConvertValue('-1.#IND') == None
        assert archiver.ConvertValue('34.12') == 34.12
        assert archiver.ConvertValue('frog') == 'frog'

        datestr = '11/04/05 12:34:23'
        dateobj = archiver.ConvertValue(datestr)
        assert isinstance(dateobj, datetime.datetime)
        assert dateobj.year == 2005
        assert dateobj.month == 11
        assert dateobj.day == 04
        assert dateobj.hour == 12
        assert dateobj.minute == 34
        assert dateobj.second == 23
        
