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
import numpy as np
import os
from functions import eunisCodes
from functions import explode_multipart_polygons
from functions import check_geometry
from functions import fields
from functions import add_fields
from functions import split_mosaic
from functions import form_mosaic

# set input file locations
path_parent = os.path.dirname(os.getcwd())
workfolder = input("Enter the path to the geopackage or geodatabase: ")
worklayer = input("Enter the name of the layer within the Geopackage or geodatabase: ")

# read the new survey shapefile
surveyMaps = gpd.read_file(workfolder, layer=worklayer)
# check that essential columns are present and add them if not
add_fields(surveyMaps)

# populate fields
surveyMaps['POLYGON'] = np.arange(len(surveyMaps)) + 1
surveyMaps['MESH_Confi'].fillna(surveyMaps['SUM_CONF'], inplace=True)

# subset columns to remove unnecessary fields
fields = fields
surveyMaps = surveyMaps[fields]
# split mosaic codes if present for quality checks
surveyCodeQuery = split_mosaic(surveyMaps)

#           If eunis codes are correct, a new dataframe "eunisCodesCorrect" is created containing only correct codes.
eunisCodesCorrect = surveyCodeQuery[surveyCodeQuery['HAB_TYPE'].isin(eunisCodes)]

#           If eunis codes are not in the master list (are incorrect) then they are saved
#           to a new dataframe "eunisCodesIncorrect"
eunisCodesIncorrect = surveyCodeQuery[~surveyCodeQuery['HAB_TYPE'].isin(eunisCodes)]
#           Now copy the first 4 characters of the HAB_TYPE field into the EUNIS_L3 column
eunisCodesCorrect['Eunis_L3'] = eunisCodesCorrect['HAB_TYPE'].str[:4]

eunisCodesCorrect = form_mosaic(eunisCodesCorrect)

eunisCodesCorrect['HAB_TYPE'] = eunisCodesCorrect['HAB_TYPE'].str.split('+').apply(set).str.join('+')
eunisCodesCorrect['Eunis_L3'] = eunisCodesCorrect['Eunis_L3'].str.split('+').apply(set).str.join('+')

eunisCodesCorrect = gpd.GeoDataFrame(eunisCodesCorrect, geometry='geometry', crs='EPSG:4326')
eunisCodesIncorrect = gpd.GeoDataFrame(eunisCodesIncorrect, geometry='geometry', crs='EPSG:4326')

outdir = '/outputs'
if not os.path.exists(outdir):
    os.makedirs(path_parent + outdir, exist_ok=True)
if eunisCodesCorrect.empty is True:
    print('No correct does present, revise data')
    exit()
else:
    print('Saving correct codes ')
    eunisCodesCorrect.to_file(path_parent + "/outputs/FormattedLayers.gpkg", layer='NewSurveyMaps', driver="GPKG")
    pass
if eunisCodesIncorrect.empty is True:
    print('No incorrect codes')
else:
    print('Incorrect EUNIS codes are present, please revise and rerun the dataset')
    eunisCodesIncorrect.to_file(path_parent + "/outputs/ToCheck.gpkg", layer='NewSurveyMaps_IncorrectCodes',
                                driver="GPKG")
    exit()

eunisCodesCorrect = explode_multipart_polygons(eunisCodesCorrect)
eunisCodesCorrect = check_geometry(eunisCodesCorrect)

eunisCodesCorrect = eunisCodesCorrect[fields]
eunisCodesCorrect.to_file(path_parent + "/outputs/FormattedLayers.gpkg", layer='NewSurveyMaps', driver="GPKG")
print('All codes are correct and have been formatted, geometry is valid and no multipart polygons are present')
