from PyQt4 import QtGui

from dls_barcode.util.image import Image


class Options:
    def __init__(self):
        self.colour_ok = Image.GREEN
        self.color_not_found = Image.RED
        self.color_unreadable = Image.ORANGE

        self.store_file = ""


class OptionsDialog(QtGui.QDialog):

    def __init__(self, options):
        super(OptionsDialog, self).__init__()

        self.options = options

        self._init_ui()


    def _init_ui(self):
        """ Create the basic elements of the user interface.
        """
        self.setGeometry(100, 100, 400, 650)
        self.setWindowTitle('Options')
        self.setWindowIcon(QtGui.QIcon('web.png'))

        col = QtGui.QColor(0, 0, 0)

        self.btn = QtGui.QPushButton('Dialog', self)
        self.btn.move(20, 20)

        self.btn.clicked.connect(self.getColorFromDialog)

    def getColorFromDialog(self):
        col = QtGui.QColorDialog.getColor()

        if col.isValid():
            print(col)



