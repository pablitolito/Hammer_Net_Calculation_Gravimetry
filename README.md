# Hammer_Net_Calculation_Gravimetry.py

This QGIS Python script calculates the elevation differences between the gravimetric stations and the surrounding terrain, usind data from a Digital Elevation Models (DEMs).
It follows Hammer's method (1936, https://doi.org/10.1190/1.144049) by generating concentric rings around each station and dividing each ring into radial compartments to compute elevation averages.

Adjust the parameters inner_radius, outer_radius, and num_compartments to perform calculations for different rings in Hammer's net.

![imagen](https://github.com/user-attachments/assets/68343b0e-04c2-46ea-a11c-d56d39df7f05)

## Inputs

1. **Active Layer of Points**  
   - A layer of points should be active in QGIS, where each point represents a gravimetric station.
   - **Note**: Ensure this layer is active in QGIS before running the script and it is UTM projected

2. **DEM Layers Group ("DEMs")**  
   - DEM layers must be organized in a group called `"DEMs"` within the QGIS Layers Panel.
   - Each DEM layer should cover the region around the points to be processed.
   - **Note**: Ensure this layer UTM projected

3. **Parameters**  
   - `inner_radius` (float): Inner radius of the rings in meters.
   - `outer_radius` (float): Outer radius of the rings in meters.
   - `num_compartments` (int): Number of compartments per ring.

## Outputs

1. **Updated Points Layer**  
   - Adds new fields to the points layer, with each field representing the average elevation difference (divided by 2) for each ring compartment.

2. **Rings Layer**  
   - Creates a new polygon layer representing the concentric rings with compartments around each point.
   - Each compartment includes the following attributes:
     - **Name**: The point's name.
     - **Partition**: The compartment number within the ring.
     - **d_Height/2**: Average elevation difference (divided by 2).
     - **n_pixels**: Number of DEM pixels used in each compartment for the calculations.

## Usage Notes

- Ensure all layers, including the points and DEMs, use the same coordinate reference system (CRS) and they are in UTM.
- This script should be run within the QGIS Python console or as part of a QGIS plugin.

---

