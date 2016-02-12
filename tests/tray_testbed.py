"""
Code to test the use of the tray class for continuous scanning of a
large set of barcodes.
"""
import math
import numpy as np

from dls_barcode.datamatrix import DataMatrix
from dls_barcode import CvImage
from dls_barcode.plate.tray import Tray
from dls_barcode.plate.transform import Transform, distance


def rad_to_deg(angle):
    return angle * 180 / math.pi


def stitch(tray_img, fragment_img, tray):
    """ Transform the fragment image appropriately and paste it onto the
    total combined image for the tray.
    """
    # Get transformation
    trans = tray.frame_transform
    print(trans)

    # Get raw image
    image = fragment_img.img

    # Resize image
    scaled = fragment_img.rescale(1/trans.zoom)

    # Rotate Image
    angle = trans.rot
    center = ((trans.x/trans.zoom),(trans.y/trans.zoom))
    rotated = scaled.rotate(angle, center)

    # Paste the transformed image in the correct location on the tray image
    x = IMG_OFFSET - ((trans.x) / trans.zoom)
    y = IMG_OFFSET - ((trans.y) / trans.zoom)
    tray_img.paste(rotated, x, y)

    return rotated


# File names
files_in = ['../test-images/tray_synth2_' + str(i) +'.png' for i in range(1,5)]
files_out = ['../test-output/tray-stitch_' + str(i) +'.png' for i in range(1,5)]
file_stitch = '../test-output/tray-stitch_aggregate.png'
file_rot_test = '../test-output/rot_test.png'


tray = Tray()
total_img = CvImage.blank(3000, 3000, 4, 255)
IMG_OFFSET = 500

for i in range(4):
    # Read image
    img = CvImage(files_in[i]).to_alpha()
    gray_image = img.to_grayscale().img

    # Locate barcodes
    finder_patterns = DataMatrix.LocateAllBarcodesInImage(gray_image)

    # Add barcodes to tray
    tray.new_frame(finder_patterns, gray_image)

    # Stitch images together
    img = stitch(total_img, img, tray)

    # Save image
    img.save_as(files_out[i])

    print("total nodes: {}".format(len(tray.nodes)))

# Draw the barcode locations on the image and save to file
tray.frame_transform = Transform(IMG_OFFSET, IMG_OFFSET, 0, 1)
tray.draw_highlights(total_img, CvImage.RED)
total_img.save_as(file_stitch)
