# Processing

A Flask wrapper app for a [digital records processing workflow](https://github.com/UAlbanyArchives/ingest-processing-workflow).

This is just for testing at the moment, so the Dockerfile isn't set up yet and there isn't a . Instead run this:

Get code:
```
git clone git@github.com:UAlbanyArchives/processing.git
cd processing
```

### For development
```
docker pull python:3.11.2-slim-buster
docker run --name flask1 -dit -p 5000:5000 -v ${PWD}:/flask1 python
docker exec -it flask1 /bin/bash
```
In docker container:
```
cd flask1
pip install -r requirements.txt
export FLASK_DEBUG="1" 
flask run --host=0.0.0.0
```
Navigate to [http://localhost:5000](http://localhost:5000)

If you stop the container, it might be easiest to just delete it and run everything from `docker run ...` down.

### For deployment
```
docker build -t "processing" .
docker run -d -p 5000:5000 processing
```
Navigate to [http://localhost:5000](http://localhost:5000)
