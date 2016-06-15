import math
import random

from dls_barcode.util import Image, Color
from dls_barcode.util.transform import Transform

IMG_CENTER = (500, 400)


def rad_to_deg(angle):
    """Convert an angle in radians into degrees"""
    return angle * 180 / math.pi


def draw_axes(img, length):
    # Draw axes
    x_neg = (-length, 0)
    x_pos = (length, 0)
    y_neg = (0, -length)
    y_pos = (0, length)

    img.draw_line(y_neg, y_pos, Color.White(), 5)
    img.draw_line(x_neg, x_pos, Color.White(), 5)


def TRIANGLE_DEMO():
    """ Draw a set of axes and a triangle. Perform a series of random transformations
     on the triangle and display the results.
    """
    A = (143, 52)
    B = (17, 96.5)
    C = (0, 0)

    for i in range(10):
        # Create random transformation
        angle = random.random() * 2 * math.pi
        scale = random.random() * 3
        delX = (random.random() - 0.5) * 200
        delY = (random.random() - 0.5) * 200
        transform = Transform(delX, delY, angle, scale)

        # Transform the triangle
        A_ = transform.transform(A)
        B_ = transform.transform(B)
        C_ = transform.transform(C)

        # From the line A-B and the transformed line A'-B', determine what the transformation was
        # This should be the same as the original transformation
        trans_calc = Transform.line_mapping(A, B, A_, B_)
        print("Angle: {0:.2f}; {1:.2f}".format(rad_to_deg(angle), rad_to_deg(trans_calc.rot)))
        print("Trans: ({0:.2f},{1:.2f}); ({2:.2f},{3:.2f})".format(delX, delY, trans_calc.x, trans_calc.y))
        print("Zoom: {0:.2f}; {1:.2f}".format(scale, trans_calc.zoom))

        # Display on image
        image = Image.blank(1000, 800)
        image.draw_offset = IMG_CENTER
        draw_axes(image, 300)

        # Draw original triangle
        image.draw_line(A, B, Color.Red(), 5)
        image.draw_line(C, B, Color.Red(), 5)
        image.draw_line(A, C, Color.Red(), 5)

        #Draw transformed triangle
        image.draw_line(A_, B_, Color.Green())
        image.draw_line(A_, C_, Color.Green())
        image.draw_line(C_, B_, Color.Green())

        # Check that the reverse transformation works properly
        A__ = transform.reverse(A_)
        B__ = transform.reverse(B_)
        C__ = transform.reverse(C_)

        # Draw the reverse transformation - this should overlap the origianl triangle
        image.draw_line(A__, B__, Color.Green(), 1)
        image.draw_line(A__, C__, Color.Green(), 1)
        image.draw_line(C__, B__, Color.Green(), 1)

        # Write the transformation on the image
        image.draw_text(transform.__str__(), (-450, 350), Color.White(), centered=False, scale=0.5, thickness=1)

        # Show the image
        image.popup()


def CIRCLES_DEMO():
    """ Draw a set of axes and a random set of circles. Perform a series of
    random transformations on the circles.
    """
    # Create a set of random circles
    points = []
    for i in range(10):
        X = (random.random()) * 200
        Y = (random.random()) * 200
        points.append((X,Y))

    for i in range(10):
        # Create random transformation
        angle = random.random() * 2 * math.pi
        scale = random.random() * 3
        delX = (random.random() - 0.5) * 200
        delY = (random.random() - 0.5) * 200
        trs = Transform(delX, delY, angle, scale)

        # Display on image
        image = Image.blank(1000, 800)
        image.draw_offset = IMG_CENTER
        draw_axes(image, 300)

        # Draw the circles and transformed circles on the image
        radius = 10
        for p in points:
            image.draw_circle(p, radius, Color.Red())
            image.draw_circle(trs.transform(p), radius * trs.zoom, Color.Blue())

        # Write the transformation on the image
        image.draw_text(trs.__str__(), (-450, 350), Color.White(), centered=False, scale=0.5, thickness=1)

        # Show the image
        image.popup()


TRIANGLE_DEMO()
CIRCLES_DEMO()



