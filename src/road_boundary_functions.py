from typing import List, Tuple
from shapely import LineString, Polygon, Point, distance
import math

from geo_tiff import GeoTiff, find_geo_tiff_for_point


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

def find_curves(lines: List[LineString]) -> List[List['RoadCurve']]:
    '''
        1.coordinate_scale 
        2.How to measure curviness
            a. Angle change per metre
            b. Sampled every line segment
        3.parameter for how much curviness is a problem
        4. What format to return result
    '''
    all_lines_curves:List[List[RoadCurve]] = []

    min_segment_angle_degrees = 1
    min_total_angle_degrees = 30


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

                change_degrees = abs(azimuth_deg1-azimuth_deg2)

                if change_degrees > min_segment_angle_degrees:
                    if current_curve is None:
                        current_curve = RoadCurve([point1, point2, point3])
                    else:
                        if current_curve.does_point_fit_curve(point3, min_segment_angle_degrees):
                            #Extend existing curve
                            current_curve.extend(point3)
                        else:
                            if abs(current_curve.net_angle()) > min_total_angle_degrees:
                                line_curves.append(current_curve)

                            #Start new curve
                            current_curve = RoadCurve([point1, point2, point3])
                else:
                    if current_curve and abs(current_curve.net_angle()) > min_total_angle_degrees:
                        line_curves.append(current_curve)
                    current_curve = None

                        
            except Exception as ex:
                raise ex
            finally:
                point1 = point2
                point2 = point3
        point1 = None
        point2 = None
        if current_curve and abs(current_curve.net_angle()) > min_total_angle_degrees:
            line_curves.append(current_curve)
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

def add_section_if_meets_threshold(all_sections, section, current_height_change, min_avg_height_change, min_total_height_change) -> bool:
    if section is None:
        return False
    if section and abs(current_height_change)/len(section.line.coords) > min_avg_height_change and abs(current_height_change) > min_total_height_change:
        all_sections.append(section)
        return True
    return False

def find_height_change(lines: List[LineString], height_files: List[GeoTiff]) -> List['RoadCurve']:

    line_sections:List[RoadSection] = []

    min_total_height_change = 1.00
    min_avg_height_change = 0.05
    min_step_height_change = 0.01

    point1 = None
    point2 = None
    for line in lines:
        current_curve:RoadSection = None
        current_height_change = 0
        point_iter = iter(line.coords)
        point2 = next(point_iter)
        while point2:
        # for point2 in line.coords:
            try:
                local_tiff = find_geo_tiff_for_point(height_files, point2[0], point2[1])
                if local_tiff is None:
                    add_section_if_meets_threshold(line_sections, current_curve, current_height_change, min_avg_height_change, min_total_height_change)
                    current_curve = None
                    current_height_change = 0
                    continue
                height2_metres = local_tiff.get_pixel(point2[0], point2[1])
                if point1 is None:
                    add_section_if_meets_threshold(line_sections, current_curve, current_height_change, min_avg_height_change, min_total_height_change)
                    current_curve = None
                    current_height_change = 0
                    continue
                if height1_metres == -1000 or height2_metres == -1000:
                    add_section_if_meets_threshold(line_sections, current_curve, current_height_change, min_avg_height_change, min_total_height_change)
                    current_curve = None
                    current_height_change = 0
                    continue
                # line_length = Point(point2[0], point2[1]).distance(Point(point1[0], point1[1]))
                height_changes = height1_metres - height2_metres
                if abs(height_changes) > min_step_height_change:
                    if current_curve is None:
                        current_curve = RoadCurve([point1, point2])
                        current_height_change = height_changes
                    else:
                        if (current_height_change > 0 and height_changes > 0) or (current_height_change < 0 and height_changes < 0):
                            current_curve.extend(point2)
                            current_height_change += height_changes
                        else:
                            add_section_if_meets_threshold(line_sections, current_curve, current_height_change, min_avg_height_change, min_total_height_change)
                            current_curve = RoadCurve([point1, point2])
                            current_height_change = height_changes
                else:
                    add_section_if_meets_threshold(line_sections, current_curve, current_height_change, min_avg_height_change, min_total_height_change)
                    current_curve = None
                    current_height_change = 0

            except Exception as ex:
                raise ex
            finally:
                point1 = point2
                height1_metres = height2_metres
                try:
                    point2 = next(point_iter)
                except StopIteration:
                    point2 = None
        point1 = None
        height1_metres = None
        add_section_if_meets_threshold(line_sections, current_curve, current_height_change, min_avg_height_change, min_total_height_change)
    return line_sections


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

class RoadSection(RoadCurve):
    pass
   



