import sys

from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import QLabel, QVBoxLayout, QHBoxLayout, QMessageBox, QLineEdit, QPushButton, \
    QGroupBox, QWidget, QCheckBox, QComboBox

from .config import *


class ConfigDialog(QtGui.QDialog):
    """ Creates a Qt Dialog that allows the user to edit the values of a set of options. This is intended
    to be used in conjunction with the Config class.

    A different type of control is implemented for each type of ConfigItem, e.g., for an integer a simple
    text box is displayed, whereas for a Color, a color picker is shown. To create controls for new types
    of config item, simply subclass ConfigControl.

    ConfigDialog may be used in one of two ways. First, you can just create an instance of ConfigDialog
    and call auto_layout():
        >>> dialog = ConfigDialog(my_config)
        >>> dialog.auto_layout()
        >>> dialog.exec_()
    This will automatically create a control of the appropriate type for each option, and lay them out in
    the order that they were added to the Config.

    The second option is to subclass ConfigDialog, and then specify the layout in the constructor. Create
    a new group (a named group box) by calling start_group(), then add config items to that group by
    using the add_item() method. Finally, use the finalize_layout() method when all the items have been
    added.
        >>> class MyConfigDialog(ConfigDialog):
        >>> def __init__(self, config):
        >>>     ConfigDialog.__init__(self, config)
        >>>
        >>>     self.start_group("Group 1")
        >>>     self.add_item(self._config.color_option1)
        >>>
        >>>     self.start_group("Group 2")
        >>>     self.add_item(self._config.int_option1)
        >>>     self.add_item(self._config.dir_option1)
        >>>
        >>>     self.finalize_layout()
    """

    LABEL_WIDTH = 110

    def __init__(self, config):
        super(ConfigDialog, self).__init__()

        self._config = config

        self._groups = []
        self._config_controls = []

        self.setWindowTitle('Config')

    def auto_layout(self):
        """ Automatically create controls for every option in the Config and lay them out in order. """
        for item in self._config._items:
            self.add_item(item)

        self.finalize_layout()

    def start_group(self, name):
        """ Start a new option group. Every option will be added to this group, until this function is
        called again, which will start another group. """
        group = _ConfigGroupBox(name)
        self._groups.append(group)

    def add_item(self, item):
        """ Add a config item to the dialog. A control of the appropriate type will be automatically created.
        The control will be added to the current group, or a new group will be created if none exists. """
        add = self._add_control

        if isinstance(item, IntConfigItem):
            add(ValueConfigControl(item, txt_width=40))
        elif isinstance(item, BoolConfigItem):
            add(BoolConfigControl(item))
        elif isinstance(item, EnumConfigItem):
            add(EnumConfigControl(item))
        elif isinstance(item, ColorConfigItem):
            add(ColorConfigControl(item))
        elif isinstance(item, DirectoryConfigItem):
            add(DirectoryConfigControl(item))

    def finalize_layout(self):
        """ Set the layout in the dialog. This must be called after all of the items have been added (if doing
        manual layout), but doesn't need to be called by the user explicitly if auto_layout is used. """
        hbox_btns = self._make_dialog_buttons()

        vbox = QVBoxLayout()
        for group in self._groups:
            vbox.addWidget(group.assemble())
        vbox.addStretch()
        vbox.addLayout(hbox_btns)

        self.setLayout(vbox)
        self._update_options_display()

    def _make_dialog_buttons(self):
        """ Create the OK/Cancel/Apply/Reset buttons. """
        btn_cancel = QtGui.QPushButton("Cancel")
        btn_cancel.pressed.connect(self._dialog_close_cancel)
        btn_ok = QtGui.QPushButton("OK")
        btn_ok.pressed.connect(self._dialog_close_ok)
        btn_apply = QtGui.QPushButton("Apply")
        btn_apply.pressed.connect(self._dialog_apply_changes)
        btn_reset = QtGui.QPushButton("Reset All")
        btn_reset.pressed.connect(self._dialog_reset)

        hbox = QtGui.QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(btn_ok)
        hbox.addWidget(btn_cancel)
        hbox.addWidget(btn_apply)
        hbox.addWidget(btn_reset)
        hbox.addStretch(1)

        return hbox

    def _add_control(self, control):
        """ Add the specified control to the current group (create a new group if none exists). """
        if len(self._groups) == 0:
            self.start_group("Config Group")

        group = self._groups[-1]
        group.add_control(control)
        self._config_controls.append(control)

    def _update_options_display(self):
        """ Update all of the config controls from their backing ConfigItem object. """
        for control in self._config_controls:
            control.update_from_config()

    def _dialog_apply_changes(self):
        """ Save the current state of the options in the dialog to their backing ConfigItem objects"""
        for control in self._config_controls:
            control.save_to_config()

        self._config.save_to_file()
        self._update_options_display()

    def _dialog_close_ok(self):
        """ Apply and save any changes and close the dialog. """
        self._dialog_apply_changes()
        self.close()

    def _dialog_close_cancel(self):
        """ Close the dialog but don't save the changes. """
        self.close()

    def _dialog_reset(self):
        """ Reset the value of all options to their default values. """
        self._config.reset_all()
        self._update_options_display()


