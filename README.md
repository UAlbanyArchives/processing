# Processing

A Flask wrapper app for a [digital records processing workflow](https://github.com/UAlbanyArchives/ingest-processing-workflow).

This is just for testing at the moment, so the Dockerfile isn't set up yet and there isn't a . Instead run this:

Get code:
```
git clone git@github.com:UAlbanyArchives/processing.git
cd processing
```

### For development
This lets you edit files while they're served from the container.

If you don't have the test directories required, you can create them with:
```
python setup-dev.py
```

Run the app:
```
docker-compose -f docker-compose.yml -f docker-compose-dev.yml up
```

For another terminal:
```
docker exec -it processing_flask1_1 /bin/bash
```

Navigate to [http://localhost:5000](http://localhost:5000)

When you're done:
```
docker-compose down
```

### For deployment
(Not currently working right)
```
docker build -t "processing" .
docker-compose -f docker-compose-prod.yml up
```
Navigate to [http://localhost:5000](http://localhost:5000)
