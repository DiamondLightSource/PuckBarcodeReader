from ..image import Color
from .config import Config


class ConfigItem:
    """ Represents a single option/configuration item which is essentially a name/value pair.
    This class should be sub-classed in order to handle different types of value.
    """

    OUTPUT_LINE = line = "{}" + Config.DELIMITER + "{}\n"

    def __init__(self, tag, default):
        """ Initialize a new config item.

        Parameters
        ----------
        tag - The 'name' of this option, used as an identifier when saved to file and in the UI.
        default - the default value of this option.
        """
        self._value = None
        self._tag = tag
        self._default = default

    def value(self):
        """ Get the value of this option. """
        return self._value

    def set(self, value):
        """ Set the value of this option. """
        self._value = self._clean(value)

    def tag(self):
        """ Get the tag (string name) of this option. """
        return self._tag

    def reset(self):
        """ Set the value of this option to its default. """
        self._value = self._default

    def to_file_string(self):
        """ Creates a string representation that can be saved to and read from file. """
        return self.OUTPUT_LINE.format(self._tag, self._value)

    def from_file_string(self, value_string):
        """ Read the value from its string representation. """
        pass

    def _clean(self, value):
        """ Perform any additional cleanup/processing on the value. Implement in subclass if needed. """
        return value


class IntConfigItem(ConfigItem):
    """ Config item that stores an integer. Constructor may also take a 'units' parameter which is a
    string that represents the units of the value. This can be used in the UI.
    """
    def __init__(self, tag, default, units=""):
        ConfigItem.__init__(self, tag, default)
        self._units = units

    def units(self):
        """ The unit type of the value. """
        return self._units

    def from_file_string(self, string):
        self._value = self._clean(string)

    def _clean(self, value):
        try:
            return int(value)
        except ValueError:
            return self._default


class DirectoryConfigItem(ConfigItem):
    """ Config item that stores a directory path (can be relative or absolute). """
    def __init__(self, tag, default):
        ConfigItem.__init__(self, tag, default)

    def from_file_string(self, string):
        self._value = self._clean(string)

    def _clean(self, value):
        value = str(value).strip()
        # if not value.endswith("/"):
        #     value += "/"
        return value


class ColorConfigItem(ConfigItem):
    """ Config item that stores a color. """
    def __init__(self, tag, default):
        ConfigItem.__init__(self, tag, default)

    def from_file_string(self, string):
        self._value = Color.from_string(string)


class BoolConfigItem(ConfigItem):
    """ Config item that stores a boolean value. """
    def __init__(self, tag, default):
        ConfigItem.__init__(self, tag, default)

    def from_file_string(self, string):
        self._value = True if string.lower() == 'true' else False


class EnumConfigItem(ConfigItem):
    """ Config item that stores an enum value. Constructor takes parameter 'enum_names' which should
    be a list of strings."""
    def __init__(self, tag, default, enum_names):
        ConfigItem.__init__(self, tag, str(default))
        self.enum_names = [str(name) for name in enum_names]

        if self._default not in self.enum_names:
            self._default = self.enum_names[0]

    def from_file_string(self, string):
        self._value = self._clean(string)

    def _clean(self, value):
        value = str(value).strip()
        if value not in self.enum_names:
            value = self._default
        return value