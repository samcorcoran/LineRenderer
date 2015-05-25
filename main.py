from pyglet.gl import *
import random
import math
from itertools import chain
import numpy as np
import utils

drawOriginalPoints = True
drawOriginalLines = True
fixedWidthBordersEnabled = False
drawFixedWidthAtIntersectionBorder = False
drawVectors = False
drawEastMitrePointLines = False
drawEastMitreConstructionLines = False
drawWestMitrePointLines = False
drawWestMitreConstructionLines = False
drawMitring = True # Only takes effect if drawEastMitrePointLines is also true
drawRoundedMitring = True # Draws thick triangle strip and rounds corners

batch = pyglet.graphics.Batch()

xMax = 600
yMax = 600

numBevelDivisions = 1 #MUST BE ODD

numPoints = 3
points = list()
lineVecs = list()
lineNormals = list()

westBorderPoints = list()
eastBorderPoints = list()

eastIntersectionPoints = list()
westIntersectionPoints = list()

# Points lists for mitring triangles sequence
eastPoints = list()
eastConstructionLines = list()
westPoints = list()
westConstructionLines = list()

lineWidth = 70
halfLineWidth = lineWidth/2

def createInitialPoints():
    # Manual points
    points.extend([np.array([100, 400]), np.array([200, 500]), np.array([300, 400]), np.array([350,550]), np.array([375,400]), np.array([500, 400]), np.array([500, 200]), np.array([400, 200])])
    utils.printPoints("Initial points", points)

def drawInitialPoints():
    pointCols = [255, 0, 0] * len(points)
    points_vertex_list = batch.add(len(points), pyglet.gl.GL_POINTS, next(utils.renderGroupGenerator),
        ('v2f/static', list(chain.from_iterable(points))),
        ('c3B/static', pointCols)
    )

def drawInitialLines():
    lineSegmentCols = [255, 255, 0] * (len(points))
    line_segments_vertex_list = batch.add(len(points), pyglet.gl.GL_LINE_LOOP, next(utils.renderGroupGenerator),
        ('v2f/static', list(chain.from_iterable(points))),
        ('c3B/static', lineSegmentCols)
    )

def calculateSegmentNormals():
    # Calculate line segment normals
    for pIndex in range(len(points)):
        #print("pIndex: ", pIndex)
        nextPIndex = (pIndex+1)%len(points)
        vec = points[nextPIndex] - points[pIndex]
        lineVecs.append(vec)
        print("Line vec")
        print(vec)
        unitNormalVec = utils.normalize(utils.perpendicular(vec))
        print("Unit normal vec:")
        print(unitNormalVec)
        lineNormals.append(unitNormalVec)
    utils.printPoints("line vectors", lineVecs)
    utils.printPoints("line normals", lineNormals)

def drawSegmentNormals():
    # Visualize normal
    for pIndex in range(len(points)):
        nextPIndex = (pIndex+1)%len(points)
        midpoint = (
            (points[pIndex][0] + points[nextPIndex][0])/2,
            (points[pIndex][1] + points[nextPIndex][1])/2
        )
        utils.drawVector(batch, midpoint, lineNormals[pIndex], [120,222,240])

def calculateFixedWidthBorderPoints():
    # Calc points for line width border
    for pIndex in range(len(points)):
        p = points[pIndex]
        wX = p[0]+(lineNormals[pIndex][0]*halfLineWidth)
        wY = p[1]+(lineNormals[pIndex][1]*halfLineWidth)
        westBorderPoints.append( (wX, wY) )
        westBorderPoints.append( (wX+lineVecs[pIndex][0], wY+lineVecs[pIndex][1]) )

        eX = p[0]-(lineNormals[pIndex][0]*halfLineWidth)
        eY = p[1]-(lineNormals[pIndex][1]*halfLineWidth)
        eastBorderPoints.append( (eX, eY) )
        eastBorderPoints.append( (eX+lineVecs[pIndex][0], eY+lineVecs[pIndex][1]) )

