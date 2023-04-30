
import geopandas as gpd
from dataset_accessor import DatasetAccessor

from road_boundary_functions import find_excessive_curves, find_line_gaps, find_nearby_opposite_angle_curves, find_nearby_same_angle_curves

data_files_location = "../../anditi_task_description/CZU60P_2020_11_10__19_46_08"
data_accessor = DatasetAccessor(data_files_location)

shp_db = gpd.read_file(
    f"{data_files_location}/road_boundary_edges/left_boundary_edges.shp"
)

left_line_file = "road_boundary_edges/left_boundary_edges.shp"
left_lines = data_accessor.load_line_strings(left_line_file)

# gaps = find_line_gaps(left_lines)
excess_curves = find_excessive_curves(left_lines)

nearby_same_curves = find_nearby_same_angle_curves(excess_curves, 100)
nearby_opposite_curves = find_nearby_opposite_angle_curves(excess_curves, 100)

# data_accessor.write_line_strings(shp_db, gaps, "road_boundary_edges/left_gaps.shp")
# data_accessor.write_polygons(shp_db, excess_curves, "road_boundary_edges/left_curves.shp")
data_accessor.write_curves(shp_db, excess_curves, "road_boundary_edges/left_curves.shp")
data_accessor.write_polygons(shp_db, nearby_same_curves, "road_boundary_edges/left_same_angle_curves.shp")
data_accessor.write_polygons(shp_db, nearby_opposite_curves, "road_boundary_edges/left_opposite_angle_curves.shp")
