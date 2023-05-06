from pathlib import Path
import os
import rasterio
import rasterio.plot
import rasterio.merge
from typing import List
import tempfile

class GeoTiff:
    def __init__(self, data):
        self.tiff = data

    @classmethod
    def create_from_file(cls, file) -> 'GeoTiff':
        tiff = rasterio.open(file)
        return GeoTiff(tiff)

    # @classmethod
    # def combine(self, tiffs: List['GeoTiff'], folder):
    #     datasets = []
    #     for tiff in tiffs:
    #         datasets.append(tiff.tiff)
    #     combined, trans = rasterio.merge.merge(datasets)

    #     output_meta = tiff.tiff.meta.copy()
    #     output_meta.update(
    #         {"driver": "GTiff",
    #             "height": combined.shape[1],
    #             "width": combined.shape[2],
    #             "transform": trans,
    #         }
    #     )
    #     # rasterio.plot.show(combined, cmap='terrain')
    #     path = os.path.join(folder, "combined.tif")
    #     path = os.path.abspath(path)
    #     with rasterio.open(path, "w", **output_meta) as m:
    #         m.write(combined)

    #     return GeoTiff.create_from_file(path)
    #     # return CombinedGeoTiff(combined, trans)

    def get_pixel(self, x, y) -> float:
        """
            e.g. get_value(393584.27,6473686.72)
        """
        col, row = self.tiff.index(x,y)
        band = self.tiff.read(1)
        return band[col][row]

def open_all_geo_tiff_in_folder(folder: str) -> List[GeoTiff]:
    path = Path(folder)
    files = list(path.iterdir())
    all_geo_tiffs = []
    for file in files:
        if file.suffix != ".tif":
            continue
        tiff = rasterio.open(file)
        geo_tiff = GeoTiff(tiff)
        all_geo_tiffs.append(geo_tiff)

    return all_geo_tiffs

def find_geo_tiff_for_point(all_tiffs: List[GeoTiff], x, y) -> GeoTiff:
    for tiff in all_tiffs:
        bounds = tiff.tiff.bounds
        if x >= bounds.left and x <= bounds.right and y >= bounds.bottom and y <= bounds.top:
            return tiff
    return None