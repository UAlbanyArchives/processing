import os
import csv
import urllib3
import requests
import argparse
import openpyxl
from datetime import datetime
from asnake.client import ASnakeClient

argParse = argparse.ArgumentParser()
argParse.add_argument("package", help="Package ID in Processing directory.")
argParse.add_argument("-f", "--file", help="File name of spreadsheet to be updated. If no files are listed, all will be updated.", default=None)
args = argParse.parse_args()

processingDir = "/backlog"

# Connect to ASpace
client = ASnakeClient()

colID = args.package.split("_")[0].split("-")[0]
package = os.path.join(processingDir, colID, args.package)
derivatives = os.path.join(package, "derivatives")
masters = os.path.join(package, "masters")
metadata = os.path.join(package, "metadata")

hyraxHeaders = ["Type", "URIs", "File Paths", "Accession", "Collecting Area", "Collection Number", "Collection", "ArchivesSpace ID", \
"Record Parents", "Title", "Description", "Date Created", "Resource Type", "License", "Rights Statement", "Subjects", "Whole/Part",\
"Processing Activity", "Extent", "Language"]

# no longer writes to single sheet file, but creates .tsvs for each asInventory spreadsheet
#hyraxSheetFile = os.path.join(metadata, args.package + ".tsv")
#hyraxImport = os.path.join(ESPYderivatives, "import")
#hyraxFiles = os.path.join(ESPYderivatives, "files", colID)
#if not os.path.isdir(hyraxFiles):
#    os.mkdir(hyraxFiles)

if not os.path.isdir(package) or not os.path.isdir(derivatives) or not os.path.isdir(metadata):
    raise ValueError("ERROR: " + package + " is not a valid package.")

# ignore not verifying SSL warnings and set up session
urllib3.disable_warnings()
session = requests.Session()
session.verify = False

collectionData = session.get("https://archives.albany.edu/description/catalog/" + colID.replace(".", "-") + "?format=json").json()
collectingArea = collectionData["data"]["attributes"]["repository_ssm"]["attributes"]["value"][0]
collection = collectionData["data"]["attributes"]["title_ssm"]["attributes"]["value"][0]
processingNote = "Processing documentation available at: https://wiki.albany.edu/display/SCA/Processing+Ingested+Digital+Files"

# make hyrax sheet
hyraxSheet = []

def getParentURIs(obj, objURI, parentList=None):
    """Recursuvely goes thorugh ASpace tree and finds matching URI and returns a list of parents
    """
    if parentList is None:
        parentList = [] 

    parentList.append(obj["record_uri"])
    
    if obj["record_uri"] == objURI:
        return parentList[:-1]

    for child in obj["children"]:
        result = getParentURIs(child, objURI, parentList.copy())
        if result:
            return result
          
    # If the objURI is not found in the current path, remove the current node
    parentList.pop()
    return None
            
    return parentList

def convertIDs(parentURIs):
    """converts a list of ASpace URIs to a list of id_0s and ref_ids
    Its much faster to to this for just the URI list than make calls for every node in getParentURIs
    """
    parentIDs = []
    for parent in parentURIs:
        parentRefID = client.get(parent).json()["ref_id"]  
        parentIDs.append(parentRefID)
    return parentIDs