def drawFixedWidthBorder():
    west_vertex_list = batch.add(len(westBorderPoints), pyglet.gl.GL_POINTS, next(utils.renderGroupGenerator),
        ('v2f/static', list(chain.from_iterable(westBorderPoints))),
        ('c3B/static', [0, 255, 0, 100, 255, 50]*int(len(westBorderPoints)/2))
    )
    east_vertex_list = batch.add(len(eastBorderPoints), pyglet.gl.GL_POINTS, next(utils.renderGroupGenerator),
        ('v2f/static', list(chain.from_iterable(eastBorderPoints))),
        ('c3B/static', [0, 0, 255, 100, 50, 255]*int(len(eastBorderPoints)/2))
    )
    west_line_vertex_list = batch.add(len(westBorderPoints), pyglet.gl.GL_LINE_LOOP, next(utils.renderGroupGenerator),
        ('v2f/static', list(chain.from_iterable(westBorderPoints))),
        ('c3B/static', [0, 255, 0, 100, 255, 50]*int(len(westBorderPoints)/2))
    )
    east_line_vertex_list = batch.add(len(eastBorderPoints), pyglet.gl.GL_LINE_LOOP, next(utils.renderGroupGenerator),
        ('v2f/static', list(chain.from_iterable(eastBorderPoints))),
        ('c3B/static', [0, 0, 255, 100, 50, 255]*int(len(eastBorderPoints)/2))
    )

def drawFixedWidthAtIntersectionBorder():
    if drawFixedWidthAtIntersectionBorder:
        east_inters_vertex_list = batch.add(len(eastIntersectionPoints), pyglet.gl.GL_LINE_LOOP, None,
            ('v2f/static', list(chain.from_iterable(eastIntersectionPoints))),
            ('c3B/static', [255, 0, 0]*len(eastIntersectionPoints))
        )
        west_inters_vertex_list = batch.add(len(westIntersectionPoints), pyglet.gl.GL_LINE_LOOP, None,
            ('v2f/static', list(chain.from_iterable(westIntersectionPoints))),
            ('c3B/static', [200, 0, 0]*len(westIntersectionPoints))
        )

def calculateMitringPoints():
    # Loop over intersections
    # On inside of turn, find where entering/exiting lines meet, use point
    # On outside of turn...
    # * stop at same length of acute line
    # * next point is intersection normal, at dist of line width
    # * subdivide if desired
    for i in range(len(lineVecs)):
        #print("\ni = %d" % i)
        #print("ith Point: %f,%f" % (points[i][0], points[i][1]))
        prever = i-2
        prev = i-1
        current = i
        v1 = utils.normalize(lineVecs[prever])
        v2 = utils.normalize(lineVecs[prev])
        position = v1[0]*v2[1] - v1[1]*v2[0]
        if (position == 0):
            print("i=%d, straight ahead" % prever)
            # ignore points here... let prev vector dictate them
            continue
        elif (position > 0):
            # Left turn, west border is acute

            ## Calculate WEST acute points
            line1Norm = (lineNormals[prever][0]*halfLineWidth, lineNormals[prever][1]*halfLineWidth)
            wX1 = points[prever][0] + line1Norm[0]
            wY1 = points[prever][1] + line1Norm[1]
            # Vector from current point, into intersection
            v1 = (points[prev][0]-points[prever][0], points[prev][1]-points[prever][1])
            # Point on line parallel to line leaving intersection point
            line2Norm = (lineNormals[prev][0]*halfLineWidth, lineNormals[prev][1]*halfLineWidth)
            wX2 = points[current][0] + line2Norm[0]
            wY2 = points[current][1] + line2Norm[1]
            # Vector from point after intersection, pointing back into it
            v2 = (points[prev][0]-points[current][0], points[prev][1]-points[current][1])
            # Gives
            p1 = (wX1, wY1)
            p2 = (wX1+v1[0], wY1+v1[1])
            # and
            p3 = (wX2, wY2)
            p4 = (wX2+v2[0], wY2+v2[1])
            xInter, yInter = utils.calcLineIntersection(p1, p2, p3, p4)
            westPoints.append((xInter, yInter))
            westConstructionLines.extend([p1, p2, p3, p4])

            ## Calculate EAST obtuse points
            # Uses point i+1 (i.e. prev) as this process is working out the termination points for the end of the prev vector
            eX1 = points[prever][0] - line1Norm[0]
            eY1 = points[prever][1] - line1Norm[1]
            #drawVector(batch, points[prev], line1Norm)
            eX2 = points[current][0] - line2Norm[0]
            eY2 = points[current][1] - line2Norm[1]
            #drawVector(batch, points[current], line2Norm, (50, 50, 50))
            # Gives
            p1 = (eX1, eY1)
            p2 = (eX1+v1[0], eY1+v1[1])
            # and
            p3 = (eX2, eY2)
            p4 = (eX2+v2[0], eY2+v2[1])
            xInter, yInter = utils.calcLineIntersection(p1, p2, p3, p4)
            eastPoints.append((xInter, yInter))
            eastConstructionLines.extend([p1, p2])
        else:
            # Right turn, east border is acute

            ## Calculate EAST acute points
            # Inverted normal to get normal on east side
            line1Norm = (lineNormals[prever][0]*halfLineWidth, lineNormals[prever][1]*halfLineWidth)
            eX1 = points[prever][0]-line1Norm[0]
            eY1 = points[prever][1]-line1Norm[1]
            # Vector from current point, into intersection
            v1 = (points[prev][0]-points[prever][0], points[prev][1]-points[prever][1])
            # Point on line parallel to line leaving intersection point
            line2Norm = (lineNormals[prev][0]*halfLineWidth, lineNormals[prev][1]*halfLineWidth)
            eX2 = points[current][0]-line2Norm[0]
            eY2 = points[current][1]-line2Norm[1]
            # Vector from point after intersection, pointing back into it
            v2 = (points[prev][0]-points[current][0], points[prev][1]-points[current][1])
            # Gives
            p1 = (eX1, eY1)
            p2 = (eX1+v1[0], eY1+v1[1])
            # and
            p3 = (eX2, eY2)
            p4 = (eX2+v2[0], eY2+v2[1])
            xInter, yInter = utils.calcLineIntersection(p1, p2, p3, p4)
            eastPoints.append((xInter, yInter))
            eastConstructionLines.extend([p1, p2, p3, p4])

            ## Calculate WEST obtuse points
            # Uses point i+1 (i.e. prev) as this process is working out the termination points for the end of the prev vector
            wX1 = points[prever][0] + line1Norm[0]
            wY1 = points[prever][1] + line1Norm[1]
            #drawVector(batch, points[prev], line1Norm)
            wX2 = points[current][0] + line2Norm[0]
            wY2 = points[current][1] + line2Norm[1]
            #drawVector(batch, points[current], line2Norm, (50, 50, 50))
            # Gives
            p1 = (wX1, wY1)
            p2 = (wX1+v1[0], wY1+v1[1])
            # and
            p3 = (wX2, wY2)
            p4 = (wX2+v2[0], wY2+v2[1])
            xInter, yInter = utils.calcLineIntersection(p1, p2, p3, p4)
            westPoints.append((xInter, yInter))
            westConstructionLines.extend([p1, p2])

