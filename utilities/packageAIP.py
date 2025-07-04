import os
import shutil
import argparse
from datetime import datetime
from packages.AIP import ArchivalInformationPackage
from packages.SIP import SubmissionInformationPackage

argParse = argparse.ArgumentParser()
argParse.add_argument("package", help="Package ID in Processing directory.")
argParse.add_argument('-u', "--update", help="Package master files from the processing package instead of the files in the SIP.", action='store_true', default=None)
argParse.add_argument('-n', "--noderivatives", help="Will not package derivatives. For cases were masters, (like PDFs) are the same as derivatives.", action='store_true', default=None)
args = argParse.parse_args()

processingDir = "/backlog"
sipDir = "/Archives/SIP"
aipDir = "/Archives/AIP"
logDir = "/logs"


print("Began at " + str(datetime.now()))

colID = args.package.split("_")[0].split("-")[0]
package = os.path.join(processingDir, colID, args.package)
print(f"Packaging {package}")
derivatives = os.path.join(package, "derivatives")
metadata = os.path.join(package, "metadata")
masters = os.path.join(package, "masters")
sipPackage = os.path.join(sipDir, colID, args.package)

if not os.path.isdir(package) or not os.path.isdir(derivatives) or not os.path.isdir(metadata):
    raise ("ERROR: " + package + " is not a valid package.")

SIP = SubmissionInformationPackage()
SIP.load(sipPackage)

print ("Validating SIP " + args.package + "...")
if not SIP.bag.is_valid():
    raise ("ERROR: SIP " + args.package + " is not a valid bag!.")
print("Finished Validating at " + str(datetime.now()))

print ("Creating AIP " + args.package + "...")
AIP = ArchivalInformationPackage()
AIP.create(colID, args.package)

print ("Moving metadata...")
AIP.packageMetadata(metadata)
AIP.addSIPData(SIP.bag.path)

if not args.noderivatives:
    print ("Moving derivatives...")
    AIP.packageFiles("derivatives", derivatives)

if args.update:
    print ("Moving masters from processing...")
    AIP.packageFiles("masters", masters)
else:
    print ("Moving masters from SIP...")
    AIP.packageFiles("masters", SIP.data)

print ("Cleaning AIP...")    
AIP.clean()

print ("Including logs before saving...")
logsDest = os.path.join(AIP.bag.path, "logs")
os.mkdir(logsDest)
for log in os.listdir(logDir):
    logMatch = False
    if args.package in log:
        logMatch = True
    elif colID in log:
        with open(os.path.join(logDir, log), "r") as f:
            if args.package in f.read():
                logMatch = True
    if logMatch:
        shutil.copy2(os.path.join(logDir, log), logsDest)

print ("Writing checksums...")
AIP.bag.save(processes=4, manifests=True)
print ("AIP Saved!")
print ("Finished save at " + str(datetime.now()))

if not args.update:
    print ("Checking AIP against SIP manifest...")
    if AIP.checkSIPManifest:
        print ("AIP masters conforms to SIP manifest :)")
        print ("Safely removing SIP " + args.package + "...")
        SIP.safeRemove()
        sipParent = os.path.join(sipDir, colID)
        if len(os.listdir(sipParent)) == 0:
            os.rmdir(sipParent)
        print ("Removed SIP " + args.package)
        print ("Removed SIP at " + str(datetime.now()))
        
        # remove processing package
        print (f"Removing processing package {args.package}...")
        shutil.rmtree(package)
        print (f"Removed processing package at {datetime.now()}.")
        collectionDir = os.path.join(processingDir, colID)
        if len(os.listdir(collectionDir)) == 0:
            os.rmdir(collectionDir)
            print (f"Removed empty collection directory at {datetime.now()}.")
        else:
            total_thing = 0
            total_files = 0
            total_dirs = 0
            for thing in os.scandir(collectionDir):
                total_thing += 1
                if thing.is_file():
                    total_files += 1
                    print (f"\tFound {thing.name}")
                if thing.is_dir():
                    total_dirs += 1
            print (f"Maintained collection directory with {total_thing} length, {total_files} files, and {total_dirs} folders.")
    else:
        raise ValueError ("ERROR: AIP does not conform to SIP manifest. Did not delete SIP.")
else:
    print ("Skipping removal of SIP. Must run safeRemoveSIP.py when updating masters from processing package.")
    
    if AIP.bag.is_valid():
        # remove processing package
        print ("Removing processing package " + args.package  + "...")
        shutil.rmtree(package)
        collectionDir = os.path.join(processingDir, colID)
        if len(os.listdir(collectionDir)) == 0:
            os.rmdir(collectionDir)
        print("Removed processing package at " + str(datetime.now())) 
    else:
        raise Exception("ERROR: " + str(aipPath) + " is not valid! A valid AIP must be present to use SIP.safeRemove().")

    print ("Remember use safeRemoveSIP.py to remove SIP " + args.package)
    
print ("Complete!")
print ("Finished at " + str(datetime.now()))
