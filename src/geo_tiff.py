import rasterio
import rasterio.plot

class GeoTiff:
    def __init__(self, file):
        self.tiff = rasterio.open(file)

    def get_pixel(self, x, y) -> float:
        """
            e.g. get_value(393584.27,6473686.72)
        """
        col, row = self.tiff.index(x,y)
        band = self.tiff.read(1)
        return band[col][row]


