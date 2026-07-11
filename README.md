# OWL Map

Links Wikidata items to OpenStreetMap objects.

## PostGIS Setup

OWL Map requires a PostgreSQL database with PostGIS and OSM data imported via osm2pgsql.

### 1. Create Database

```bash
createdb osm
psql -d osm -c "CREATE EXTENSION postgis;"
```

### 2. Download OSM Extract

Download an OSM extract for your region of interest. Example using Sweden:

```bash
wget https://download.geofabrik.de/europe/sweden-latest.osm.pbf
```

For other regions, browse [Geofabrik's download site](https://download.geofabrik.de/).

### 3. Import OSM Data

The repository includes `style.lua` for osm2pgsql's flex output:

```bash
osm2pgsql \
    --create \
    --output flex \
    --style style.lua \
    --slim \
    --database osm \
    --cache 4000 \
    --number-processes $(nproc) \
    sweden-latest.osm.pbf
```

Adjust `--cache` and `--number-processes` based on your system's RAM and CPU cores.

### 4. Set Database URL

```bash
export DATABASE_URL="postgresql:///osm"
```

## Quick Start

### Backend

```bash
poetry install
just api
```

API runs on port 8080.

### Frontend

```bash
cd frontend
npm install
just vite
```

Frontend runs on port 3000 with proxy to API on 8080.

### Tests

```bash
just test-all
```

Runs both backend (pytest) and frontend (vitest) tests.

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql:///matcher` | PostgreSQL connection string |
| `SECRET_KEY` | `dev-secret-key` | Session secret key |
| `GEOLITE2` | (none) | Path to GeoLite2 database for IP geolocation |
