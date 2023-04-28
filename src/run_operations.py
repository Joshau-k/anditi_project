
import geopandas as gpd
from dataset_accessor import DatasetAccessor

from road_boundary_functions import find_line_gaps

data_files_location = "../../anditi_task_description/CZU60P_2020_11_10__19_46_08"
data_accessor = DatasetAccessor(data_files_location)

shp_db = gpd.read_file(
    f"{data_files_location}/road_boundary_edges/left_boundary_edges.shp"
)

left_line_file = "road_boundary_edges/left_boundary_edges.shp"
left_lines = data_accessor.load_line_strings(left_line_file)

gaps = find_line_gaps(left_lines)

data_accessor.write_line_strings(shp_db, gaps, "road_boundary_edges/left_gaps.shp")