def drawMitreConstructionLines():
    if drawEastMitreConstructionLines:
        east_acute_construction_vertex_list = batch.add(len(eastConstructionLines), pyglet.gl.GL_LINES, next(utils.renderGroupGenerator),
            ('v2f/static', list(chain.from_iterable(eastConstructionLines))),
            ('c3B/static', [25, 180, 60]*len(eastConstructionLines))
        )
    if drawWestMitreConstructionLines:
        west_acute_construction_vertex_list = batch.add(len(westConstructionLines), pyglet.gl.GL_LINES, next(utils.renderGroupGenerator),
            ('v2f/static', list(chain.from_iterable(westConstructionLines))),
            ('c3B/static', [25, 180, 60]*len(westConstructionLines))
        )

def drawMitreLines():
    if drawEastMitrePointLines:
        east_acute_vertex_list = batch.add(len(eastPoints), pyglet.gl.GL_LINE_LOOP, next(utils.renderGroupGenerator),
            ('v2f/static', list(chain.from_iterable(eastPoints))),
            ('c3B/static', [200, 0, 0]*len(eastPoints))
        )

    if drawWestMitrePointLines:
        west_acute_vertex_list = batch.add(len(westPoints), pyglet.gl.GL_LINE_LOOP, next(utils.renderGroupGenerator),
            ('v2f/static', list(chain.from_iterable(westPoints))),
            ('c3B/static', [0, 0, 200]*len(westPoints))
        )

