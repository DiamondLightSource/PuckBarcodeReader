import cv2
import numpy as np
import math
import random

from dls_barcode.plate.transform import Transform


def rad_to_deg(angle):
    return angle * 180 / math.pi

def draw_line(img, a, b, color, thickness=2):
    a = (int(a[0]+500), int(a[1]+400))
    b = (int(b[0]+500), int(b[1]+400))
    cv2.line(img, a, b, color, thickness)


WHITE = (255,255,255)
RED = (0,0,255)
GREEN = (255,0,0)
BLUE = (0,255,0)


A = (143, 52)
B = (17, 96.5)
C = (0, 0)

for i in range(20):
    angle = random.random() * 2 * math.pi
    scale = random.random() * 3
    delX = (random.random() - 0.5) * 200
    delY = (random.random() - 0.5) * 200

    transform = Transform(delX, delY, angle, scale)

    A_ = transform.transform(A)
    B_ = transform.transform(B)
    C_ = transform.transform(C)

    trans_calc = Transform.line_mapping(A, B, A_, B_)

    print("Angle: {0:.2f}; {1:.2f}".format(rad_to_deg(angle), rad_to_deg(trans_calc.rot)))
    print("Trans: ({0:.2f},{1:.2f}); ({2:.2f},{3:.2f})".format(delX, delY, trans_calc.x, trans_calc.y))
    print("Zoom: {0:.2f}; {1:.2f}".format(scale, trans_calc.zoom))


    # Display on image
    image = np.zeros((800,1000,3), np.uint8)

    # Draw axes
    x_neg = (-300,0)
    x_pos = (300,0)
    y_neg = (0,-300)
    y_pos = (0,300)

    draw_line(image, y_neg, y_pos, WHITE, 5)
    draw_line(image, x_neg, x_pos, WHITE, 5)

    # Draw Transformed Axes
    #draw_line(image, trans_calc.transform(y_neg), trans_calc.transform(y_pos), WHITE, 2)
    #draw_line(image, trans_calc.transform(x_neg), trans_calc.transform(x_pos), WHITE, 2)

    # Draw original triangle
    draw_line(image, A, B, RED, 5)
    draw_line(image, C, B, RED, 5)
    draw_line(image, A, C, RED, 5)

    #Draw transformed triangle
    draw_line(image, A_, B_, GREEN)
    draw_line(image, A_, C_, GREEN)
    draw_line(image, C_, B_, GREEN)

    # Check that the reverese transformation works properly
    A__ = transform.reverse(A_)
    B__ = transform.reverse(B_)
    C__ = transform.reverse(C_)

    draw_line(image, A__, B__, GREEN, 1)
    draw_line(image, A__, C__, GREEN, 1)
    draw_line(image, C__, B__, GREEN, 1)

    cv2.imshow('Barcode Scanner', image)
    cv2.waitKey(0)



