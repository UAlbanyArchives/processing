import os

def writeList(package, directory, name, verbose, log_file):

    #get all files in the folder
    fileList = []
    dirList = []
    for root, dirs, files in os.walk(directory):
        for folder in dirs:
            dirList.append(folder)
        for item in files:
            filePath = os.path.join(root, item).split(directory)[1]
            if filePath.startswith("\\"):
                filePath = filePath[1:]
            if filePath.startswith("/"):
                filePath = filePath[1:]
            if verbose:
                if log_file:
                    with open(log_file, "a") as f:
                        f.write(f"\n\twriting {filePath}")
                else:
                    print (f"\twriting {filePath}")
            fileList.append(filePath)

    # Write to files
    with open(os.path.join(package, f'{name}.txt'), 'w') as f:
        for line in fileList:
            f.write(f"{line}\n")
        f.close()
    with open(os.path.join(package, f'{name}-directories.txt'), 'w') as f:
        for line in dirList:
            f.write(f"{line}\n")
        f.close()

def listFiles(ID, verbose=False, log_file=None):

    processingDir = "/backlog"

    colID = ID.split("_")[0].split("-")[0]
    package = os.path.join(processingDir, colID, ID)
    derivatives = os.path.join(package, "derivatives")
    masters = os.path.join(package, "masters")

    if not os.path.isdir(package) or not os.path.isdir(derivatives):
        raise ("ERROR: " + package + " is not a valid package.")

    if verbose:
        if log_file:
            with open(log_file, "a") as f:
                f.write(f"Writing file list for {package}")
        else:
            print (f"Writing file list for {package}")

    writeList(package, derivatives, "derivatives", verbose, log_file)
    writeList(package, masters, "masters", verbose, log_file)

    if verbose:
        if log_file:
            with open(log_file, "a") as f:
                f.write(f"\nComplete.")
        else:
            print ("Complete.")


# for running with command line args
if __name__ == '__main__':
    import argparse

    argParse = argparse.ArgumentParser()
    argParse.add_argument("ID", help="ID for a package in Processing directory.")
    argParse.add_argument("-v", "--verbose", help="lists all files written.", action="store_true")
    args = argParse.parse_args()
    
    listFiles(args.ID, args.verbose)
