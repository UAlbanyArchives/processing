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

Build the image:
```
docker build -t "processing" .
```

Once the image is built you can run the app in development mode without rebuilding:
```
docker-compose up
```

Navigate to [http://localhost:5000](http://localhost:5000)

When you're done:
```
docker-compose down
```

### For deployment

This needs an `.env` or environment variable with:
```
FLASK_SECRET_KEY=value
```
This also needs ~/.archivessnake.yml config and ~/.description_harvester config.

Building the `processing` image:
```
make build
```

Restarting the service:
```
make restart
```

Navigate to [http://localhost:5000](http://localhost:5000)

## On Windows
Raw commands without Makefile:
```
docker build -t "processing" .
```
Running the image
```
docker-compose up -d
```

### For a terminal

If you need another terminal:
```
docker exec -it processing_flask1_1 /bin/bash
```