import os


class Config:
    """ Class for making simple persistent config/options for a program. To use, you should subclass
    and call the add() method for each option to be added and then call the initialize_from_file()
    method to load the saved options from the specified config file:
        >>> class MyConfig(Config):
        >>>     def __init__(self, file):
        >>>         Config.__init__(self, file)
        >>>
        >>>         self.int_option1 = self.add(IntConfigItem, "Int Option", default=35)
        >>>         self.dir_option1 = self.add(DirectoryConfigItem, "Dir Option", default="../my_dir/")
        >>>         self.color_option1 = self.add(ColorConfigItem, "Color Option", Color.Red())
        >>>
        >>>         self.initialize_from_file()
    The type of the config item supplied as the first argument to add() determines how the item
    behaves (any formatting done, how it is read from and print to file, etc). To add handling for new
    custom types, subclass ConfigItem and override the appropriate functions.

    Note to access the value of an option from a client class, call the value() method of the item.:
        >>> my_config.dir_option1.value()

    The ConfigDialog class is also provided, which is intended to be used with this class in order to
    create simple Qt4 Dialog windows for editing these options.
    """

    DELIMITER = "="

    def __init__(self, file):
        self._file = file
        self._items = []

    def initialize_from_file(self):
        """ Open and parse the config file provided in the constructor. This should only be called after
        the relevant ConfigItems hasve been set up by adding them with add(). """
        self.reset_all()
        self._load_from_file(self._file)

    def add(self, cls, tag, default, extra_arg=None):
        """ Add a new option of a specified type to this config.

        Parameters
        ----------
        cls - The config type; should be subclass of ConfigItem
        tag - the text string that uniquely labels this option, will appear in file and config dialog
        default - The default value for this option
        extra_arg - Additional argument required by some ConfigItems
        """
        if extra_arg is None:
            item = cls(tag, default)
        else:
            item = cls(tag, default, extra_arg)
        self._items.append(item)
        return item

    def reset_all(self):
        """ Set the value of every option to its default. """
        for item in self._items:
            item.reset()

    def save_to_file(self):
        """ Save the current options to the config file specified in the constructor. """
        with open(self._file, 'w') as f:
            for item in self._items:
                f.write(item.to_file_string())

    def _load_from_file(self, file):
        """ Load options from the config file specified in the constructor. """
        if not os.path.isfile(file):
            self.save_to_file()
            return

        with open(file) as f:
            lines = f.readlines()
            for line in lines:
                try:
                    self._parse_line(line)
                except ValueError:
                    pass

    def _parse_line(self, line):
        """ Parse a line from a config file, setting the value of the relevant option. """
        tokens = line.strip().split(Config.DELIMITER)
        tag, value = tuple(tokens)
        for item in self._items:
            if tag == item.tag():
                item.from_file_string(value)
                break