class _ConfigGroupBox:
    """ Layout grouping for config controls. Intended only for internal use by ConfigDialog. """
    def __init__(self, name):
        self._name = name
        self._controls = []

    def add_control(self, control):
        self._controls.append(control)

    def assemble(self):
        grp_box = QGroupBox(self._name)
        vbox = QVBoxLayout()
        for control in self._controls:
            vbox.addWidget(control)

        grp_box.setLayout(vbox)
        return grp_box


class ConfigControl(QWidget):
    """ Base class for config controls. When subclassing, be sure to implement both update_from_config()
    and save_to_config().

    """
    def __init__(self, item):
        super(ConfigControl, self).__init__()
        self._config_item = item
        self.setContentsMargins(0, 0, 0, 0)

    def update_from_config(self):
        """ Update the value displayed in the control by reading from the ConfigItem"""
        pass

    def save_to_config(self):
        """ Set the value of the ConfigItem to that displayed in this control. """
        pass


class ValueConfigControl(ConfigControl):
    TEXT_WIDTH = 100

    def __init__(self, config_item, txt_width=TEXT_WIDTH):
        ConfigControl.__init__(self, config_item)

        self._init_ui(txt_width)

    def _init_ui(self, txt_width):
        lbl_int = QLabel(self._config_item.tag())
        lbl_int.setFixedWidth(ConfigDialog.LABEL_WIDTH)

        self._txt_value = QLineEdit()
        self._txt_value.setFixedWidth(txt_width)

        hbox = QHBoxLayout()
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.addWidget(lbl_int)
        hbox.addWidget(self._txt_value)
        hbox.addWidget(QLabel(self._config_item.units()))
        hbox.addStretch()

        self.setLayout(hbox)

    def update_from_config(self):
        self._txt_value.setText(str(self._config_item.value()))

    def save_to_config(self):
        self._config_item.set(self._txt_value.text())


class BoolConfigControl(ConfigControl):
    def __init__(self, config_item):
        ConfigControl.__init__(self, config_item)

        self._init_ui()
        self.update_from_config()

    def _init_ui(self):
        lbl_bool = QLabel(self._config_item.tag())
        lbl_bool.setFixedWidth(ConfigDialog.LABEL_WIDTH)

        self._chk_box = QCheckBox()
        self._chk_box.setTristate(False)

        hbox = QHBoxLayout()
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.addWidget(lbl_bool)
        hbox.addWidget(self._chk_box)
        hbox.addStretch()

        self.setLayout(hbox)

    def update_from_config(self):
        state = 2 if self._config_item.value() == True else 0
        self._chk_box.setCheckState(state)

    def save_to_config(self):
        value = True if self._chk_box.checkState() == 2 else False
        self._config_item.set(value)


