from PyQt4 import QtGui, QtCore
import sys
import time

try:
    from pkg_resources import require
    require("numpy")
except:
    pass

import numpy as np
import cv2


class CamTest(QtGui.QMainWindow):

    def __init__(self):
        super(CamTest, self).__init__()

        self.setGeometry(100, 100, 850, 800)
        self.setWindowTitle('Diamond Puck Barcode Scanner')

        self.img_frame = QtGui.QLabel(self)
        self.img_frame.setGeometry(0, 0, 700, 700)
        self.show()

        self.camera_loop()



    def camera_loop(self):
        cap = cv2.VideoCapture(0)
        cap.set(3,1920)
        cap.set(4,1080)

        #cap.set(cv2.CV_CAP_PROP_FRAME_WIDTH, 1920)
        #cap.set(cv2.CV_CAP_PROP_FRAME_HEIGHT, 1080)
        print(str(cap.get(3)), str(cap.get(4)))
        print("test")

        while(True):
            # Capture frame-by-frame
            _, frame = cap.read()
            #print(frame)

            # Our operations on the frame come here
            #gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            height, width, channels = frame.shape
            image = QtGui.QImage(frame.tostring(), width, height, QtGui.QImage.Format_RGB888).rgbSwapped()
            pixmap = QtGui.QPixmap.fromImage(image)

            self.img_frame.setPixmap(pixmap.scaled(self.img_frame.size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
            self.img_frame.setAlignment(QtCore.Qt.AlignCenter)
            #print("test")


            # Display the resulting frame
            cv2.imshow('frame', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break



        # When everything done, release the capture
        cap.release()
        cv2.destroyAllWindows()


def main():
    app = QtGui.QApplication(sys.argv)
    ex = CamTest()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
