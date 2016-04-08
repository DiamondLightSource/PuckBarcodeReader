"""
Code to test the use of the tray class for continuous scanning of a
large set of barcodes.
"""
import math

from dls_barcode import Image
from dls_barcode.datamatrix import DataMatrix
from dls_barcode.plate.geometry_tray import Tray
from dls_barcode.util.transform import Transform


def rad_to_deg(angle):
    return angle * 180 / math.pi


def stitch(tray_img, fragment_img, tray):
    """ Transform the fragment image appropriately and paste it onto the
    total combined image for the tray.
    """
    # Get transformation
    trans = tray.frame_transform
    print(trans)

    # Resize image
    scaled = fragment_img.rescale(1/trans.zoom)

    # Rotate Image
    angle = trans.rot

    if FREE_ROTATION:
        rotated = scaled.rotate_no_clip(angle)

        '''
        image_center = (trans.x/trans.zoom+scaled.width/2, trans.y/trans.zoom+scaled.height/2)
        trans_image_center = Transform._rotate(image_center, trans.rot)
        rot_offset = (trans_image_center[0]-rotated.width/2, trans_image_center[1]-rotated.height/2)
        x = IMG_OFFSET - rot_offset[0]
        y = IMG_OFFSET - rot_offset[1]
        '''

        # I think these two lines are correct
        off = (scaled.width/2-(trans.x/trans.zoom), scaled.height/2-(trans.y/trans.zoom))
        rot = Transform._rotate(off, trans.rot)

        # Still very slightly off compared to the other image
        offX = -(trans.x/trans.zoom) - (rot[0]-off[0]) - (rotated.width-scaled.width) / 2
        offY = -(trans.y/trans.zoom) - (rot[1]-off[1]) - (rotated.height-scaled.height) / 2


        x = IMG_OFFSET + offX
        y = IMG_OFFSET + offY
        print("off: {}, rot: {}, offX: {}, offY: {}".format(off,rot,offX,offY))

    else:
        center = ((trans.x/trans.zoom),(trans.y/trans.zoom))
        rotated = scaled.rotate(angle, center)
        x = IMG_OFFSET - (trans.x / trans.zoom)
        y = IMG_OFFSET - (trans.y / trans.zoom)


    # Paste the transformed image in the correct location on the tray image
    tray_img.paste(rotated, x, y)

    return rotated


# File names
files_in = ['../test-images/tray_synth2_' + str(i) +'.png' for i in range(1,5)]
files_out = ['../test-output/tray-stitch_' + str(i) +'.png' for i in range(1,5)]
file_stitch = '../test-output/tray-stitch_aggregate.png'


tray = Tray()
total_img = Image.blank(1500, 1500, 4, 255)
IMG_OFFSET = 100
FREE_ROTATION = True

for i in range(4):
    # Read image
    img = Image(files_in[i]).to_alpha()
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
tray.draw_highlights(total_img, Image.RED)
total_img.draw_dot((IMG_OFFSET,IMG_OFFSET), Image.RED, thickness=10)
total_img.save_as(file_stitch)
