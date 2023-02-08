# Processing

A Flask wrapper app for a [digital records processing workflow](https://github.com/UAlbanyArchives/ingest-processing-workflow).

```
docker run --name flask1 -dit -p 5000:5000 -v ${PWD}:/flask1 python
docker exec -it flask1 /bin/bash
flask run --host=0.0.0.0
```
