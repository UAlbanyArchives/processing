# Processing

A Flask wrapper app for a [digital records processing workflow](https://github.com/UAlbanyArchives/ingest-processing-workflow).

This is just for testing at the moment, so the Dockerfile isn't working yet. Instead run this:

Get code:
```
git clone git@github.com:UAlbanyArchives/processing.git
cd processing
```
Run docker:
```
docker pull python:latest
docker run --name flask1 -dit -p 5000:5000 -v ${PWD}:/flask1 python
docker exec -it flask1 /bin/bash
```
In docker container:
```
cd flask1
export FLASK_DEBUG="1" 
pip install flask
pip install wtforms
flask run --host=0.0.0.0
```

Navigate to [http://localhost:5000](http://localhost:5000)
