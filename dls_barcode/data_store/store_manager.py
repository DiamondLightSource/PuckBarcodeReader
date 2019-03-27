from dls_barcode.data_store import Store
from dls_barcode.data_store.backup import Backup
from dls_barcode.data_store.comms_manager import CommsManager


class StoreManager:

    def __init__(self, directory, store_capacity, backup_time):
        self._store_capacity = store_capacity
        self._directory = directory
        self._backup_time = backup_time

    def create_store(self):
        comms_manager = self._create_store_comms_manager()
        backup_comms_manager = self._create_backup_comms_manager()
        backup = self._create_backup(backup_comms_manager)
        return Store(comms_manager, backup, self._store_capacity)

    def _create_store_comms_manager(self):
        return CommsManager(self._directory, "store")

    def _create_backup(self, backup_comms_manager):
        return Backup(backup_comms_manager, self._backup_time)

    def _create_backup_comms_manager(self):
        return CommsManager(self._directory, "backup")





