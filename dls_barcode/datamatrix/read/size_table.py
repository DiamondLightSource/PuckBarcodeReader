class DatamatrixSizeError(Exception):
    pass


class DatamatrixSizeTable:
    """ Table of the sizes of datamatrix available including the number of bytes used for data
    and for error correction.

    Only square datamatrices are currently accounted for.

    See:
    http://www.gs1.org/docs/barcodes/GS1_DataMatrix_Guideline.pdf
        or
    http://www.codecorp.com/assets/white_paper/C001684-WhitePaper-DataMatrixECCLevels.pdf
    """

    # Square matrix size (including border): [num data bytes, num error bytes]
    CAPACITY = {
        10: [3, 5],
        12: [5, 7],
        14: [8, 10],
        16: [12, 12],
        18: [18, 14],
        20: [22, 18],
        22: [30, 20],
        24: [36, 24],
        26: [44, 28]
    }

    @staticmethod
    def valid_sizes():
        sizes = list(DatamatrixSizeTable.CAPACITY.keys())
        return sorted(sizes)

    @staticmethod
    def num_data_bytes(size):
        """ The number of bytes used to encode data in a square datamatrix of the specified size. """
        DatamatrixSizeTable.check_datamatrix_size(size)
        return DatamatrixSizeTable.CAPACITY[size][0]

    @staticmethod
    def num_error_bytes(size):
        """ The number of bytes used for error correction in a square datamatrix of the specified size. """
        DatamatrixSizeTable.check_datamatrix_size(size)
        return DatamatrixSizeTable.CAPACITY[size][1]

    @staticmethod
    def num_bytes(size):
        """ The total number of bytes encoded in a square datamatrix of the specified size. """
        DatamatrixSizeTable.check_datamatrix_size(size)
        return sum(DatamatrixSizeTable.CAPACITY[size])

    @staticmethod
    def check_datamatrix_size(size):
        if size not in DatamatrixSizeTable.CAPACITY:
            raise DatamatrixSizeError("Invalid or unimplemented datamatrix size: {}".format(size))
