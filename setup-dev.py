import os

cwd = os.getcwd()
parent = os.path.dirname(cwd)

def setup_dir(name):
	if not os.path.isdir(name):
		os.mkdir(name)

base = os.path.join(parent, "flask_processing_app_testing")
setup_dir(base)

archives = os.path.join(base, "Archives")
setup_dir(archives)

sip = os.path.join(archives, "SIP")
setup_dir(sip)

aip = os.path.join(archives, "AIP")
setup_dir(aip)

automated = os.path.join(base, "automated")
setup_dir(automated)

backlog = os.path.join(base, "backlog")
setup_dir(backlog)

ingest = os.path.join(base, "ingest")
setup_dir(ingest)

logs = os.path.join(base, "processing_logs")
setup_dir(logs)
