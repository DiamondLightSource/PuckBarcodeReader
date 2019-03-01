from __future__ import division



from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QLabel, QGroupBox, QVBoxLayout

from dls_barcode.gui.image_widget import ImageWidget


class ImageFrame(QGroupBox):
    """ GUI component. Displays an image of the currently selected barcode.
    """
    def __init__(self, title):
        super(ImageFrame, self).__init__()
        self.setTitle(title)
        self._init_ui()

    def _init_ui(self):
        # Image frame - displays image of the currently selected scan record
        self._frame = ImageWidget()
        self._frame.setStyleSheet("background-color: white; color: red; font-size: 30pt; text-align: center")
        self._frame.setMinimumWidth(700)
        self._frame.setAlignment(Qt.AlignCenter)
        vbox = QVBoxLayout()
        vbox.addWidget(self._frame)

        self.setLayout(vbox)

    def clear_frame(self, message):
        self._frame.clear()
        self._frame.setText(message)

    def display_puck_image(self, image):
        """ Called when a new row is selected on the record table. Displays the specified
        image (image of the highlighted scan) in the image frame
        """
        self._frame.clear()
        self._frame.setAlignment(Qt.AlignCenter)

        if image is not None and image.is_valid():
            pixmap = image.to_qt_pixmap(self._frame.size())
            self._frame.setPixmap(pixmap)
        else:
            self._frame.setText("Image Not Found")
