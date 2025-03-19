from description_harvester import harvest

def reindex(collection_ID, indexNDPA):

    if collection_ID.startswith("ger"):
        repo = "ger"
    elif collection_ID.startswith("mss"):
        repo = "mss"
    elif collection_ID.startswith("ua"):
        repo = "ua"
    else:
        if indexNDPA:
            repo = "ndpa"
        else:
            repo = "apap"
    
    print (f"collection: {collection_ID}")
    print (f"NDPA?: {indexNDPA}")
    print (f"Repository: {repo}")

    harvest(["--id", collection_ID, "--repo", repo])

    print ("Complete.")


# for running with command line args
if __name__ == '__main__':
    import argparse

    argParse = argparse.ArgumentParser()
    argParse.add_argument("--id", help="Collection ID to reindex.")
    argParse.add_argument("--ndpa", help="Index apap IDs as NDPA.", action="store_true")
    args = argParse.parse_args()
    
    reindex(args.id, args.ndpa)
