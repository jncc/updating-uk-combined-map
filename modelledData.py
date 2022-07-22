########################################################################################################################

# Title: Combined Map Updates (code to be used for modelled data layer)

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
euseamap = gpd.read_file(workfolder, layer=worklayer)
# check that desired fields are present
add_fields(euseamap)

# the following code will explode multipart polygons, check the geometry and remove unnecessary fields
euseamap = explode_multipart_polygons(euseamap)
euseamap = check_geometry(euseamap)
euseamap = euseamap[fields]

# save the newly formatted layer to the outputs folder.
euseamap.to_file(path_parent + "/outputs/FormattedLayers.gpkg", layer='EUSeaMap', driver="GPKG")
print('All codes are correct and have been formatted, geometry is valid and no multipart polygons are present')
