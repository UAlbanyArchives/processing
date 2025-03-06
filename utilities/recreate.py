import os
import argparse

def main():
    parser = argparse.ArgumentParser(description="Rebuild parts of a SPE_DAO package.")

    parser.add_argument("mode", help="Collection ID for the files you are recreating.")
    parser.add_argument("--collectionID", required=True, help="Collection ID for the files you are packaging.")
    parser.add_argument("--refID", required=True, help="A 32-character ArchivesSpace ID, e.g., '855f9efb1fae87fa3b6ef8c8a6e0a28d'.")

    args = parser.parse_args()

    print(f"Mode: {args.mode}")
    print(f"Collection ID: {args.collectionID}")
    print(f"Object Ref ID: {args.refID}")

    if args.mode == "thumbnail":
        from iiiflow import make_thumbnail
        make_thumbnail(args.collectionID, args.refID)
    elif args.mode == "ptif":
        from iiiflow import create_ptif
        print ("Creating pyramidal tifs (.ptifs)...")
        create_ptif(args.collectionID, args.refID)
    elif args.mode == "ocr":
        from iiiflow import create_hocr
        print ("Recognizing text...")  
        create_hocr(args.collectionID, args.refID)
    elif args.mode == "manifest":
        from iiiflow import create_manifest  
        print ("Generating IIIF manifest...")
        create_manifest(args.collectionID, args.refID)
        print (f"Check out digital object at:")
        #print (f"https://media.archives.albany.edu/test.html?collection={args.collection_ID}&id={args.refID}")
    else:
        raise ValueError(f"ERROR: incorrect mode {args.mode}.")

    print ("Success!")

if __name__ == "__main__":
    main()