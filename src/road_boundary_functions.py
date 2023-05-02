from typing import List, Tuple
from shapely import LineString, Polygon, Point, distance
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

def find_curves(lines: List[LineString], min_angle_degrees=10) -> List[List['RoadCurve']]:
    '''
        1.coordinate_scale 
        2.How to measure curviness
            a. Angle change per metre
            b. Sampled every line segment
        3.parameter for how much curviness is a problem
        4. What format to return result
    '''

    # problem_regions:List[Polygon] = []
    all_lines_curves:List[List[RoadCurve]] = []


    point1 = None
    point2 = None
    for line in lines:
        line_curves:List[RoadCurve] = []
        current_curve:RoadCurve = None

        for point3 in line.coords:
            try:
                if point1 is None or point2 is None or point3 is None:
                    continue

                azimuth_deg1 = 360 + math.degrees(math.atan2((point1[0] - point2[0]),(point1[1] - point2[1])))
                azimuth_deg2 = 360 + math.degrees(math.atan2((point2[0] - point3[0]),(point2[1] - point3[1])))
                # direction1 = (point1[0] - point2[0])/(point1[1] - point2[1])
                # direction2 = (point2[0] - point3[0])/(point2[1] - point3[1])

                change_degrees = abs(azimuth_deg1-azimuth_deg2)

                if change_degrees > min_angle_degrees:
                    if current_curve is None:
                        current_curve = RoadCurve([point1, point2, point3])
                        line_curves.append(current_curve)
                    else:
                        if current_curve.does_point_fit_curve(point3, min_angle_degrees):
                            #Extend existing curve
                            current_curve.extend(point3)
                        else:
                            #Start new curve
                            current_curve = RoadCurve([point1, point2, point3])
                            line_curves.append(current_curve)
                else:
                    current_curve = None

                        
            except Exception as ex:
                raise ex
            finally:
                point1 = point2
                point2 = point3
        point1 = None
        point2 = None
        if line_curves:
            all_lines_curves.append(line_curves)

    return all_lines_curves

def find_pos_neg_neg_pos_curve_sequence(road_curves : List[List['RoadCurve']], max_distance:float) -> List[Polygon]:
    """
        Find a sequence of 4 curves with angle in the pattern:
            - positive, negative, negative, positive
            or
            - negative, positive, positive, negative
    """
    
    problem_regions: List[Polygon] = []
    for line_curves in road_curves:
        if len(line_curves) >=3:
            curve1 = line_curves[0]
            curve2 = line_curves[1]
            curve3 = line_curves[2]
        for curve4 in line_curves[3:]:
            try:
                if distance(curve1.to_polygon(), curve4.to_polygon()) > max_distance:
                    continue
                if (
                    (curve1.net_angle() > 0 and curve2.net_angle() < 0 and curve3.net_angle() < 0 and curve4.net_angle() > 0)
                    or (curve1.net_angle() < 0 and curve2.net_angle() > 0 and curve3.net_angle() > 0 and curve4.net_angle() < 0)
                ):
                    combined_polygon = combine_polygons(curve1.to_polygon(), curve2.to_polygon(), curve3.to_polygon(), curve4.to_polygon())
                    problem_regions.append(combined_polygon)
            except Exception as ex:
                raise ex
            finally:
                curve1 = curve2
                curve2 = curve3
                curve3 = curve4

    return problem_regions

def find_nearby_opposite_angle_curves(road_curves : List['RoadCurve'], max_distance:float) -> List[Polygon]:
    problem_regions: List[Polygon] = []
    for line_curves in road_curves:
        prev_curve = line_curves[0]
        for current_curve in line_curves[1:]:
            try:
                if distance(prev_curve.to_polygon(), current_curve.to_polygon()) > max_distance:
                    continue
                if (prev_curve.net_angle() > 0 and current_curve.net_angle() < 0) or (prev_curve.net_angle() < 0 and current_curve.net_angle() > 0):
                    combined_polygon = combine_polygons(prev_curve.to_polygon(), current_curve.to_polygon())
                    problem_regions.append(combined_polygon)
            except Exception as ex:
                raise ex
            finally:
                prev_curve = current_curve

    return problem_regions