def drawMitringTriangles():
    if drawMitring:
        # Construct wide-line triangles
        # West triangles
        westTrianglePoints = list()
        for pIndex in range(len(points)):
            westTrianglePoints.append(points[pIndex-1])
            westTrianglePoints.append(westPoints[pIndex])
        westTrianglePoints.append(points[-1])
        westTrianglePoints.append(westPoints[0])
        col = list()
        for n in range(len(westTrianglePoints)):
            col.extend([random.randint(0,255), random.randint(0,255), random.randint(0,255)])
        west_acute_vertex_list = batch.add(len(westTrianglePoints), pyglet.gl.GL_TRIANGLE_STRIP, next(utils.renderGroupGenerator),
            ('v2f/static', list(chain.from_iterable(westTrianglePoints))),
            ('c3B/static', col)
        )
        # East triangles
        eastTrianglePoints = list()
        for pIndex in range(len(points)):
            eastTrianglePoints.append(points[pIndex-1])
            eastTrianglePoints.append(eastPoints[pIndex])
        eastTrianglePoints.append(points[-1])
        eastTrianglePoints.append(eastPoints[0])
        col = list()
        for n in range(len(eastTrianglePoints)):
            col.extend([random.randint(0,255), random.randint(0,255), random.randint(0,255)])
        east_acute_vertex_list = batch.add(len(eastTrianglePoints), pyglet.gl.GL_TRIANGLE_STRIP, next(utils.renderGroupGenerator),
            ('v2f/static', list(chain.from_iterable(eastTrianglePoints))),
            ('c3B/static', col)
        )


