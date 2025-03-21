from description_harvester import harvest

def reindex(collection_ID):

    if collection_ID.startswith("ger"):
        repo = "ger"
    elif collection_ID.startswith("mss"):
        repo = "mss"
    elif collection_ID.startswith("ua"):
        repo = "ua"
    else:
        ndpa_path = "/ndpaList.txt"
        with open(ndpa_path, "r") as ndpa_file:
            ndpa_ids = {line.strip() for line in ndpa_file}
        if collection_ID in ndpa_ids:
            repo = "ndpa"
        else:
            repo = "apap"
    
    print (f"collection: {collection_ID}")
    print (f"Repository: {repo}")

    harvest(["--id", collection_ID, "--repo", repo])

    print ("Complete.")


# for running with command line args
if __name__ == '__main__':
    import argparse

    argParse = argparse.ArgumentParser()
    argParse.add_argument("--id", help="Collection ID to reindex.")
    args = argParse.parse_args()
    
    reindex(args.id)
