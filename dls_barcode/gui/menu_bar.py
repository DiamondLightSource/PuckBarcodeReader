from __future__ import division

from PyQt5.QtWidgets import qApp, QAction, QMainWindow, QStyle


class MenuBar(QMainWindow):
    """ GUI component. Displays a start/stop button
    """

    def __init__(self, mainMenu, version, flags, *args, **kwargs):
        #super(MenuBar, self).__init__(mainMenu, version)
        super().__init__(flags, *args, **kwargs)
        self._version = version

        self._exit_icon = self.style().standardIcon(QStyle.SP_DialogCloseButton)
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
        # Exit Application
        self._exit_action = QAction(self._exit_icon, '&Exit', self)
        self._exit_action.setShortcut('Ctrl+Q')
        self._exit_action.setStatusTip('Exit application')

        # Open options dialog
        self._options_action = QAction(self._config_icon, '&Config', self)
        self._options_action.setShortcut('Ctrl+O')
        self._options_action.setStatusTip('Open Options Dialog')

        # Show version number
        self._about_action = QAction(self._about_icon, "About", self)

        # Create menu bar
        file_menu = self._mainMenu.addMenu('&File')
        file_menu.addAction(self._exit_action)

        option_menu = self._mainMenu.addMenu('&Options')
        option_menu.addAction(self._options_action)

        help_menu = self._mainMenu.addMenu('?')
        help_menu.addAction(self._about_action)

    def exit_action_triggered(self, cleanup):
#        self._exit_action.triggered.connect(cleanup)
        self._exit_action.triggered.connect(qApp.quit)

    def optiones_action_triggered(self, on_options_action_clicked):
        self._options_action.triggered.connect(on_options_action_clicked)

    def about_action_trigerred(self, on_about_action_clicked):
        self._about_action.triggered.connect(on_about_action_clicked)
