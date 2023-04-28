from typing import List
from shapely import LineString


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


