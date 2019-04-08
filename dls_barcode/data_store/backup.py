class Backup:

    """
    Backup class maintains the short time backaup of records which is kept in the same folder as the store files.
    """

    def __init__(self, comms_man):
        self._comms = comms_man

    def backup_records(self, to_back):
        self._comms.to_csv_file(to_back)


