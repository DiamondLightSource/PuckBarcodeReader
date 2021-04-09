import logconfig
import logging
import logging.handlers
import multiprocessing


class ProcessLogger(multiprocessing.Process):
    """Logging support for multiprocessing application
    Code taken from: https://stackoverflow.com/a/60831737
    """
    _global_process_logger = None

    def __init__(self):
        super().__init__()
        self.queue = multiprocessing.Queue(-1)

    @classmethod
    def get_global_logger(cls):
        if cls._global_process_logger is not None:
            return cls._global_process_logger
        raise Exception("No global process logger exists.")

    @classmethod
    def create_global_logger(cls):
        cls._global_process_logger = ProcessLogger()
        return cls._global_process_logger

    @staticmethod
    def configure():
        logconfig.setup_logging()

    def stop(self):
        logging.shutdown()
        self.queue.put_nowait(None)

    def run(self):
        self.configure()
        while True:
            try:
                record = self.queue.get()
                if record is None:
                    break
                logger = logging.getLogger(record.name)
                logger.handle(record)
            except Exception:
                import sys, traceback

                print("Problem:", file=sys.stderr)
                traceback.print_exc(file=sys.stderr)

    def new_process(self, target, args=[], kwargs={}):
        return ProcessWithLogging(self, target, args, kwargs)


def configure_new_process(log_process_queue):
    h = logging.handlers.QueueHandler(log_process_queue)
    root = logging.getLogger()
    root.addHandler(h)
    root.setLevel(logging.DEBUG)


class ProcessWithLogging(multiprocessing.Process):
    def __init__(self, target, args=[], kwargs={}, log_process=None):
        super().__init__()
        self.target = target
        self.args = args
        self.kwargs = kwargs
        if log_process is None:
            log_process = ProcessLogger.get_global_logger()
        self.log_process_queue = log_process.queue

    def run(self):
        configure_new_process(self.log_process_queue)
        self.target(*self.args, **self.kwargs)
