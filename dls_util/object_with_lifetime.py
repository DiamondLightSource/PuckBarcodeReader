import time


class ObjectWithLifetime:
    """ Abstract base class. Has a specified lifetime.
    """
    def __init__(self, lifetime):
        """A lifetime of 0 indicates that the object does not expire"""
        self._lifetime = lifetime
        self._start_time = time.time()

    def has_expired(self):
        if self._lifetime == 0:
            return False

        return (time.time() - self._start_time) > self._lifetime
