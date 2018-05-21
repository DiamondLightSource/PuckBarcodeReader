from __future__ import division

from PyQt4.QtGui import qApp, QAction, QMainWindow, QStyle


class MenuBar(QMainWindow):
    """ GUI component. Displays a start/stop button
    """

    def __init__(self, mainMenu, version, clean_up, on_options_action_clicked, on_about_action_clicked):
        super(MenuBar, self).__init__()
        self._version = version
        self._cleanup = clean_up
        self._on_options_action_clicked = on_options_action_clicked
        self._on_about_action_clicked = on_about_action_clicked

        self._exit_icon = self.style().standardIcon(QStyle.SP_DialogCloseButton)
        self._config_icon = self.style().standardIcon(QStyle.SP_FileDialogDetailedView)
        self._about_icon = self.style().standardIcon(QStyle.SP_FileDialogInfoView)

        self._mainMenu = mainMenu

        self._init_ui()

    def _init_ui(self):
        """Create and populate the menu bar.
              """
        # Exit Application
        exit_action = QAction(self._exit_icon, '&Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit application')
        exit_action.triggered.connect(self._cleanup)
        exit_action.triggered.connect(qApp.quit)

        # Open options dialog
        options_action = QAction(self._config_icon, '&Config', self)
        options_action.setShortcut('Ctrl+O')
        options_action.setStatusTip('Open Options Dialog')
        options_action.triggered.connect(self._on_options_action_clicked)

        # Show version number
        about_action = QAction(self._about_icon, "About", self)
        about_action.triggered.connect(self._on_about_action_clicked)

        # Create menu bar
        file_menu = self._mainMenu.addMenu('&File')
        file_menu.addAction(exit_action)

        option_menu = self._mainMenu.addMenu('&Options')
        option_menu.addAction(options_action)

        help_menu = self._mainMenu.addMenu('?')
        help_menu.addAction(about_action)
