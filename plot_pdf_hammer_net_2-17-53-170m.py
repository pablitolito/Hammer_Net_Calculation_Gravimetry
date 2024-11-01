#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct 27 21:21:59 2024

@author: pablo
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
import os

'''
This Python script reads the CSV table generated by Hammer_Net_Calculation_Gravimetry.py script
after calculating three internal rings (from 2 to 17, 17 to 53, and 53 to 170 meters),
divided into 4 quadrants for the innermost ring and 6 for each of the other two. 
The program creates a Hammer_net chart for each gravimetric station, 
displaying the absolute height differences (halved) between each quadrant 
and the central gravimetric station.

Input:
    a csv file coming from Hammer_Net_Calculation_Gravimetry.py
    you can change the name of the file_name
Outup:
    a pdf file with a Hammer net for each gravimetric station




'''
# Open the Excel file
file_name = 'Input_points_etrs89_utm30.csv'

# Check if the file exists
if not os.path.exists(file_name):
    raise FileNotFoundError(f"The file '{file_name}' was not found.")

data = pd.read_csv(file_name)

# Settings for generating charts
num_stations = len(data)
stations_per_page = 6
cols_per_page = 2
rows_per_page = 3
page_count = (num_stations // stations_per_page) + (1 if num_stations % stations_per_page != 0 else 0)

# Figure size in inches for A4 size
fig_width, fig_height = 8.27, 11.69  # A4 in inches (21 cm x 29.7 cm)

def plot_circle_with_partitions(ax, radius, values, num_partitions, angle_offset=0, inner_radius=0):
    """Draw radial partitions of a circle from an inner to an outer radius and place the values."""
    angle_step = 2 * np.pi / num_partitions
    for i, value in enumerate(values):
        angle = i * angle_step
        ax.plot([inner_radius * np.cos(angle), radius * np.cos(angle)],
                [inner_radius * np.sin(angle), radius * np.sin(angle)], color='black')
        ax.text(radius * 0.75 * np.cos(angle + angle_offset),
                radius * 0.75 * np.sin(angle + angle_offset), 
                f"{value}", ha='center', va='center')

    # Draw the outer circle of the ring
    theta = np.linspace(0, 2 * np.pi, 100)
    x_circle = radius * np.cos(theta)
    y_circle = radius * np.sin(theta)
    ax.plot(x_circle, y_circle, color='black')

# Create the PDF file to save all pages
pdf_file_name = f"{file_name[:-5]}.pdf"
with PdfPages(pdf_file_name) as pdf:
    # Generate charts
    for page in range(page_count):
        plt.figure(figsize=(fig_width, fig_height))  # Adjusted figure size for A4

        for i in range(stations_per_page):
            idx = page * stations_per_page + i
            if idx >= num_stations:
                break
            
            station_name = data.iloc[idx, 0]
            values_inner = data.iloc[idx, 1:5].values   # Columns B, C, D, E
            values_mid = data.iloc[idx, 5:11].values    # Columns F to K
            values_outer = data.iloc[idx, 11:17].values # Columns L to Q

            # Chart positioning
            ax = plt.subplot(rows_per_page, cols_per_page, i + 1)

            # Inner ring: 4 partitions
            plot_circle_with_partitions(ax, 0.8, values_inner, 4, angle_offset=np.pi/4)

            # Middle ring: 6 partitions (without overlapping lines onto the inner ring)
            plot_circle_with_partitions(ax, 1.6, values_mid, 6, angle_offset=np.pi/6, inner_radius=0.8)

            # Outer ring: 6 partitions (without overlapping lines onto inner rings)
            plot_circle_with_partitions(ax, 2.4, values_outer, 6, angle_offset=np.pi/6, inner_radius=1.6)

            # Chart settings
            ax.set_title(station_name, fontweight='bold')
            ax.set_xlim([-2.5, 2.5])
            ax.set_ylim([-2.5, 2.5])
            ax.set_aspect('equal')
            ax.axis('off')
        
        # Adjust margins to reduce space between charts
        plt.subplots_adjust(left=0.02, right=0.98, top=0.95, bottom=0.05, wspace=0.1, hspace=0.1)

        # Save the current figure as a new page in the PDF
        pdf.savefig()
        plt.close()

