# Processing

A Flask wrapper app for a [digital records processing workflow](https://github.com/UAlbanyArchives/ingest-processing-workflow).

Get code:
```
git clone git@github.com:UAlbanyArchives/processing.git
cd processing
```

### For development
This lets you edit files while they're served from the container.

If you don't have the default development test directories required, you can create them with:
```
python setup-dev.py
```

Run the app:
```
docker-compose -f docker-compose-dev.yml up
```

Navigate to [http://localhost:5000](http://localhost:5000)

When you're done:
```
docker-compose down
```

### For deployment

Building the `processing` image:
(FYI you need .archivessnake.yml and .hyrax.yml)
```
docker build -t "processing" .
```

Running the image
```
docker-compose up -d
```
Navigate to [http://localhost:5000](http://localhost:5000)

To stop:
```
docker-compose down
```

This needs an `.env` or environment variable with:
```
FLASK_SECRET_KEY=value
```

### For a terminal

If you need another terminal:
```
docker exec -it processing_flask1_1 /bin/bash
```