# OWL Map

Links Wikidata items to OpenStreetMap objects using SPARQL queries.

## Architecture

Frontend-only SPA that queries:
- **Wikidata API** - Search and nearcoord for finding items
- **Qlever (Wikidata)** - Coordinate and type queries
- **Qlever (OSM)** - OSM object queries

## Quick Start

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on port 3000.

## Configuration

Environment variables in `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_DEFAULT_LAT` | `62.3913` | Default map center latitude |
| `VITE_DEFAULT_LON` | `17.3068` | Default map center longitude |
| `VITE_DEFAULT_ZOOM` | `8` | Default zoom level |
| `VITE_MIN_ZOOM` | `13` | Minimum zoom for item search |

## Development

```bash
npm run dev     # Start dev server
npm run build   # Production build
npm run lint    # Run ESLint
npm run test    # Run tests
```
