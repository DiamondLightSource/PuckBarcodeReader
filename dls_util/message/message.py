from dls_util.object_with_lifetime import ObjectWithLifetime

class Message(ObjectWithLifetime):
    """A class that holds a message"""
    def __init__(self, type, content, lifetime=2):
        ObjectWithLifetime.__init__(self, lifetime)
        self._type = type
        self._content = content

    def type(self):
        return self._type

    def content(self):
        return self._content