def createPoints():
    ## ROUNDED OBTUSE CORNERS
    # Loop over intersections
    # On inside of turn, find where entering/exiting lines meet, use point
    # On outside of turn...
    # * stop at same length of acute line
    # * next point is intersection normal, at dist of line width
    # * subdivide if desired
    eastPoints = list()
    eastConstructionLines = list()
    westPoints = list()
    westConstructionLines = list()
    for i in range(len(lineVecs)):
        #print("\ni = %d" % i)
        #print("ith Point: %f,%f" % (points[i][0], points[i][1]))
        prever = i-2
        prev = i-1
        current = i
        v1 = utils.normalize(lineVecs[prever])
        v2 = utils.normalize(lineVecs[prev])
        position = v1[0]*v2[1] - v1[1]*v2[0]
        if (position == 0):
            print("i=%d, straight ahead" % prever)
            # ignore points here... let prev vector dictate them
            continue
        elif (position > 0):
            # Left turn, west border is acute

            p1, p2, p3, p4 = utils.calcParallelLinePoints(halfLineWidth, points[prever], points[prev], points[current], eastSide=False)

            ## Calculate WEST acute points
            line1Norm = (lineNormals[prever][0]*halfLineWidth, lineNormals[prever][1]*halfLineWidth)
            # wX1 = points[prever][0] + line1Norm[0]
            # wY1 = points[prever][1] + line1Norm[1]
            # # Vector from current point, into intersection
            # v1 = (points[prev][0]-points[prever][0], points[prev][1]-points[prever][1])
            # # Point on line parallel to line leaving intersection point
            line2Norm = (lineNormals[prev][0]*halfLineWidth, lineNormals[prev][1]*halfLineWidth)
            # wX2 = points[current][0] + line2Norm[0]
            # wY2 = points[current][1] + line2Norm[1]
            # # Vector from point after intersection, pointing back into it
            # v2 = (points[prev][0]-points[current][0], points[prev][1]-points[current][1])
            # # Gives
            # p1 = (wX1, wY1)
            # p2 = (wX1+v1[0], wY1+v1[1])
            # # and
            # p3 = (wX2, wY2)
            # p4 = (wX2+v2[0], wY2+v2[1])
            xInter, yInter = utils.calcLineIntersection(p1, p2, p3, p4)
            westPoints.append((xInter, yInter))
            westConstructionLines.extend([p1, p2, p3, p4])

            ## Calculate EAST obtuse points
            # Outer corner fans out from point on line
            fanCentre = points[prev]
            # Uses point i+1 (i.e. prev) as this process is working out the termination points for the end of the prev vector
            eX1 = points[prever][0] - line1Norm[0]
            eY1 = points[prever][1] - line1Norm[1]
            #drawVector(batch, points[prev], line1Norm)
            eX2 = points[current][0] - line2Norm[0]
            eY2 = points[current][1] - line2Norm[1]
            #drawVector(batch, points[current], line2Norm, (50, 50, 50))
            # Gives
            p1 = (eX1, eY1) # Not required for calculation
            p2 = (eX1+v1[0], eY1+v1[1])
            # and
            p3 = (eX2, eY2) # Not required for calculation
            p4 = (eX2+v2[0], eY2+v2[1])
            # 'Cap' is straight line from p2 to p4
            capVec = (p4[0]-p2[0], p4[1]-p2[1])

            # DRAWS BLUE TO ENTRY
            #drawLine(fanCentre, p2, (0,0,200))
            # DRAWS WHITE TO EXIT
            #drawLine(fanCentre, p4)
            # DRAWS BROWN CAP
            #drawVector(batch, p2, capVec, (120,80,50))

            capDist = utils.mag(capVec)
            capNorm = utils.normalize(capVec)
            divGap = capDist / (numBevelDivisions+1)
            currentDiv = divGap
            #eastPoints.append(p2)

            # Temporary increasing colour for diagnosis
            colourIncrease = int(255/(numBevelDivisions+2))

            # The +2 is to include the start and end points too
            for dIndex in range(numBevelDivisions+2):
                # t is one minus the increment so triangle fan starts at correct end
                t = 1 - (1/(numBevelDivisions+1))*dIndex
                vX = fanCentre[0] - (p2[0]+capVec[0]*t)
                vY = fanCentre[1] - (p2[1]+capVec[1]*t)
                # Vector reaches straight line chord, but must be halfLineWidth long
                normalizedRadius = utils.normalize((vX, vY))
                x = fanCentre[0] + normalizedRadius[0]*halfLineWidth
                y = fanCentre[1] + normalizedRadius[1]*halfLineWidth

                # Draw diagnostic line for fan radii
                #print("Radius %d, increasing colour: %d" % (dIndex, colourIncrease))
                #drawLine(fanCentre, (x, y), [0, colourIncrease*(dIndex+1), 0])

                currentDiv += divGap
                # Append next fan-point location
                eastPoints.append((x, y))
                if dIndex%2 == 0 and dIndex != numBevelDivisions:
                    # Append fan centre
                    eastPoints.append(points[prev])
                    pass
                else:
                    # Append next fan-point location again to create degenerate triangles
                    eastPoints.append((x, y))

            eastConstructionLines.extend([p1, p2])
        else:
            # Right turn, east border is acute

            ## Calculate EAST acute points
            # Inverted normal to get normal on east side
            line1Norm = (lineNormals[prever][0]*halfLineWidth, lineNormals[prever][1]*halfLineWidth)
            eX1 = points[prever][0]-line1Norm[0]
            eY1 = points[prever][1]-line1Norm[1]
            # Vector from current point, into intersection
            v1 = (points[prev][0]-points[prever][0], points[prev][1]-points[prever][1])
            # Point on line parallel to line leaving intersection point
            line2Norm = (lineNormals[prev][0]*halfLineWidth, lineNormals[prev][1]*halfLineWidth)
            eX2 = points[current][0]-line2Norm[0]
            eY2 = points[current][1]-line2Norm[1]
            # Vector from point after intersection, pointing back into it
            v2 = (points[prev][0]-points[current][0], points[prev][1]-points[current][1])
            # Gives
            p1 = (eX1, eY1)
            p2 = (eX1+v1[0], eY1+v1[1])
            # and
            p3 = (eX2, eY2)
            p4 = (eX2+v2[0], eY2+v2[1])
            xInter, yInter = utils.calcLineIntersection(p1, p2, p3, p4)
            eastPoints.append((xInter, yInter))
            # Append point on entering line
            eastPoints.append((xInter+line1Norm[0], yInter+line1Norm[1]))
            eastPoints.append(points[prev])
            # Append a second time to create degenerate triangle
            eastPoints.append(points[prev])
            # Append intersection again
            eastPoints.append((xInter, yInter))
            # Append point on exiting line
            eastPoints.append((xInter+line2Norm[0], yInter+line2Norm[1]))
            eastConstructionLines.extend([p1, p2, p3, p4])

            ## Calculate WEST obtuse points
            # Uses point i+1 (i.e. prev) as this process is working out the termination points for the end of the prev vector
            wX1 = points[prever][0] + line1Norm[0]
            wY1 = points[prever][1] + line1Norm[1]
            #drawVector(batch, points[prev], line1Norm)
            wX2 = points[current][0] + line2Norm[0]
            wY2 = points[current][1] + line2Norm[1]
            #drawVector(batch, points[current], line2Norm, (50, 50, 50))
            # Gives
            p1 = (wX1, wY1)
            p2 = (wX1+v1[0], wY1+v1[1])
            # and
            p3 = (wX2, wY2)
            p4 = (wX2+v2[0], wY2+v2[1])
            xInter, yInter = utils.calcLineIntersection(p1, p2, p3, p4)
            westPoints.append((xInter, yInter))
            westConstructionLines.extend([p1, p2])
            pass

    if drawEastMitreConstructionLines:
        east_acute_construction_vertex_list = batch.add(len(eastConstructionLines), pyglet.gl.GL_LINES, next(utils.renderGroupGenerator),
            ('v2f/static', list(chain.from_iterable(eastConstructionLines))),
            ('c3B/static', [25, 180, 60]*len(eastConstructionLines))
        )
    if drawEastMitrePointLines:
        east_acute_vertex_list = batch.add(len(eastPoints), pyglet.gl.GL_LINE_LOOP, next(utils.renderGroupGenerator),
            ('v2f/static', list(chain.from_iterable(eastPoints))),
            ('c3B/static', [200, 0, 0]*len(eastPoints))
        )
    if drawWestMitreConstructionLines:
        west_acute_construction_vertex_list = batch.add(len(westConstructionLines), pyglet.gl.GL_LINES, next(utils.renderGroupGenerator),
            ('v2f/static', list(chain.from_iterable(westConstructionLines))),
            ('c3B/static', [25, 180, 60]*len(westConstructionLines))
        )
    if drawWestMitrePointLines:
        west_acute_vertex_list = batch.add(len(westPoints), pyglet.gl.GL_LINE_LOOP, next(utils.renderGroupGenerator),
            ('v2f/static', list(chain.from_iterable(westPoints))),
            ('c3B/static', [0, 0, 200]*len(westPoints))
        )

    if drawRoundedMitring:
        #Construct wide-line triangles
        # # West triangles
        # westTrianglePoints = list()
        # for pIndex in range(len(points)):
        #     westTrianglePoints.append(points[pIndex-1])
        #     westTrianglePoints.append(westPoints[pIndex])
        # westTrianglePoints.append(points[-1])
        # westTrianglePoints.append(westPoints[0])
        # col = list()
        # for n in range(len(westTrianglePoints)):
        #     col.extend([random.randint(0,255), random.randint(0,255), random.randint(0,255)])
        # west_acute_vertex_list = batch.add(len(westTrianglePoints), pyglet.gl.GL_TRIANGLE_STRIP, next(utils.renderGroupGenerator),
        #     ('v2f/static', list(chain.from_iterable(westTrianglePoints))),
        #     ('c3B/static', col)
        # )
        #East triangles
        eastTrianglePoints = list()
        for pIndex in range(len(eastPoints)):
            #eastTrianglePoints.append(points[pIndex-1])
            eastTrianglePoints.append(eastPoints[pIndex])
        eastTrianglePoints.append(eastPoints[0])
        eastTrianglePoints.append(eastPoints[1])

        col = list()
        for n in range(len(eastTrianglePoints)):
            #col.extend([random.randint(0,255), random.randint(0,255), random.randint(0,255)])
            col.extend([0.9,0,0,0.5])
        east_acute_vertex_list = batch.add(len(eastTrianglePoints), pyglet.gl.GL_TRIANGLE_STRIP, next(utils.renderGroupGenerator),
            ('v2f/static', list(chain.from_iterable(eastTrianglePoints))),
            ('c4f/static', col)
        )
        pass

