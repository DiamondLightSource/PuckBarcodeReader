from random import randint

from PyQt5.QtGui import QColor


class Color:
    SEP = ","
    CONSTRUCTOR_ERROR = "Values must be integers in range 0-255"
    STRING_PARSE_ERROR = "Input string must be 3 or 4 integers (0-255) separated by '{}'".format(SEP)


    def __init__(self, r, g, b, a=255):
        try:
            r, g, b, a = int(r), int(g), int(b), int(a)
        except ValueError:
            raise ValueError(self.CONSTRUCTOR_ERROR)

        for val in [r, g, b, a]:
            if val < 0 or val > 255:
                raise ValueError(self.CONSTRUCTOR_ERROR)

        self.r = r
        self.g = g
        self.b = b
        self.a = a

    def __str__(self):
        return "{1}{0}{2}{0}{3}{0}{4}".format(self.SEP, self.r, self.g, self.b, self.a)

    def bgra(self):
        return self.b, self.g, self.r, self.a

    def bgr(self):
        return self.b, self.g, self.r

    def mono(self):
        return int(round(0.3*self.r + 0.6*self.g + 0.1*self.b))

    def to_qt(self):
        return QColor(self.r, self.g, self.b, self.a)

    def to_hex(self):
        hex_str = '#'
        for val in [self.r, self.g, self.b]:
            hex_str += '{:02x}'.format(val)

        return hex_str

    def rgb(self):
        return self.r, self.g, self.b

    @staticmethod
    def from_qt(qt_color):
        return Color(qt_color.red(), qt_color.green(), qt_color.blue(), qt_color.alpha())

    @staticmethod
    def from_string(string, sep=SEP):
        tokens = string.split(sep)

        if len(tokens) == 3:
            r, g, b = tuple(tokens)
            color = Color(r, g, b)
        elif len(tokens) == 4:
            r, g, b, a = tuple(tokens)
            color = Color(r, g, b, a)
        else:
            raise ValueError(Color.STRING_PARSE_ERROR)

        return color

    @staticmethod
    def Random():
        return Color(randint(0, 255), randint(0, 255), randint(0, 255), 255)

    @staticmethod
    def TransparentBlack(): return Color(0, 0, 0, 0)

    @staticmethod
    def TransparentWhite(): return Color(255, 255, 255, 0)

    @staticmethod
    def White(): return Color(255, 255, 255)

    @staticmethod
    def Black(): return Color(0, 0, 0)

    @staticmethod
    def Grey(): return Color(128, 128, 128)

    @staticmethod
    def Blue(): return Color(0, 0, 255)

    @staticmethod
    def Red(): return Color(255, 0, 0)

    @staticmethod
    def Green(): return Color(0, 255, 0)

    @staticmethod
    def Yellow(): return Color(255, 255, 0)

    @staticmethod
    def Cyan(): return Color(0, 255, 255)

    @staticmethod
    def Magenta(): return Color(255, 0, 255)

    @staticmethod
    def Orange(): return Color(255, 128, 0)

    @staticmethod
    def Purple(): return Color(128, 0, 255)