sheetCount = 0
objectCount = 0
warningList = [] 
for sheetFile in os.listdir(metadata):
    if sheetFile.lower().endswith(".xlsx") and not sheetFile.lower().startswith("~$"):
        if not args.file or args.file.lower() == sheetFile.lower():
            outfileName = os.path.join(metadata, os.path.splitext(sheetFile)[0] + ".tsv")
            sheetCount += 1
            print ("Reading sheet: " + sheetFile)
            sheetPath = os.path.join(metadata, sheetFile)
            wb = openpyxl.load_workbook(filename=sheetPath, read_only=True)
            
            #validate sheets
            for sheet in wb.worksheets:
                checkSwitch = True
                try:
                    if sheet["H1"].value.lower().strip() != "title":
                        checkSwitch = False
                    elif sheet["H2"].value.lower().strip() != "level":
                        checkSwitch = False
                    elif sheet["H3"].value.lower().strip() != "ref id":
                        checkSwitch = False
                    elif sheet["J6"].value.lower().strip() != "date 1 display":
                        checkSwitch = False
                    elif sheet["D6"].value.lower().strip() != "container uri":
                        checkSwitch = False
                except:
                    print ("ERROR: incorrect sheet " + sheet.title + " in file " + sheetPath)
                    
                if checkSwitch == False:
                    print ("ERROR: incorrect sheet " + sheet.title + " in file " + sheetPath)
                else:              
                    
                    rowCount = 0
                    tree = None
                    for row in sheet.rows:
                        rowCount = rowCount + 1
                        if rowCount > 6:
                            if not row[22].value is None:
                                if not row[8].value:
                                    raise ValueError(f"ERROR: Row {rowCount} is invalid. Missing Title.")
                                elif not row[0].value:
                                    raise ValueError(f"ERROR: Row {rowCount} is invalid. Missing Ref ID for {row[8].value}.")
                                elif not row[9].value:
                                    raise ValueError(f"ERROR: Row {rowCount} is invalid. Missing display date for {row[8].value}.")
                                else:
                                    refID = row[0].value
                                    title = row[8].value
                                    date = row[9].value
                                    print ("\tReading " + str(title) + "...")

                                    #for new objects not yet indexed in ArcLight
                                    ref = client.get("repositories/2/find_by_id/archival_objects?ref_id[]=" + refID).json()
                                    item = client.get(ref["archival_objects"][0]["ref"]).json()
                                    if tree is None:                                                                                    
                                        resource = client.get(item["resource"]["ref"]).json()
                                        tree = client.get(resource["tree"]["ref"]).json()

                                    objURI = ref["archival_objects"][0]["ref"]
                                    parentURIs = getParentURIs(tree, objURI)
                                    parentList = convertIDs(parentURIs[1:])
                                    #print (parentList)
                                    parents = "|".join(parentList)                                            
                                    
                                    derivativesDao = os.path.join(derivatives, row[22].value)
                                    masterDao = os.path.join(masters, row[22].value)
                                    if os.path.isfile(derivativesDao) or os.path.isfile(masterDao):
                                        dao_path = row[22].value
                                    elif os.path.isdir(derivativesDao) or os.path.isdir(masterDao):
                                        excluded_files = ["thumbs.db", "desktop.ini", ".ds_store"]
                                        dao_files = []
                                        if os.path.isdir(derivativesDao):
                                            for dao_file in os.listdir(derivativesDao):
                                                if not dao_file.lower() in excluded_files:
                                                    dao_files.append(dao_file)
                                        else:
                                            for dao_file in os.listdir(masterDao):
                                                if not dao_file.lower() in excluded_files:
                                                    dao_files.append(dao_file)
                                        dao_path = "|".join(dao_files)
                                    else:
                                        print ("WARNING: DAO filename \"" + row[22].value + "\" does not exist in package.")
                                        warningList.append(row[22].value)
                                        dao_path = row[22].value
                                    
                                    
                                    hyraxObject = ["DAO", "", dao_path, args.package, collectingArea, colID, collection, refID, parents, title, "", date, \
                                    "", "", "", "", "whole", processingNote, "", ""]
                                    hyraxSheet.append(hyraxObject)
                                    objectCount += 1

            print (f"Writing to {outfileName}...")                 
            if os.path.isfile(outfileName):
                outfile = open(outfileName, "a", encoding='utf-8', newline='')
                writer = csv.writer(outfile, delimiter='\t', lineterminator='\n')
            else:
                outfile = open(outfileName, "w", encoding='utf-8', newline='')
                writer = csv.writer(outfile, delimiter='\t', lineterminator='\n')
                writer.writerow(hyraxHeaders)
            for object in hyraxSheet:
                #print (object[9])
                writer.writerow(object)
            outfile.close()

if len(warningList) > 0:
    print ("WARNING: the following files were not found in package:")
    print ("\t" + "\n\t".join(warningList))

if sheetCount == 0:
    print ("Error: No asInventory spreadsheet found. Could not build Hyrax upload sheet.")
elif objectCount == 0:
    print ("Error: Did not find any objects to upload in sheets. Requires ref_id, title, display date, and DAO path.")
else:
    print (f"Complete! Created {sheetCount} sheets with {objectCount} total objects.")
    print (f"Finished at {datetime.now()}")
