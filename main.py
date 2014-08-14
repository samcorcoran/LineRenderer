import pyglet
import random
import math
from itertools import chain

batch = pyglet.graphics.Batch()

xMax = 600
yMax = 600

numPoints = 3
points = list()

lineWidth = 20
halfLineWidth = lineWidth/2

def printPoints(listName, pointList):
    print("Printing list: %s" % listName)
    for p in pointList:
        print(p)

def normalize(vec):
    magnitude = math.sqrt(vec[0]**2 + vec[1]**2)
    return (vec[0]/magnitude, vec[1]/magnitude)

def drawVector(start, vector, col = [255,255,255]):
    v = normalize(vector)
    drawnLength = 20
    batch.add(2, pyglet.gl.GL_LINES, None,
        ('v2f/static', [start[0], start[1], start[0]+v[0]*drawnLength, start[1]+v[1]*drawnLength]),
        ('c3B/static', col+col)
    )

def createPoints():
    # Manual points
    points.extend([(100, 400), (200, 500), (300, 400), (350,550), (375,400), (500, 400), (500, 200), (400, 200), (100, 400)])
    printPoints("Initial points", points)
    pointCols = [255, 0, 0] * len(points)
    points_vertex_list = batch.add(len(points), pyglet.gl.GL_POINTS, None,
        ('v2f/static', list(chain.from_iterable(points))),
        ('c3B/static', pointCols)
    )
    lineSegmentCols = [255, 255, 0] * (len(points))
    line_segments_vertex_list = batch.add(len(points), pyglet.gl.GL_LINE_LOOP, None,
        ('v2f/static', list(chain.from_iterable(points))),
        ('c3B/static', lineSegmentCols)
    )

    # Calculate line segment normals
    lineVecs = list()
    lineNormals = list()
    intersectionNormals = list()

    # Calc line segment normals
    for pIndex in range(len(points)):
        #print("pIndex: ", pIndex)
        if (pIndex == len(points)-1):
            continue
        vec = (points[pIndex+1][0] - points[pIndex][0], points[pIndex+1][1] - points[pIndex][1])
        lineVecs.append(vec)
        normalVec = (-vec[1], vec[0])
        unitNormalVec = normalize(normalVec)
        lineNormals.append(unitNormalVec)
        # Visualize normal
        midpoint = (
            (points[pIndex][0] + points[pIndex+1][0])/2,
            (points[pIndex][1] + points[pIndex+1][1])/2
        )
        drawVector(midpoint, unitNormalVec, [120,222,240])

    printPoints("line vectors", lineVecs)
    printPoints("line normals", lineNormals)

    # Calc intersection normals
    for lineIndex in range(len(lineVecs)):
        if (lineIndex == len(lineVecs)-1):
            continue
        xComp = lineNormals[lineIndex][0] + lineNormals[lineIndex+1][0]
        yComp = lineNormals[lineIndex][1] + lineNormals[lineIndex+1][1]
        intersectionNormal = normalize((xComp, yComp))
        intersectionNormals.append(intersectionNormal)
        # Visualize normal
        drawVector(points[lineIndex+1], intersectionNormal, [200,250,150])


    printPoints("intersection normals", intersectionNormals)

    # Calc points for line width border
    westBorderPoints = list()
    eastBorderPoints = list()
    for pIndex in range(len(points)):
        if (pIndex == len(points)-1):
            continue
        p = points[pIndex]
        wX = p[0]+(lineNormals[pIndex][0]*halfLineWidth)
        wY = p[1]+(lineNormals[pIndex][1]*halfLineWidth)
        westBorderPoints.append( (wX, wY) )
        westBorderPoints.append( (wX+lineVecs[pIndex][0], wY+lineVecs[pIndex][1]) )

        eX = p[0]-(lineNormals[pIndex][0]*halfLineWidth)
        eY = p[1]-(lineNormals[pIndex][1]*halfLineWidth)
        eastBorderPoints.append( (eX, eY) )
        eastBorderPoints.append( (eX+lineVecs[pIndex][0], eY+lineVecs[pIndex][1]) )
    west_vertex_list = batch.add(len(westBorderPoints), pyglet.gl.GL_POINTS, None,
        ('v2f/static', list(chain.from_iterable(westBorderPoints))),
        ('c3B/static', [0, 255, 0, 100, 255, 50]*int(len(westBorderPoints)/2))
    )
    east_vertex_list = batch.add(len(eastBorderPoints), pyglet.gl.GL_POINTS, None,
        ('v2f/static', list(chain.from_iterable(eastBorderPoints))),
        ('c3B/static', [0, 0, 255, 100, 50, 255]*int(len(eastBorderPoints)/2))
    )
    west_line_vertex_list = batch.add(len(westBorderPoints), pyglet.gl.GL_LINE_LOOP, None,
        ('v2f/static', list(chain.from_iterable(westBorderPoints))),
        ('c3B/static', [0, 255, 0, 100, 255, 50]*int(len(westBorderPoints)/2))
    )
    east_line_vertex_list = batch.add(len(eastBorderPoints), pyglet.gl.GL_LINE_LOOP, None,
        ('v2f/static', list(chain.from_iterable(eastBorderPoints))),
        ('c3B/static', [0, 0, 255, 100, 50, 255]*int(len(eastBorderPoints)/2))
    )

    # Print whether line is making left or right turns
    for i in range(len(lineVecs)):
        if i == len(lineVecs)-1:
            continue
        v1 = normalize(lineVecs[i])
        v2 = normalize(lineVecs[i+1])
        position = v1[0]*v2[1] - v1[1]*v2[0]
        if (position == 0):
            print("i=%d, straight ahead" % i)
        elif (position > 0):
            print("i=%d, left turn" % i)
        else:
            print("i=%d, right turn" % i)

    # Calculate intersection points for east line segments (and then west) using normal offsets from corners
    eastIntersectionPoints = list()
    westIntersectionPoints = list()
    for i in range(len(intersectionNormals)):
        eastIntersection = (points[i+1][0] - intersectionNormals[i][0]*halfLineWidth, points[i+1][1] - intersectionNormals[i][1]*halfLineWidth)
        eastIntersectionPoints.append(eastIntersection)
        westIntersection = (points[i+1][0] + intersectionNormals[i][0]*halfLineWidth, points[i+1][1] + intersectionNormals[i][1]*halfLineWidth)
        westIntersectionPoints.append(westIntersection)
    east_inters_vertex_list = batch.add(len(eastIntersectionPoints), pyglet.gl.GL_LINE_LOOP, None,
        ('v2f/static', list(chain.from_iterable(eastIntersectionPoints))),
        ('c3B/static', [255, 0, 0]*len(eastIntersectionPoints))
    )
    west_inters_vertex_list = batch.add(len(westIntersectionPoints), pyglet.gl.GL_LINE_LOOP, None,
        ('v2f/static', list(chain.from_iterable(westIntersectionPoints))),
        ('c3B/static', [200, 0, 0]*len(westIntersectionPoints))
    )


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
    window = GameWindow(xMax, yMax, caption="Hexagons", resizable=True, vsync=False)
    # Pyglet FPS Overlay
    fps_display = pyglet.clock.ClockDisplay()
    # Call update 120 per second
    pyglet.clock.schedule_interval(window.update, 1/120.0)
    # Generate point data
    createPoints()
    pyglet.app.run()
    print("Ran app")
