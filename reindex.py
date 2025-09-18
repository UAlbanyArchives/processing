import os
from datetime import datetime
from iiiflow import collections, index_hocr_to_solr

complete_path = "/DigitizationExtentTracker/reindex-complete.log"
log_path = "/DigitizationExtentTracker/reindex.log"

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")

# --- Load already completed IDs from the log ---
completed = {}  # {collection_id: [object_ids]}

if os.path.exists(complete_path):
    current_collection = None
    with open(complete_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Check if line is a collection id (no leading tab)
            if not line.startswith("\t"):
                # Extract collection id from log format: [timestamp] collection_id
                try:
                    collection_id = line.split("]")[1].strip()
                    current_collection = collection_id
                    if current_collection not in completed:
                        completed[current_collection] = []
                except IndexError:
                    continue
            else:
                # Extract object id (line starts with tab)
                object_id = line.strip()
                if current_collection:
                    completed[current_collection].append(object_id)

log(f"Loaded {sum(len(v) for v in completed.values())} completed object IDs from log")

# --- Run indexing only for objects not in completed ---
for collection in collections:
    collection_id = collection.id
    for object_id in collection.objects:
        if collection_id in completed and object_id in completed[collection_id]:
            log(f"Skipping already indexed {object_id} in {collection_id}")
            continue

        log(f"Indexing {object_id} in {collection_id}")
        index_hocr_to_solr(collection_id, object_id)

        # Optionally append to the complete log immediately
        with open(complete_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {collection_id}\n")
            f.write(f"\t{object_id}\n")
