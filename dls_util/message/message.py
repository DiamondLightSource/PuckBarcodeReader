class Message:
    """A class that holds a message"""
    def __init__(self, type, content):
        self._type = type
        self._content = content

    def type(self):
        return self._type

    def content(self):
        return self._content