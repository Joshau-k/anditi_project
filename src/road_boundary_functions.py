from typing import List
from shapely import LineString, Polygon
import math


def find_line_gaps(lines: List[LineString]) -> List[LineString]:
    gaps:List[LineString] = []

    prev_line = None
    for line in lines:
        if prev_line is not None:
            if prev_line.coords[-1] != line.coords[0]:
                gap = LineString([prev_line.coords[-1], line.coords[0]])
                gaps.append(gap)

        prev_line = line

    return gaps

def find_excessive_curves(lines: List[LineString]) -> List[Polygon]:
    '''
        1.coordinate_scale 
        2.How to measure curviness
            a. Angle change per metre
            b. Sampled every line segment
        3.parameter for how much curviness is a problem
        4. What format to return result
    '''

    max_angle_degrees = 10

    problem_regions:List[Polygon] = []

    point1 = None
    point2 = None
    for line in lines:
        for point3 in line.coords:
            try:
                if point1 is None or point2 is None or point3 is None:
                    continue

                azimuth_deg1 = 360 + math.degrees(math.atan2((point1[0] - point2[0]),(point1[1] - point2[1])))
                azimuth_deg2 = 360 + math.degrees(math.atan2((point2[0] - point3[0]),(point2[1] - point3[1])))
                # direction1 = (point1[0] - point2[0])/(point1[1] - point2[1])
                # direction2 = (point2[0] - point3[0])/(point2[1] - point3[1])

                change_degrees = abs(azimuth_deg1-azimuth_deg2)

                if change_degrees > max_angle_degrees:
                    polygon_string = LineString([point1, point2, point3, point1])
                    problem_region = Polygon(
                        polygon_string
                    )
                    problem_regions.append(problem_region)
                
            finally:
                point1 = point2
                point2 = point3
        point1 = None
        point2 = None

    return problem_regions

   



