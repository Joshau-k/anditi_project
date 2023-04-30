
from pathlib import Path
from typing import List
import geopandas as gpd
import shapely
import numpy as np

from road_boundary_functions import RoadCurve


class DatasetAccessor:
    def __init__(self, dataset_folder:str):
        self.dataset_folder = dataset_folder 

    def load_line_strings(self, file_path) -> List[shapely.LineString]:
        shp_db = gpd.read_file(
            f"{self.dataset_folder}/{file_path}"
        )

        left_edge_lines = [ln for ln in shp_db.geometry]
        # Convert lines coordinates to numpy array
        lines_coords = [np.array(ln.coords) for ln in left_edge_lines]
        # Convert numpy array to linestring and save to vector shape file
        rec_lines = [shapely.geometry.LineString(np_ln) for np_ln in lines_coords]

        return rec_lines
    
    def write_line_strings(self, shp_db, data:List[shapely.LineString], new_file_path:str) -> None:
        gpd.GeoDataFrame(
            geometry=data, crs=shp_db.crs
        ).to_file(
            Path(
            f"{self.dataset_folder}/{new_file_path}"
            ),
            index=False,
        )

    def write_polygons(self, shp_db, data:List[shapely.Polygon], new_file_path:str) -> None:
        # lines = []
        # for polygon in data:
        #     line = shapely.LineString(polygon.boundary)
        #     lines.append(line)
        gpd.GeoDataFrame(
            geometry=data, crs=shp_db.crs
        ).to_file(
            Path(
            f"{self.dataset_folder}/{new_file_path}"
            ),
            index=False,
        )

    def write_curves(self,  shp_db, curves:List[RoadCurve], new_file_path:str) -> None:
        polygons = []
        for curve in curves:
            polygons.append(curve.to_polygon())
        self.write_polygons(shp_db, polygons, new_file_path)