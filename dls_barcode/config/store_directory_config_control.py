from PyQt4 import QtGui

from dls_util.config import DirectoryConfigControl


class StoreDirectoryConfigControl(DirectoryConfigControl):

    def __init__(self, config_item):
        DirectoryConfigControl.__init__(self, config_item)

    def before_apply(self):
        self.is_confirmed = True
        if self._txt_dir.text() == self._config_item.value():
            return

        confirm_msg = "TODO: add message here"
        reply = QtGui.QMessageBox.question(self, 'CHANGE ME to Change Store Directory',
                                           confirm_msg, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)

        if reply == QtGui.QMessageBox.No:
            self.is_confirmed = False


