from PyQt5.QtWidgets import QVBoxLayout, QGroupBox, QPushButton, QHBoxLayout, QDialog

from .control import *
from .item import *


class ConfigDialog(QDialog):
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
        """ Create the OK/Cancel/Reset buttons. """
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setAutoDefault(False)
        btn_cancel.pressed.connect(self._dialog_close_cancel)
        btn_ok = QPushButton("OK")
        btn_ok.setAutoDefault(False)
        btn_ok.pressed.connect(self._dialog_close_ok)
        btn_reset = QPushButton("Reset All")
        btn_reset.setAutoDefault(False)
        btn_reset.pressed.connect(self._dialog_reset)

        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(btn_ok)
        hbox.addWidget(btn_cancel)
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

    def _all_changes_confirmed(self):
        """ Confirm that the user is happy with all changes. """
        return all(ctrl.is_confirmed for ctrl in self._config_controls)

    def _dialog_apply_changes(self):
        """ Save the current state of the options in the dialog to their backing ConfigItem objects. """
        for control in self._config_controls:
            control.save_to_config()

        self._config.save_to_file()
        self._update_options_display()

    def _dialog_close_ok(self):
        """ Apply and save any changes and close the dialog. """
        for control in self._config_controls:
            control.before_apply()

        if not self._all_changes_confirmed():
            return

        self._dialog_apply_changes()
        self.accept()

    def _dialog_close_cancel(self):
        """ Close the dialog but don't save the changes. """
        self.reject()

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
