import math
import numpy as np
from qgis.core import (
    QgsGeometry,
    QgsProject,
    QgsRasterLayer,
    QgsPointXY,
    QgsField,
    QgsFeature,
    QgsWkbTypes,
    QgsFields,
    QgsVectorLayer,
    QgsFeature,
    QgsVectorDataProvider
)
from PyQt5.QtCore import QVariant
import csv
import os

'''
Calculation of elevation differences for terrain correction between the gravimetric station 
and the surrounding terrain, from the DEM, according to Hammer (1936, https://doi.org/10.1190/1.1440495).

Adjust the parameters inner_radius, outer_radius, and num_compartments to perform calculations for different rings in Hammer's net.

Inputs:
    Active Layer of Points
        A layer of points should be active in QGIS, where each point represents a gravimetric station.
        Note: Ensure this layer is active in QGIS before running the script and it is UTM projected.

    DEM Layers Group ("DEMs")
        DEM layers must be organized in a group called "DEMs" within the QGIS Layers Panel.
        Each DEM layer should cover the region around the points to be processed.
        Note: Ensure this layer is UTM projected.

    Parameters
        inner_radius (float): Inner radius of the rings in meters (e.g. 2, 16.6, 53.3)
        outer_radius (float): Outer radius of the rings in meters (e.g. 16.6, 53.5, 170.1)
        num_compartments (int): Number of compartments per ring (e.g. 4, 6, 6)


'''



inner_radius = 53.3  # Set the inner radius (in m)
outer_radius = 170.1 # Set the inner radius (in m)
num_compartments = 6  # Set the number of compartments

def get_DEMs(group_name):
    # Function to obtain all raster layers within the "DEMs" group
    dems = []
    root = QgsProject.instance().layerTreeRoot()
    group_dem = root.findGroup(group_name)
    
    if group_dem is None:
        print(f"The group '{group_name}' does not exist.")
        return dems

    for child in group_dem.children():
        if isinstance(child.layer(), QgsRasterLayer):
            dems.append(child.layer())
        else:
            print(f"The layer '{child.layer().name()}' is not a raster and will be ignored.")
    
    return dems

def get_DEM_point(dems, point):
    # Function to select the first DEM covering the point
    for dem in dems:
        extent = dem.extent()
        geom_dem = QgsGeometry.fromRect(extent)
        if geom_dem.contains(QgsGeometry.fromPointXY(point)):
            return dem
    return None

def get_height_dem(dem, point):
    # Function to get the DEM height for a specific point
    provider = dem.dataProvider()
    request = provider.identify(QgsPointXY(point), QgsRaster.IdentifyFormatValue)
    if request.isValid():
        for pixel_value in request.results().values():
            if pixel_value is not None:
                return pixel_value
    return None

def create_ring(center, inner_radius, outer_radius, num_compartments):
    # Function to create radial ring partitions
    init_angle = 0
    angle_per_compartment = 360 / num_compartments
    rings = []

    for i in range(num_compartments):
        # Create coordinates for the outer ring
        outer_circle = [
            QgsPointXY(
                center.x() + outer_radius * math.cos(math.radians(angle)),
                center.y() + outer_radius * math.sin(math.radians(angle))
            )
            for angle in range(int(init_angle), int(init_angle + angle_per_compartment) + 1, 1)
        ]
        
        # Create coordinates for the inner ring
        inner_circle = [
            QgsPointXY(
                center.x() + inner_radius * math.cos(math.radians(angle)),
                center.y() + inner_radius * math.sin(math.radians(angle))
            )
            for angle in reversed(range(int(init_angle), int(init_angle + angle_per_compartment) + 1, 1))
        ]
        
        # Update the initial angle for the next partition
        init_angle += angle_per_compartment

        # Combine outer and inner ring coordinates to form a closed polygon
        geom_externo = QgsGeometry.fromPolygonXY([outer_circle + inner_circle])
        rings.append(geom_externo)

    return rings
    
