import cv2
import numpy as np
import math
import random

from dls_barcode.plate.transform import Transform


WHITE = (255,255,255)
RED = (0,0,255)
GREEN = (255,0,0)
BLUE = (0,255,0)

IMG_CENTER = (500, 400)

'''
Code to test/demo the Transform class
'''


def rad_to_deg(angle):
    return angle * 180 / math.pi

def draw_line(img, a, b, color, thickness=2):
    a = (int(a[0]+IMG_CENTER[0]), int(a[1]+IMG_CENTER[1]))
    b = (int(b[0]+IMG_CENTER[0]), int(b[1]+IMG_CENTER[1]))
    cv2.line(img, a, b, color, thickness)

def draw_circle(img, point, radius, color):
    point = (int(point[0]+IMG_CENTER[0]), int(point[1]+IMG_CENTER[1]))
    radius = int(radius)
    cv2.circle(img, point, radius, color, 2)

def draw_axes(img, length):
    # Draw axes
    x_neg = (-length,0)
    x_pos = (length,0)
    y_neg = (0,-length)
    y_pos = (0,length)

    draw_line(img, y_neg, y_pos, WHITE, 5)
    draw_line(img, x_neg, x_pos, WHITE, 5)


def TRIANGLE_DEMO():
    A = (143, 52)
    B = (17, 96.5)
    C = (0, 0)

    for i in range(10):
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

        draw_axes(image, 300)

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


def CIRCLES_DEMO():

    points = []
    for i in range(10):
        X = (random.random()) * 200
        Y = (random.random()) * 200
        points.append((X,Y))

    for i in range(10):
        angle = random.random() * 2 * math.pi
        scale = random.random() * 3
        delX = (random.random() - 0.5) * 200
        delY = (random.random() - 0.5) * 200

        trs = Transform(delX, delY, angle, scale )

        # Display on image
        image = np.zeros((800,1000,3), np.uint8)
        draw_axes(image, 300)

        radius = 10
        for p in points:
            draw_circle(image, p, radius, RED)
            draw_circle(image, trs.transform(p), radius*trs.zoom, BLUE)

        cv2.imshow('Barcode Scanner', image)
        cv2.waitKey(0)


TRIANGLE_DEMO()
CIRCLES_DEMO()