class GameWindow(pyglet.window.Window):
    def __init__(self, *args, **kwargs):
        pyglet.window.Window.__init__(self, *args, **kwargs)

    def on_draw(self):
        self.clear()
        batch.draw()

    def update(self, deltaTime):
        pass

if __name__ == '__main__':
    print("Running app")
    window = GameWindow(xMax, yMax, caption="LineRenderer", resizable=True, vsync=False)
    # Pyglet FPS Overlay
    fps_display = pyglet.clock.ClockDisplay()
    # Call update 120 per second
    pyglet.clock.schedule_interval(window.update, 1/120.0)

    # Generate point data
    createInitialPoints()
    calculateSegmentNormals()
    calculateFixedWidthBorderPoints()
    createPoints()
    calculateMitringPoints()

    if drawOriginalPoints:
        drawInitialPoints()

    # Draws initially input line whose points are held in 'points' list
    if drawOriginalLines:
        drawInitialLines()

    # For each line-segment connecting pairs of original/initial points, a small white line is drawn
    #  to indicate the normal for that segment.
    if drawVectors:
        drawSegmentNormals()

    # Fixed width border draws straight lines on both sides of the original sequence of points
    #  at a fixed width from it. This acts as a guide to show roughly where the 'thick line' would
    #  be drawn. These are just aides though.
    if fixedWidthBordersEnabled:
        drawFixedWidthBorder()

    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_BLEND)

    pyglet.app.run()
    print("Ran app")
