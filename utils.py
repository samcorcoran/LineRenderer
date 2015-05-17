import math
import numpy as np
from pyglet.gl import *

def printPoints(listName, pointList):
    print("Printing list: %s" % listName)
    for p in pointList:
        print(p)

def normalize(vec):
    print("NORMALIZING VEC:")
    print(vec)
    print(vec[0])
    print(vec[1])
    magnitude = math.sqrt(vec[0]**2 + vec[1]**2)
    return np.array([vec[0]/magnitude, vec[1]/magnitude])

def perpendicular(vec):
    return np.array([-vec[1], vec[0]])

def mag(vec):
    return math.sqrt(vec[0]**2 + vec[1]**2)

def drawVector(batch, start, vector, col = [255,255,255], norm=False):
    v = 0
    if norm:
        v = normalize(vector)
    else:
        v = vector
    drawnLengthMultiplier = 20
    if not norm:
        drawnLengthMultiplier = 1
    batch.add(2, pyglet.gl.GL_LINES, None,
        ('v2f/static', [start[0], start[1], start[0]+v[0]*drawnLengthMultiplier, start[1]+v[1]*drawnLengthMultiplier]),
        ('c3B/static', col+col)
    )

def drawLine(batch, start, end, col = [255, 255, 255]):
    batch.add(2, pyglet.gl.GL_LINES, None,
        ('v2f/static', [start[0], start[1], end[0], end[1]]),
        ('c3B/static', col+col)
    )

def calcLineIntersection(p1, p2, p3, p4):
    # First line: Pa = p1 + u1(p2-p1)
    # Second line: Pb = p3 + u2(p4-p3)
    # Unknowns
    denominator = ((p4[1]-p3[1])*(p2[0]-p1[0]) - (p4[0]-p3[0])*(p2[1]-p1[1]))
    if denominator == 0:
        # Use 0, 0 as an obvious diagnostic indicator that something is wrong
        return 0, 0
    u1 = ((p4[0]-p3[0])*(p1[1]-p3[1]) - (p4[1]-p3[1])*(p1[0]-p3[0]))/denominator
    # Don't even need to calculate the second, but here it is
    #u2 = ((p2[0]-p1[0])*(p1[1]-p3[1]) - (p2[1]-p1[1])*(p1[0]-p3[0]))/denominator
    x = p1[0]+(u1*(p2[0]-p1[0]))
    y = p1[1]+(u1*(p2[1]-p1[1]))
    # Notes:
    # If denominator is zero, lines are parallel
    # Intersection is for infinite lines. If line segment intersection is necessary
    #   must test if u1 and u2 are between 0 and 1.
    # This link was very helpful: http://paulbourke.net/geometry/pointlineplane/
    return x, y

def scaleVector(vec, length):
    normVec = normalize(vec)
    return (normVec[0]*length, normVec[1]*length)

def calcParallelLinePoints(offset, p1, p2, p3, eastSide):
   sign = -1 if eastSide else 1
   # Vector entering p2 from p1
   v1 = p2 - p1
   print("v1, normal")
   print(v1)
   # Perpendicular vector on east/west side
   v1Normal = normalize(v1) * offset
   print(v1Normal)
   # Vector entering p2 from p3
   v2 = p2 - p3
   # Perpendicular vector on east/west side
   v2Normal = normalize(v2) * offset
   a1 = p1 + v1Normal
   a2 = a1 + v1
   b1 = p2 + v2Normal
   b2 = b1 + v2
   return a1, a2, b1, b2