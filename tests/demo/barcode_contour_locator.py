""" This file gives an illustrated demonstration of process involved in
locating a datamatrix in an image. This isn't to be used as a test as it
re-implements some parts of the locator algorithm

"""
import cv2

from dls_util.image import Image, Color
from dls_util.shape import Point
from dls_barcode.datamatrix.locate.locate_contour import ContourLocator as CL


# Load the image file
folder = "./demo-resources/"
file = folder + "dm.png"
image_original = Image.from_file(file)

# Convert to a grayscale image
image_mono = image_original.to_grayscale()

# Perform adaptive threshold
block_size = 35
C = 16
image_threshold = CL._do_threshold(image_mono, block_size, C)

# Perform morphological close
close_size = 2
image_morphed = CL._do_close_morph(image_threshold, close_size)

# Find a bunch of contours in the image.
contours = CL._get_contours(image_morphed)
polygons = CL._contours_to_polygons(contours)

# Convert lists of vertices to lists of edges (easier to work with).
edge_sets1 = map(CL._polygons_to_edges, polygons)

# Discard all edge sets which probably aren't datamatrix perimeters.
edge_sets2 = list(filter(CL._filter_non_trivial, edge_sets1))
edge_sets3 = list(filter(CL._filter_longest_adjacent, edge_sets2))
edge_sets4 = list(filter(CL._filter_longest_approx_orthogonal, edge_sets3))
edge_sets5 = list(filter(CL._filter_longest_similar_in_length, edge_sets4))

# Convert edge sets to FinderPattern objects
fps = [CL._get_finder_pattern(es) for es in edge_sets5]


# Define drawing functions
def polygon_image(lines):
    blank = Image.blank(image_original.width, image_original.height, 3, 255)
    img = cv2.drawContours(blank.img, lines, -1, (0, 255, 0), 1)
    return Image(img)


def edges_image(edge_sets):
    blank = Image.blank(image_original.width, image_original.height, 3, 255)

    for shape in edge_sets:
        for edge in shape:
            print(edge[1])
            blank.draw_line(Point.from_array(edge[0]), Point.from_array(edge[1]), Color.Green(), 1)

    return blank


# Make images
image_contours = polygon_image(contours)
image_polygons = polygon_image(polygons)
image_filter1 = edges_image(edge_sets2)
image_filter2 = edges_image(edge_sets5)

# Make finder pattern image
image_fp = Image.blank(image_original.width, image_original.height, 3, 255)
fps[0].draw_to_image(image_fp)


# Popups
image_original.rescale(2).popup()
image_mono.rescale(2).popup()
image_threshold.rescale(2).popup()
image_morphed.rescale(2).popup()
image_contours.rescale(2).popup()
image_polygons.rescale(2).popup()
image_filter1.rescale(2).popup()
image_filter2.rescale(2).popup()
image_fp.rescale(2).popup()

# Save images
image_original.rescale(2).save_as(folder + "out_1_original.png")
image_mono.rescale(2).save_as(folder + "out_2_gray.png")
image_threshold.rescale(2).save_as(folder + "out_3_threshold.png")
image_morphed.rescale(2).save_as(folder + "out_4_morphed.png")
image_contours.rescale(2).save_as(folder + "out_5_contours.png")
image_polygons.rescale(2).save_as(folder + "out_6_polygons.png")
image_filter1.rescale(2).save_as(folder + "out_7_filter1.png")
image_filter2.rescale(2).save_as(folder + "out_8_filter2.png")
image_fp.rescale(2).save_as(folder + "out_9_pattern.png")

# Save image of finder pattern on original
fps[0].draw_to_image(image_original)
image_original.rescale(2).save_as(folder + "out_10_located.png")




