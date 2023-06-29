from osgeo import gdal
from osgeo import ogr
from qgis.core import QgsVectorLayer, QgsGeometry, QgsFeature, QgsVectorFileWriter

# Path to the EVI classified raster layer
raster_path = 'C:/Users/gis/Desktop/Healthy_Forest/Forest.tif'

# Path to the intermediate output shapefile
intermediate_output_path = 'C:/Users/gis/Desktop/Healthy_Forest/Forest.shp'

# Path to the final output shapefile
output_path = 'C:/Users/gis/Desktop/Healthy_Forest/Forest_simplified.shp'

# Open the raster layer using GDAL
raster_dataset = gdal.Open(raster_path)

# Create a vector layer in memory
memory_driver = ogr.GetDriverByName('Memory')
vector_dataset = memory_driver.CreateDataSource('mem_data_source')

# Create a new layer in the vector dataset
vector_layer = vector_dataset.CreateLayer('polygonized', None, ogr.wkbPolygon)

# Add a field to the layer
field_defn = ogr.FieldDefn("DN", ogr.OFTInteger)
vector_layer.CreateField(field_defn)

# Convert the raster to polygons and add them to the vector layer
gdal.Polygonize(raster_dataset.GetRasterBand(1), None, vector_layer, 0, [], callback=None)

# Get the first layer from the vector dataset
vector_layer = vector_dataset.GetLayer()

# Create a query to select the polygons of the third classification
query = '"DN" = 3'

# Apply the query to the layer
vector_layer.SetAttributeFilter(query)

# Export the selected features as polygons to the intermediate output file
driver = ogr.GetDriverByName('ESRI Shapefile')
driver.CopyDataSource(vector_dataset, intermediate_output_path)

# Cleanup
vector_dataset = None
raster_dataset = None

# Load the intermediate output shapefile as a QGIS vector layer
layer = QgsVectorLayer(intermediate_output_path, 'input_layer', 'ogr')

# Check if the layer loaded successfully
if not layer.isValid():
    print("Failed to load the input layer.")
else:
    # Create a new vector layer for the simplified geometries
    output_layer = QgsVectorLayer("Polygon", "output_layer", "memory")
    output_pr = output_layer.dataProvider()

    # Set the CRS for the output layer to match the input layer
    output_layer.setCrs(layer.crs())

    # Iterate over the features and simplify the geometries
    for feature in layer.getFeatures():
        geometry = feature.geometry()
        simplified_geometry = geometry.simplify(9000)  # Adjust the tolerance value as needed

        # Create a new feature with the simplified geometry
        output_feature = QgsFeature()
        output_feature.setGeometry(QgsGeometry.fromPolygonXY([simplified_geometry.asPolygon()[0]]))
        output_feature.setAttributes(feature.attributes())

        # Add the feature to the output layer's data provider
        output_pr.addFeatures([output_feature])

    # Save the output layer to the final output shapefile
    QgsVectorFileWriter.writeAsVectorFormat(output_layer, output_path, 'UTF-8', output_layer.crs(), 'ESRI Shapefile')

    # Cleanup
    del output_layer
