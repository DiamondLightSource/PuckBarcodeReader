import unittest

from dls_util.image import Color

class TestColor(unittest.TestCase):
    # given-when-then

    def setUp(self):
        self.firstColor = Color(10, 50, 100)

    def test_init_riases_valueerror_when_r_is_not_number(self):
        with self.assertRaises(ValueError):
            Color("a", 50, 100)

    def test_init_riases_valueerror_when_r_is_lt_zero(self):
        with self.assertRaises(ValueError):
            Color(-10, 50, 100)

    def test_init_riases_valueerror_when_r_is_gt_255(self):
        with self.assertRaises(ValueError):
            Color(400, 50, 100)

    def test_init_sets_alpha_255_if_not_set(self):
        self.assertEquals(self.firstColor.a, 255)


    def test_bgra_returns_rgb_plus_alpha_tuple(self):
        self.assertEquals(Color.bgra(self.firstColor), (100,50,10,255))

    def test_bgr_returns_blue_green_red(self):
        self.assertEquals(self.firstColor.bgr(), (100,50,10))

    def test_mono_returns_one_value_function_of_rgb(self):
        self.assertEquals(Color.mono(self.firstColor), round(0.3*10 + 0.6*50 + 0.1*100))

    def test_to_qt_returns_QColour_of_rgba_values_zeroone(self):

        actual = Color.to_qt(self.firstColor)
        self.assertEqual(actual.getRgbF(),  (10.0/255, 50.0/255, 100.0/255, 1.0))

    def test_from_qt_returns_QColour_of_rgba_as_zero255(self):

        qtcolor = Color.to_qt(self.firstColor)
        actual = Color.from_qt(qtcolor)

        self.assertEqual(Color.bgra(actual),  (100, 50, 10, 255))

    def test_to_hex_10_50_100_returns_0a3264(self):
        self.assertEquals(Color.to_hex(self.firstColor), '#0a3264')

    def test_to_string_returns_csv_rgba(self):
        self.assertEqual(str(self.firstColor), "10,50,100,255")

    def test_Black_is_000000(self):
        self.assertEqual(Color.Black().to_hex(), "#000000")

    def test_Blue_is_0000ff(self):
        self.assertEqual(Color.Blue().to_hex(), "#0000ff")

    def test_Grey_is_808080(self):
        self.assertEqual(Color.Grey().to_hex(), "#808080")

    def test_from_string_returns_Color_with_given_rbg_and_alpha255_with_csv_three_valued_string(self):
        col = Color.from_string("25, 100, 243")
        self.assertEqual(col.bgra(), (243, 100, 25, 255))

    def test_from_string_returns_Color_with_given_rbga_with_csv_four_valued_string(self):
        col = Color.from_string("251, 63, 1, 128")
        self.assertEqual(col.bgra(), (1, 63, 251, 128))

    def test_from_string_returns_Color_with_given_rbga_with_custom_seperator_four_valued_string(self):
        col = Color.from_string("251;63;1;128", ";")
        self.assertEqual(col.bgra(), (1, 63, 251, 128))

    def test_from_string_raises_ValueError_if_no_separator(self):
        self.assertRaises(ValueError, Color.from_string, "121242")
