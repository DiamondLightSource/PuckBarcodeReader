import os


class FileManager:
    """Helper class to manage reading and writing files"""
    def read_lines(self, file_path):
        with open(file_path) as file:
            lines = file.readlines()

        return lines

    def write_lines(self, file_path, lines):
        with open(file_path, 'w') as file:
            for item in lines:
                file.write(item)

    def exists(self, file):
        return os.path.isfile(file)