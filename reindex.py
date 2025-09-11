import os
from datetime import datetime
from iiiflow import collections, index_hocr_to_solr

log_path = "/DigitizationExtentTracker/reindex.log"

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")

for collection in collections:
	log(collection.id)
	for object_id in collection.objects:
		log(f"\t{object_id}")
		index_hocr_to_solr(collection.id, object_id)
