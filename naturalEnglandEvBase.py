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
import os
import geopandas as gpd
import pandas as pd
import numpy as np
from functions import explode_multipart_polygons
from functions import check_geometry
from functions import add_fields
from functions import fields
from functions import eunisCodes
from functions import split_mosaic
from functions import form_mosaic
from shapely import wkt

path_parent = os.path.dirname(os.getcwd())
workfolder = input("Enter the path to the geopackage or geodatabase: ")
worklayer = input("Enter the name of the layer within the Geopackage or geodatabase: ")

evBase = gpd.read_file(workfolder, layer=worklayer)

add_fields(evBase)
evBase['GUI'].fillna(evBase['Dataset_UID'], inplace=True)
evBase['NE_UID'].fillna(evBase['Dataset_UID'], inplace=True)
evBase['POLYGON'] = np.arange(len(evBase)) + 1
evBase['MESH_Confi'] = evBase['MESH_confidence_score']
evBase = evBase[~evBase['GUI'].str.contains('UKSM')]
evBase = evBase[~evBase['NE_UID'].str.contains('NE_1848|D_00346|NE_1426|NE_1594|NE_1955')]

dataAccess = input("location of excel containing publicly accessible NE UID's: ")
dataAccess = pd.read_excel(dataAccess)
public = evBase[evBase['NE_UID'].isin(dataAccess.UID)]

explode_multipart_polygons(public)
check_geometry(public)

clipLayer = input("Enter the path to the clip layer: ")
clip_feature = gpd.read_file(clipLayer)
evBaseClip = gpd.clip(evBase, clip_feature)

# the HAB_TYPE column within the evidence base contains less detailed codes that the ORIG_HAB field. Due to this it was
# decided that we should use values within the ORIG_HAB field where possible. The following codes aims to achieve this.
# create a new field (new_hab) which includes A and B habitat codes, otherwise use values present in the HAB_TYPE field.
# This is required as a number of rows contain strings of non eunis codes, so we are interested in those which start
# with A or B.
evBaseClip['new_hab'] = np.where(evBaseClip['ORIG_HAB'].str.startswith('A' or 'B'), evBaseClip['ORIG_HAB'],
                                 evBaseClip['HAB_TYPE'])
# here we create two dataframes. One which contains complex habitats. Those where the new hab field contains the word
# 'with' indicating that a mosaic is present where the determiner was unsure how to classify the habitat.
# the other (habchecks) includes every polygon that did not contain the word 'with'.
complex_habs = evBaseClip.loc[evBaseClip['new_hab'].str.contains('with', na=False)].copy()
habchecks = evBaseClip.loc[~evBaseClip['new_hab'].str.contains('with', na=False)].copy()
habchecks['ORIG_HAB'].fillna("", inplace=True)
# formatting of the new hab field is required to satisfy the formatting of the combined map. special characters are
# removed some replaced with a + and others replaced with and empty value.
habchecks['new_hab'] = habchecks['new_hab'].str.replace('&|/|, ', '+')
habchecks['new_hab'] = habchecks['new_hab'].str.replace('or ', '/')
habchecks['new_hab'] = habchecks['new_hab'].str.replace('#', "")
habchecks['new_hab'] = habchecks['new_hab'].str.replace('*', "")
habchecks['new_hab'] = habchecks['new_hab'].str.replace('(', "")
habchecks['new_hab'] = habchecks['new_hab'].str.replace(')', "")
habchecks['new_hab'] = habchecks['new_hab'].str.replace(' ', '')
habchecks['new_hab'] = habchecks['new_hab'].str.split('-|:|[g-zG-Z]').str[0]
habchecks = habchecks.replace(r'\n|\r', '', regex=True)
habchecks = habchecks.replace(r'^\s*$', np.NaN, regex=True)
habchecks.new_hab.fillna(habchecks.Eunis_L3, inplace=True)
habchecks['new_hab'] = habchecks['new_hab'].str.replace('a', '')
habchecks['HAB_TYPE'] = habchecks['new_hab']

NE_eunisCodesCorrect = habchecks[habchecks['HAB_TYPE'].isin(eunisCodes)]
#           If eunis codes are not in the master list (are incorrect) then they are saved
#           to a new dataframe "eunisCodesIncorrect"
NE_eunisCodesIncorrect = habchecks[~habchecks['HAB_TYPE'].isin(eunisCodes)]

# Some of the values which have been designated as incorrect are actually correct, but contain a / indicating that
# during classification it was unsure which habitat it might be, so both are reported.
# we create a condition which removes the values containing a /
# correcting some of the incorrect values.
condition1 = NE_eunisCodesIncorrect.loc[NE_eunisCodesIncorrect['HAB_TYPE'].str.contains('/', na=False)].copy()
NE_eunisCodesIncorrect.drop(condition1.index, inplace=True)