class EnumConfigControl(ConfigControl):
    def __init__(self, config_item):
        ConfigControl.__init__(self, config_item)

        self._init_ui()

    def _init_ui(self):
        lbl_enum = QLabel(self._config_item.tag())
        lbl_enum.setFixedWidth(ConfigDialog.LABEL_WIDTH)

        self._cmbo_enum = QComboBox()
        self._cmbo_enum.addItems(self._config_item.enum_names)

        selected = self._config_item.value()
        index = self._cmbo_enum.findText(selected, QtCore.Qt.MatchFixedString)
        self._cmbo_enum.setCurrentIndex(index)

        hbox = QHBoxLayout()
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.addWidget(lbl_enum)
        hbox.addWidget(self._cmbo_enum)
        hbox.addStretch()

        self.setLayout(hbox)

    def update_from_config(self):
        selected = self._config_item.value()
        index = self._cmbo_enum.findText(selected, QtCore.Qt.MatchFixedString)
        index = max(0, index)
        self._cmbo_enum.setCurrentIndex(index)

    def save_to_config(self):
        value = self._cmbo_enum.currentText()
        self._config_item.set(value)


class DirectoryConfigControl(ConfigControl):
    BUTTON_WIDTH = 80
    TEXT_WIDTH = 200

    def __init__(self, config_item):
        ConfigControl.__init__(self, config_item)

        self._init_ui()

    def _init_ui(self):
        self._txt_dir = QLineEdit()
        self._txt_dir.setFixedWidth(self.TEXT_WIDTH)

        lbl_dir = QLabel(self._config_item.tag())
        lbl_dir.setFixedWidth(ConfigDialog.LABEL_WIDTH)

        btn_show = QPushButton('View Files')
        btn_show.setFixedWidth(self.BUTTON_WIDTH)
        btn_show.clicked.connect(self._open_directory)

        hbox = QHBoxLayout()
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.addWidget(lbl_dir)
        hbox.addWidget(self._txt_dir)
        hbox.addWidget(btn_show)
        hbox.addStretch()

        self.setLayout(hbox)

    def update_from_config(self):
        self._txt_dir.setText(self._config_item.value())

    def save_to_config(self):
        self._config_item.set(self._txt_dir.text())

    def _open_directory(self):
        path = self._txt_dir.text()
        path = os.path.abspath(path)

        if sys.platform == 'win32':
            try:
                os.startfile(path)
            except OSError:
                QMessageBox.critical(self, "File Error", "Unable to find directory: '{}".format(path))
        else:
            QMessageBox.critical(self, "File Error", "Only available on Windows")


class ColorConfigControl(ConfigControl):
    STYLE = "background-color: {};"

    def __init__(self, config_item):
        ConfigControl.__init__(self, config_item)

        self._color = None

        self._init_ui()

    def _init_ui(self):
        lbl_color = QLabel(self._config_item.tag())
        lbl_color.setFixedWidth(ConfigDialog.LABEL_WIDTH)
        self._swatch = QPushButton("")
        self._swatch.setFixedWidth(25)
        self._swatch.clicked.connect(self._choose_color)

        hbox = QHBoxLayout()
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.addWidget(lbl_color)
        hbox.addWidget(self._swatch)
        hbox.addStretch()

        self.setLayout(hbox)

    def update_from_config(self):
        self._color = self._config_item.value()
        self.set_swatch_color(self._color)

    def save_to_config(self):
        self._config_item.set(self._color)

    def _choose_color(self):
        self._color = self._get_dialog_color(self._color)
        self.set_swatch_color(self._color)

    def set_swatch_color(self, color):
        self._swatch.setStyleSheet(self.STYLE.format(color.to_hex()))

    @staticmethod
    def _get_dialog_color(start_color):
        color = start_color

        qt_col = QtGui.QColorDialog.getColor(start_color.to_qt())
        if qt_col.isValid():
            color = Color.from_qt(qt_col)

        return color


