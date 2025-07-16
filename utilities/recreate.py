import os
import yaml
import argparse

def main():
    parser = argparse.ArgumentParser(description="Rebuild parts of a SPE_DAO package.")

    parser.add_argument("mode", help="Collection ID for the files you are recreating.")
    parser.add_argument("--collectionID", required=True, help="Collection ID for the files you are packaging.")
    parser.add_argument("--refID", required=True, help="A 32-character ArchivesSpace ID, e.g., '855f9efb1fae87fa3b6ef8c8a6e0a28d'.")

    args = parser.parse_args()

    with open("/root/.iiiflow.yml", "r") as config_file:
        config = yaml.safe_load(config_file)
    manifest_url_root = config.get("manifest_url_root")

    print(f"Mode: {args.mode}")
    print(f"Collection ID: {args.collectionID}")
    print(f"Object Ref ID: {args.refID}")

    if args.mode == "thumbnail":
        from iiiflow import make_thumbnail
        make_thumbnail(args.collectionID, args.refID)
    elif args.mode == "all":
        from iiiflow import make_thumbnail, create_pdf, create_ptif, create_hocr, create_manifest, index_hocr_to_solr
        print ("Recreating IIIF object...")
        make_thumbnail(args.collectionID, args.refID)
        print ("Creating pyramidal tifs (.ptifs)...")
        create_ptif(args.collectionID, args.refID)
        print ("Creating alternative PDF...")
        create_pdf(args.collectionID, args.refID)
        print ("Recognizing text...")  
        create_hocr(args.collectionID, args.refID)
        print ("Indexing HOCR text for content search...")
        index_hocr_to_solr(args.collectionID, args.refID)
        print ("Generating IIIF manifest...")
        create_manifest(args.collectionID, args.refID)
        #print (f"Check out digital object at:")
        #print (f"https://media.archives.albany.edu/test.html?collection={args.collection_ID}&id={args.refID}")
    elif args.mode == "all-no-pdf":
        from iiiflow import make_thumbnail, create_ptif, create_hocr, create_manifest, index_hocr_to_solr
        print ("Recreating IIIF object...")
        make_thumbnail(args.collectionID, args.refID)
        print ("Creating pyramidal tifs (.ptifs)...")
        create_ptif(args.collectionID, args.refID)
        print ("Recognizing text...")  
        create_hocr(args.collectionID, args.refID)
        print ("Indexing HOCR text for content search...")
        index_hocr_to_solr(args.collectionID, args.refID)
        print ("Generating IIIF manifest...")
        create_manifest(args.collectionID, args.refID)
        #print (f"Check out digital object at:")
        #print (f"https://media.archives.albany.edu/test.html?collection={args.collection_ID}&id={args.refID}")
    elif args.mode == "pdf":
        from iiiflow import create_pdf
        print ("Creating alternative PDF...")
        create_pdf(args.collectionID, args.refID)
    elif args.mode == "ptif":
        from iiiflow import create_ptif
        print ("Creating pyramidal tifs (.ptifs)...")
        create_ptif(args.collectionID, args.refID)
    elif args.mode == "ocr":
        from iiiflow import create_hocr, index_hocr_to_solr
        print ("Recognizing text...")  
        create_hocr(args.collectionID, args.refID)
        print ("Indexing HOCR text for content search...")
        index_hocr_to_solr(args.collectionID, args.refID)
    elif args.mode == "index":
        from iiiflow import index_hocr_to_solr
        print ("Indexing HOCR text for content search...")
        index_hocr_to_solr(args.collectionID, args.refID)
    elif args.mode == "manifest":
        from iiiflow import create_manifest  
        print ("Generating IIIF manifest...")
        create_manifest(args.collectionID, args.refID)
        #print (f"Check out digital object at:")
        #print (f"https://media.archives.albany.edu/test.html?collection={args.collection_ID}&id={args.refID}")
    else:
        raise ValueError(f"ERROR: incorrect mode {args.mode}.")

    print ("Success!")
    dao_url = f"{manifest_url_root}/{args.collectionID}/{args.refID}/manifest.json"
    print (f"Check out digital object at:")
    print (f"https://media.archives.albany.edu/test.html?manifest={dao_url}")

if __name__ == "__main__":
    main()