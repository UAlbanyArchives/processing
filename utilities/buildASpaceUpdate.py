import os
import csv
import openpyxl
import argparse
from datetime import datetime

argParse = argparse.ArgumentParser()
argParse.add_argument("package", help="Package ID in Processing directory.")
argParse.add_argument("-f", "--file", help="File name of spreadsheet to be updated. If no files are listed, all will be updated.", default=None)
args = argParse.parse_args()


processingDir = "/backlog"

colID = args.package.split("_")[0].split("-")[0]
package = os.path.join(processingDir, colID, args.package)
derivatives = os.path.join(package, "derivatives")
masters = os.path.join(package, "masters")
metadata = os.path.join(package, "metadata")

if not os.path.isdir(package) or not os.path.isdir(derivatives) or not os.path.isdir(metadata):
    raise ValueError(f"ERROR: {package} is not a valid package.")

hyraxHeaders = ["Type", "URIs", "File Paths", "Accession", "Collecting Area", "Collection Number", "Collection", "ArchivesSpace ID", \
"Record Parents", "Title", "Description", "Date Created", "Resource Type", "License", "Rights Statement", "Subjects", "Whole/Part",\
"Processing Activity", "Extent", "Language"]
hyraxImport = os.path.join(metadata, args.package + ".tsv")
finalMetadata = []

# No longer reads from package-ID.tsv, instead creates it from all .tsv files
#if not os.path.isfile(hyraxImport):
#    raise ValueError(f"ERROR: {hyraxImport} is missing or not a valid hyrax import TSV.")
tsvFiles = []
for tsv in os.listdir(metadata):
    if not tsv == args.package + ".tsv":
        if tsv.lower().endswith(".tsv"):
            tsvFiles.append(os.path.join(metadata, tsv))

if args.file and not os.path.isfile(os.path.join(metadata, args.file)):
    raise ValueError(f"ERROR: {args.file} is missing.")
elif args.file and not args.file.lower().endswith(".xlsx"):
    raise ValueError(f"ERROR: {args.file} is not a valid asInventory spreadsheet.")

sheetCount = 0
for sheetFile in os.listdir(metadata):
    if sheetFile.lower().endswith(".xlsx"):
        if not args.file or args.file.lower() == sheetFile.lower():
            print ("Reading sheet: " + sheetFile)
            
            sheetPath = os.path.join(metadata, sheetFile)
            wb = openpyxl.load_workbook(filename=sheetPath, read_only=False)
            
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
                    sheetCount += 1
                    rowCount = 0
                    for row in sheet.rows:
                        rowCount = rowCount + 1
                        if rowCount > 6:
                            if not row[22].value is None:
                                
                                if "|" in row[22].value:
                                    daoPath = row[22].value.split("|")[0]
                                else:
                                    daoPath = row[22].value
                                filePathDerivatives = os.path.join(derivatives, daoPath)
                                filePathMasters = os.path.join(masters, daoPath)
                                if os.path.exists(filePathDerivatives):
                                    filePath = filePathDerivatives
                                else:
                                    filePath = filePathMasters
                                if os.path.exists(filePath):
                            
                                    refID = row[0].value
                                    match = False
                                    
                                    for tsv in tsvFiles:
                                        file = open(tsv, "r")
                                        reader = csv.reader(file, delimiter='\t')
                                        for line in reader:
                                            if line[1].startswith("daos/") or line[1].startswith("avs/") or line[1].startswith("images/"):
                                                if line[7] == refID:
                                                    print ("Updating " + str(row[22].value) + " to " + str(line[1]))
                                                    row[22].value = "https://archives.albany.edu/concern/" + line[1]
                                                    match = True
                                                    finalMetadata.append(line)         
                                        file.close()
                                    
                                    if match == False:
                                        print ("ERROR: failed to find matching refID " + refID + " in hyrax upload file " + hyraxImport)
                                else:
                                    print (f"ERROR: no matching file for {daoPath}. Does not exist in either derivatives or masters.")
            wb.save(filename=os.path.join(metadata, "updated_" + sheetFile))

if os.path.isfile(hyraxImport):
    outfile = open(hyraxImport, "a", encoding='utf-8', newline='')
    writer = csv.writer(outfile, delimiter='\t', lineterminator='\n')
else:
    outfile = open(hyraxImport, "w", encoding='utf-8', newline='')
    writer = csv.writer(outfile, delimiter='\t', lineterminator='\n')
    writer.writerow(hyraxHeaders)
for metadataLine in finalMetadata:
    writer.writerow(metadataLine)
outfile.close()

if sheetCount > 0:
    print (f"Wrote {len(finalMetadata)} Hyrax objects to {args.package}.tsv.")
    print (f"Complete! Updated {sheetCount} asInventory spreadsheets.")
else:
    print ("ERROR: Found no valid asInventory spreadsheets.")
print (f"Finished at {datetime.now()}")
