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
    points.extend([(100, 400), (200, 500), (300, 400), (500, 400), (500, 200), (400, 200), (100, 400)])
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
        p = points[pIndex]
        #westBorderPoints.append( (p[0]+(unitNormalVec[pIndex][0]*halfLineWidth), p[1])+(unitNormalVec[pIndex][1]*halfLineWidth) )
        #eastBorderPoints.append( (p[0]-(unitNormalVec[pIndex][0]*halfLineWidth), p[1])-(unitNormalVec[pIndex][1]*halfLineWidth) )

    # Calculate intersection points for east line segments (and then west)
    #for intersectionIndex in range(len(intersectionNormals)):

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
