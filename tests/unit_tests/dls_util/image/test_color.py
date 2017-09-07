import unittest

from mock import MagicMock, patch

from dls_util.image import Color

class TestColor(unittest.TestCase):

    def setUp(self):
        self.firstColor = Color(10,50,100)



    def test_bgra(self):
        self.assertEquals(Color.bgra(self.firstColor), (100,50,10,255))

    def test_bgr(self):
        self.assertEquals(Color.bgr(self.firstColor), (100,50,10))

    def test_mono(self):
        self.assertEquals(Color.mono(self.firstColor), round(0.3*10 + 0.6*50 + 0.1*100))

    #def test_to_qcolor(self):

    def test_to_hex(self):
        self.assertEquals(Color.to_hex(self.firstColor), '#0a3264')

    #def test_from_qt(self):

    #def test_from_string(self):
     #   str = "10,50,100"
     #  self.assertEquals(Color.from_string(str,",").to_hex(),self.firstColor.to_hex())