def export_attributes_to_csv():
    # Get the active layer
    layer = iface.activeLayer()

    # Ensure the active layer exists
    if not layer:
        print("No active layer found.")
        return
    
    # Ensure the active layer is a vector layer
    if layer.type() != QgsVectorLayer.VectorLayer:
        print(f"The active layer '{layer.name()}' is not a vector layer.")
        return

    # Get the path of the current QGIS project
    project_path = QgsProject.instance().fileName()
    if not project_path:
        print("Project not saved. Please save the project before running the script.")
        return

    # Set the output path to the same directory as the project file
    output_directory = os.path.dirname(project_path)
    csv_path = os.path.join(output_directory, f"{layer.name()}.csv")
    
    # Open the CSV file for writing
    with open(csv_path, mode='w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        
        # Write the column headers
        fields = [field.name() for field in layer.fields()]
        writer.writerow(fields)
        
        # Write each row from the attribute table
        for feature in layer.getFeatures():
            attributes = feature.attributes()
            writer.writerow(attributes)
    
    print(f"The attribute table has been successfully exported to '{csv_path}'.")

def process_rings(points_lyr, inner_radius, outer_radius, num_compartments):
    # Function to process the rings, create a new layer, and save results
    dem_lyr = get_DEMs('DEMs')
    
    if not dem_lyr:
        print("No DEM layers found in the specified group.")
        return

    print(f"The following DEM layers were found: {[dem.name() for dem in dem_lyr]}")

    points_lyr.startEditing()

    # Create a new vector layer for the rings
    crs = points_lyr.crs().authid()  # Get the EPSG of the points layer
    rings_layer_name = f"Rings_{inner_radius:.0f}_{outer_radius:.0f}"
    rings_layer = QgsVectorLayer(f'Polygon?crs={crs}', rings_layer_name, 'memory')
    provider_rings = rings_layer.dataProvider()
    provider_rings.addAttributes([QgsField("Name", QVariant.String), QgsField("Particion", QVariant.Int), 
                                   QgsField("d_Height", QVariant.Double), QgsField("n_pixels", QVariant.Int)])
    rings_layer.updateFields()

    # Create the columns before performing calculations
    for i in range(num_compartments):
        column_name = f"{inner_radius:.0f}_{outer_radius:.0f}_{num_compartments}.{i+1}"
        idx = points_lyr.fields().indexFromName(column_name)

        # If the column does not exist, create it
        if idx == -1:
            points_lyr.dataProvider().addAttributes([QgsField(column_name, QVariant.Double)])
            points_lyr.updateFields()

    for feature in points_lyr.getFeatures():
        center = feature.geometry().asPoint()

        dem_selected = get_DEM_point(dem_lyr, center)
        if not dem_selected:
            print(f"No DEM found covering the point {feature['Name']}.")
            continue

        altura_point = get_height_dem(dem_selected, center)
        if altura_point is None:
            print(f"Could not obtain height for the point {feature['Name']}.")
            continue

        rings = create_ring(center, inner_radius, outer_radius, num_compartments)

        for i, ring in enumerate(rings):
            # Get the DEM resolution
            resolution_x = dem_selected.rasterUnitsPerPixelX()
            resolution_y = dem_selected.rasterUnitsPerPixelY()

            # Iterate over each raster pixel in the polygon (ring) extent
            values_dem = []
            extent = ring.boundingBox()

            for x in np.arange(extent.xMinimum(), extent.xMaximum(), resolution_x):
                for y in np.arange(extent.yMinimum(), extent.yMaximum(), resolution_y):
                    pixel_point = QgsPointXY(x, y)
                    # Check if the pixel is within the ring
                    if ring.contains(QgsGeometry.fromPointXY(pixel_point)):
                        pixel_height = get_height_dem(dem_selected, pixel_point)
                        if pixel_height is not None:
                            values_dem.append(abs(pixel_height - altura_point))

            num_pixels = len(values_dem)

            # Save values in the previously created columns
            if values_dem:
                average_partition = round((sum(values_dem) / len(values_dem)), 1)
                column_name = f"{inner_radius:.0f}_{outer_radius:.0f}_{num_compartments}.{i+1}"
                idx = points_lyr.fields().indexFromName(column_name)

                if idx != -1:
                    points_lyr.changeAttributeValue(feature.id(), idx, average_partition)
                    print(f"Ring partition {i+1}/{num_compartments} created for point {feature['Name']} with average value {average_partition}.")
                    print(f"{num_pixels} pixels were used for the calculation in partition {i+1}/{num_compartments}.")

            # Create a new feature for the rings layer
            ring_feature = QgsFeature(rings_layer.fields())
            ring_feature.setGeometry(ring)
            ring_feature.setAttribute("Name", feature["Name"])
            ring_feature.setAttribute("Particion", i + 1)
            ring_feature.setAttribute("d_Height", average_partition if values_dem else None)
            ring_feature.setAttribute("n_pixels", num_pixels)
            provider_rings.addFeature(ring_feature)
    
    points_lyr.commitChanges()
    
    # Add the rings layer to the project
    QgsProject.instance().addMapLayer(rings_layer)
    


points_lyr = iface.activeLayer()

process_rings(points_lyr, inner_radius, outer_radius, num_compartments)

export_attributes_to_csv()
