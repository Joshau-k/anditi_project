
import geopandas as gpd
from dataset_accessor import DatasetAccessor

from road_boundary_functions import find_curves, find_line_gaps, find_nearby_opposite_angle_curves, find_nearby_same_angle_curves, find_pos_neg_neg_pos_curve_sequence

# dataset = "CZU60Q_2022_09_03__13_18_38_2"
# dataset = "CZU60Q_2020_12_09__16_05_47"
dataset = "CZU60P_2020_11_10__19_46_08"
tiff_file = f"../../anditi_task_description/{dataset}/density_rasters/081_ground.tif"
tiff = GeoTiff(tiff_file)
pixel = tiff.get_pixel(393584.27,6473686.72)

data_files_location = f"../../anditi_task_description/{dataset}"
data_accessor = DatasetAccessor(data_files_location)

for boundary_edge_file in ["left_boundary_edges", "right_boundary_edges"]:

    shp_db = gpd.read_file(
        f"{data_files_location}/road_boundary_edges/{boundary_edge_file}.shp"
    )

    line_file = f"road_boundary_edges/{boundary_edge_file}.shp"
    lines = data_accessor.load_line_strings(line_file)

    # gaps = find_line_gaps(left_lines)
    curves = find_curves(lines, 10)

    # nearby_same_curves = find_nearby_same_angle_curves(excess_curves, 100)
    # nearby_opposite_curves = find_nearby_opposite_angle_curves(excess_curves, 100)
    abba_curve_regions = find_pos_neg_neg_pos_curve_sequence(curves, 100)

    # data_accessor.write_line_strings(shp_db, gaps, "road_boundary_edges/left_gaps.shp")
    # data_accessor.write_polygons(shp_db, excess_curves, "road_boundary_edges/left_curves.shp")
    data_accessor.write_curves(shp_db, curves, f"road_boundary_edges/{boundary_edge_file}_curves.shp")
    data_accessor.write_polygons(shp_db, abba_curve_regions, f"road_boundary_edges/{boundary_edge_file}_problem_curves.shp")

    # data_accessor.write_polygons(shp_db, nearby_same_curves, f"road_boundary_edges/{boundary_edge_file}_same_angle_curves.shp")
    # data_accessor.write_polygons(shp_db, nearby_opposite_curves, f"road_boundary_edges/{boundary_edge_file}_opposite_angle_curves.shp")
