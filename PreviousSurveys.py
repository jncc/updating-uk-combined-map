########################################################################################################################

# Title: Combined Map Updates

# Authors: Audsley, A., Burrel, B., Matear, L.(2022)
# Version Control: 2.0

# Script description:
#                        To ensure no permanent alterations are made to the master documents, all data used within this
#                        script are copies of the original files. Files referenced within this code have been copied to
#                        a local location (D:) to reduce overall processing speed.
#                        This script is the first stage of updating the combined map. It focused on loading and
#                        standardising the datasets. Outputs will be generated which highlight incorrect data and must
#                        be queried with data providers.
#                        For any enquiries please contact Marine Evidence Team

########################################################################################################################

import geopandas as gpd
from functions import add_fields
from functions import fields
from functions import explode_multipart_polygons
from functions import check_geometry
import os

# set the file path and request location to the geopackage or geodatabase and the corresponding layer required
path_parent = os.path.dirname(os.getcwd())
workfolder = input("Enter the path to the geopackage or geodatabase: ")
worklayer = input("Enter the name of the layer within the Geopackage or geodatabase: ")

# load the layer previously requested.
CBmap = gpd.read_file(workfolder, layer=worklayer)

# subset previous combined map to remove EuSeaMap, UKSeaMap
oldSurveyData = CBmap[~CBmap['GUI'].str.contains('EUSM|UKSM')]

# erase english inshore waters
# load the shapefile that is required to clip data
clip_feature = input("Location of layer used to clip: ")
clip_feature = gpd.read_file(clip_feature)
# remove the english inshore waters
offshoreSurveys = gpd.overlay(oldSurveyData, clip_feature, how='difference')

# check that desired fields are present
add_fields(offshoreSurveys)

# the following code will explode multipart polygons, check the geometry and remove unnecessary fields
offshoreSurveys = explode_multipart_polygons(offshoreSurveys)
offshoreSurveys = check_geometry(offshoreSurveys)
offshoreSurveys = offshoreSurveys[fields]

# save file
offshoreSurveys.to_file(path_parent + "/outputs/FormattedLayers.gpkg", layer='OldOffshoreSurveys', driver="GPKG")
print("File has been saved and contains correctly formatted and valid geometry")
