class FileManager:
    """Helper class to manage reading and writing files"""
    def read_lines(self, file_path):
        with open(file_path) as file:
            lines = file.readlines()

        return lines

    def write_items(self, file_path, items):
        with open(file_path, 'w') as file:
            for item in items:
                file.write(item)