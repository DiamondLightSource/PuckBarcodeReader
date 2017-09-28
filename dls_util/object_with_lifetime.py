import time


class ObjectWithLifetime:
    """ Abstract base class. Has a specified lifetime.
    """
    def __init__(self, lifetime):
        self._lifetime = lifetime
        self._start_time = time.time()

    def has_expired(self):
        return (time.time() - self._start_time) > self._lifetime