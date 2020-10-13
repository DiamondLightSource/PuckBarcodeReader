import os.path
from PyQt5.QtWidgets import QMessageBox

from dls_util.config import DirectoryConfigControl


class StartupDirectoryConfigControl(DirectoryConfigControl):
    def __init__(self, config_item):
        DirectoryConfigControl.__init__(self, config_item)

    def before_apply(self):
        self.is_confirmed = True
        current_dir = self._config_item.value()
        new_dir = self._txt_dir.text()
        if os.path.abspath(new_dir) == os.path.abspath(current_dir):
            return

        confirm_msg = (
            "The Startup {} was changed from {} to\n {} \n\n"
            "This change will only take effect at the next startup.".format(
                self._config_item.tag(), current_dir, new_dir
            )
        )
        reply = QMessageBox.information(
            self,
            "Startup {}".format(self._config_item.tag()),
            confirm_msg,
            QMessageBox.Ok,
            QMessageBox.Cancel,
        )

        if reply == QMessageBox.Cancel:
            self.is_confirmed = False