if condition1.empty is False:
    split_mosaic(condition1)
    condition1['Eunis_L3'] = condition1['HAB_TYPE'].str[:4]
    form_mosaic(condition1)
    condition1 = gpd.GeoDataFrame(condition1, geometry='geometry', crs='EPSG:4326')
else:
    pass

# other values have also been incorrectly designated as incorrect. In this case this is due a . being used to separate
# eunis codes, but are otherwise correct. a new condition is made which removed these specific values from the
# incorrect dataframe. The replace the . with a +
options = ['A3.A1', 'A3.A2', 'A3.A1', 'A3.A4']
condition2 = NE_eunisCodesIncorrect[NE_eunisCodesIncorrect['HAB_TYPE'].isin(options)].copy()
condition2['HAB_TYPE'] = condition2['HAB_TYPE'].str.replace('.', '+')
NE_eunisCodesIncorrect.drop(condition2.index, inplace=True)
# as with the previous condition the EUNIS_L3 field must be redone based on the HAB_TYPE field.
if condition2.empty is False:
    split_mosaic(condition2)
    condition2['Eunis_L3'] = condition2['HAB_TYPE'].str[:4]
    form_mosaic(condition2)
    condition2 = gpd.GeoDataFrame(condition2, geometry='geometry', crs='EPSG:4326')
else:
    pass

# a final condition is set to correct for values which are correct but have not started with a correct eunis value.
# in this case both should have an A at the start.
options2 = ["5.4", "1.1221"]
condition3 = NE_eunisCodesIncorrect[NE_eunisCodesIncorrect['HAB_TYPE'].isin(options2)]
condition3['HAB_TYPE'] = 'A' + condition3['HAB_TYPE']
NE_eunisCodesIncorrect.drop(condition3.index, inplace=True)
condition3['Eunis_L3'] = condition3['HAB_TYPE'].str[:4]

#  merge dataframes of corrected codes back together
dataframesList = [condition1, condition2, condition3]
allConditionsMet = gpd.GeoDataFrame(pd.concat(dataframesList, ignore_index=False), crs=dataframesList[0].crs)

########################################################################################################################
NE_eunisCodesCorrect['Eunis_L3'] = NE_eunisCodesCorrect['HAB_TYPE'].str[:4]

NE_eunisCodesCorrect = NE_eunisCodesCorrect.applymap(str)
NE_eunisCodesCorrect['geometry'] = NE_eunisCodesCorrect['geometry'].apply(wkt.loads)
NE_eunisCodesIncorrect = NE_eunisCodesIncorrect.applymap(str)
NE_eunisCodesIncorrect['geometry'] = NE_eunisCodesIncorrect['geometry'].apply(wkt.loads)

form_mosaic(NE_eunisCodesCorrect)
form_mosaic(NE_eunisCodesIncorrect)

#           During the previous step the original geodataframe is changed to a dataframe,
#           in order to change it back we must redefine the geometry column and co-ord ref system
NE_eunisCodesCorrect = gpd.GeoDataFrame(NE_eunisCodesCorrect, geometry='geometry', crs='EPSG:4326')
NE_eunisCodesIncorrect = gpd.GeoDataFrame(NE_eunisCodesIncorrect, geometry='geometry', crs='EPSG:4326')

########################################################################################################################
# merging the corrected values which are merged into a single dataframe back into the dataframe of correct codes.
correctDataframesList = [NE_eunisCodesCorrect, allConditionsMet]
NE_eunisCodesCorrected = gpd.GeoDataFrame(pd.concat(correctDataframesList, ignore_index=False),
                                          crs=dataframesList[0].crs)

NE_eunisCodesCorrected = NE_eunisCodesCorrected[fields]
NE_eunisCodesIncorrect = NE_eunisCodesIncorrect[fields]


########################################################################################################################
# save files
if complex_habs.empty is True:
    pass
else:
    complex_habs.to_file(path_parent + "/outputs/ToCheck.gpkg", layer='NE_complexHabs', driver="GPKG")

if NE_eunisCodesIncorrect.empty is True:
    pass
else:
    NE_eunisCodesIncorrect.to_file(path_parent + "/outputs/ToCheck.gpkg", layer='NE_EUNIS_Incorrect', driver="GPKG")

NE_eunisCodesCorrected.to_file(path_parent + "/outputs/FormattedLayers.gpkg", layer='NE_EUNIS_Corrected', driver="GPKG")

if complex_habs.empty is False:
    print('complex habitats are present')
elif NE_eunisCodesIncorrect.empty is False:
    print('Incorrect EUNIS codes are present')
else:
    print("All codes are correct and formatted no incorrect codes or complex habitat codes")
if NE_eunisCodesCorrect.empty is False:
    print("Correct EUNIS codes are present, incorrect codes may also be present, please check messages")
