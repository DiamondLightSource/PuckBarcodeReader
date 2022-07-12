from __future__ import division

from PyQt5.QtWidgets import qApp, QAction, QMainWindow, QStyle


class MenuBar(QMainWindow):
    """ GUI component. Displays a start/stop button
    """

    def __init__(self, mainMenu, version, flags, *args, **kwargs):
        #super(MenuBar, self).__init__(mainMenu, version)
        super().__init__(flags, *args, **kwargs)
        self._version = version

        self._config_icon = self.style().standardIcon(QStyle.SP_FileDialogDetailedView)
        self._about_icon = self.style().standardIcon(QStyle.SP_FileDialogInfoView)

        self._mainMenu = mainMenu
        self._exit_action = None
        self._options_action = None
        self._about_action = None

        self._init_ui()

    def _init_ui(self):
        """Create and populate the menu bar.
              """

        # Open options dialog
        self._options_action = QAction(self._config_icon, '&Config', self)
        self._options_action.setShortcut('Ctrl+O')
        self._options_action.setStatusTip('Open Options Dialog')

        # Show version number
        self._about_action = QAction(self._about_icon, "About", self)

        option_menu = self._mainMenu.addMenu('&Options')
        option_menu.addAction(self._options_action)

        help_menu = self._mainMenu.addMenu('?')
        help_menu.addAction(self._about_action)


    def options_action_triggered(self, on_options_action_clicked):
        self._options_action.triggered.connect(on_options_action_clicked)

    def about_action_trigerred(self, on_about_action_clicked):
        self._about_action.triggered.connect(on_about_action_clicked)