def find_nearby_same_angle_curves(road_curves : List['RoadCurve'], max_distance:float) -> List[Polygon]:
    problem_regions: List[Polygon] = []
    for line_curves in road_curves:
        prev_curve = line_curves[0]
        for current_curve in line_curves[1:]:
            try:
                if distance(prev_curve.to_polygon(), current_curve.to_polygon()) > max_distance:
                    continue
                if (prev_curve.net_angle() > 0 and current_curve.net_angle() > 0) or (prev_curve.net_angle() < 0 and current_curve.net_angle() < 0):
                    combined_polygon = combine_polygons(prev_curve.to_polygon(), current_curve.to_polygon())
                    problem_regions.append(combined_polygon)

            except Exception as ex:
                raise ex
            finally:
                prev_curve = current_curve

    return problem_regions

def combine_polygons(*polygons:Polygon)-> Polygon:
    min_x = polygons[0].boundary.coords[0][0]
    min_y = polygons[0].boundary.coords[0][1]
    max_x = polygons[0].boundary.coords[0][0]
    max_y = polygons[0].boundary.coords[0][1]

    for polygon in polygons[1:]:
        for point in polygon.boundary.coords[1:]:
            if point[0] < min_x:
                min_x = point[0]
            elif point[0] > max_x:
                max_x = point[0]

            if point[1] < min_y:
                min_y = point[1]
            elif point[1] > max_y:
                max_y = point[1]

    polygon = Polygon([(min_x, min_y), (min_x, max_y), (max_x, max_y), (max_x, min_y), (min_x, min_y)])
    return polygon


class RoadCurve:
    def __init__(self, points:List[Tuple[float, float]]):
        self.line = LineString(points)

    def does_point_fit_curve(self, point:Tuple[float, float], min_angle_degrees:float) -> bool:
        point1 = self.line.coords[-3]
        point2 = self.line.coords[-2]
        point3 = self.line.coords[-1]
        azimuth_dir1 = math.degrees(math.atan2((point1[0] - point2[0]),(point1[1] - point2[1])))
        azimuth_dir2 = math.degrees(math.atan2((point2[0] - point3[0]),(point2[1] - point3[1])))
        angle1 = azimuth_dir1-azimuth_dir2
        azimuth_dir3 = math.degrees(math.atan2((point3[0] - point[0]),(point3[1] - point[1])))
        angle2 = azimuth_dir2-azimuth_dir3

        if ((angle1 < 0 and angle2 < 0) or (angle1 > 0 and angle2 > 0)) and (abs(angle2) > min_angle_degrees):
            return True
        return False

    def extend(self, point:Tuple[float, float]):
        coords = list(self.line.coords)
        coords.append(point)
        self.line = LineString(coords)

    def net_angle(self) -> float:
        net_angle = 0
        point1 = None
        point2 = None
        for point3 in self.line.coords:
            try:
                if point1 is None or point2 is None or point3 is None:
                    continue

                azimuth_dir1 = math.degrees(math.atan2((point1[0] - point2[0]),(point1[1] - point2[1])))
                azimuth_dir2 = math.degrees(math.atan2((point2[0] - point3[0]),(point2[1] - point3[1])))
                net_angle += azimuth_dir1-azimuth_dir2
                
            except Exception as ex:
                raise ex
            finally:
                point1 = point2
                point2 = point3
        return net_angle

    def to_polygon(self):
        min_x = self.line.coords[0][0]
        min_y = self.line.coords[0][1]
        max_x = self.line.coords[0][0]
        max_y = self.line.coords[0][1]

        for point in self.line.coords[1:]:
            if point[0] < min_x:
                min_x = point[0]
            elif point[0] > max_x:
                max_x = point[0]

            if point[1] < min_y:
                min_y = point[1]
            elif point[1] > max_y:
                max_y = point[1]

        polygon = Polygon([(min_x, min_y), (min_x, max_y), (max_x, max_y), (max_x, min_y), (min_x, min_y)])
        return polygon


   



