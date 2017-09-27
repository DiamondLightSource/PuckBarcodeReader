import os


class FileManager:
    """Helper class to manage reading and writing files"""
    def read_lines(self, file_path):
        with open(file_path) as file:
            lines = file.readlines()

        return lines

    def write_lines(self, file_path, lines):
        """Calls file.writelines, so doesn't append any new line characters"""
        with open(file_path, 'w') as file:
            file.writelines(lines)

    def is_file(self, path):
        return os.path.isfile(path)

    def is_dir(self, path):
        return os.path.isdir(path)

    def make_dir(self, path):
        os.makedirs(path)

    def remove(self, path):
        os.remove(path)