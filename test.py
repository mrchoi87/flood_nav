from shapely.geometry import Point, Polygon

poly = Polygon([(0,0), (0,10), (10,10), (10,0)])
pt_inside = Point(5,5)
pt_outside = Point(15,5)

print(pt_inside.within(poly))  # True
print(pt_outside.within(poly)) # False