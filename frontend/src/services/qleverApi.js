import axios from 'redaxios';

const QLEVER_WIKIDATA_URL = 'https://qlever.cs.uni-freiburg.de/api/wikidata';
const QLEVER_OSM_URL = 'https://qlever.dev/osm-planet';
const USER_AGENT = 'owl-map/1.0 (https://github.com/dpriskorn/owl-map; User:So9q)';

const qleverWikidata = axios.create({
  baseURL: QLEVER_WIKIDATA_URL,
  headers: {'User-Agent': USER_AGENT},
});

const qleverOsm = axios.create({
  baseURL: QLEVER_OSM_URL,
  headers: {'User-Agent': USER_AGENT},
});

export const qleverCache = new Map();
const QLEVER_TTL = 5 * 60 * 1000;

function getCache(key) {
  const cached = qleverCache.get(key);
  if (cached && Date.now() - cached.timestamp < QLEVER_TTL) {
    return cached.data;
  }
  return null;
}

function setCache(key, data) {
  qleverCache.set(key, {data, timestamp: Date.now()});
}

function parsePoint(coordStr) {
  const match = coordStr.match(/POINT\(([0-9.-]+) ([0-9.-]+)\)/);
  if (match) {
    const lon = parseFloat(match[1]);
    const lat = parseFloat(match[2]);
    return {lat, lon};
  }
  return null;
}

async function executeQuery(endpoint, query) {
  console.debug('Qlever query:', query.substring(0, 200));
  const response = await endpoint.get('', {
    params: {query, action: 'json_export'},
    timeout: 60000,
  });
  return response.data;
}

export async function getItemsByQids(qids, isaType = null) {
  if (!qids || qids.length === 0) {
    return {items: {}, isa_count: []};
  }

  const cacheKey = `wikidata_items:${qids.sort().join(',')}:${isaType || 'none'}`;
  const cached = getCache(cacheKey);
  if (cached) return cached;

  const valuesClause = qids.map(qid => `wd:${qid}`).join(' ');

  let isaFilter = '';
  if (isaType) {
    isaFilter = `?item wdt:P31 wd:${isaType} .`;
  }

  const query = `PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX bd: <http://www.bigdata.com/rdf#>
SELECT ?item (STR(?coord) AS ?coord_str) WHERE {
  VALUES ?item { ${valuesClause} }
  ?item wdt:P625 ?coord .
  ${isaFilter}
}
LIMIT ${qids.length * 2}`;

  const result = await executeQuery(qleverWikidata, query);

  const items = {};
  try {
    for (const binding of result.results.bindings) {
      const qid = binding.item.value.split('/').pop();
      const coords = parsePoint(binding.coord_str.value);
      if (coords) {
        if (!items[qid]) {
          items[qid] = {qid, markers: []};
        }
        items[qid].markers.push(coords);
      }
    }
  } catch (e) {
    console.error('Error parsing Qlever results:', e);
  }

  const data = {items, isa_count: []};
  setCache(cacheKey, data);
  return data;
}

export async function getP1282(qid) {
  const cacheKey = `p1282:${qid}`;
  const cached = getCache(cacheKey);
  if (cached !== null) return cached;

  const query = `PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX bd: <http://www.bigdata.com/rdf#>
SELECT ?osm_tag WHERE {
  wd:${qid} wdt:P1282 ?osm_tag .
}`;

  try {
    const result = await executeQuery(qleverWikidata, query);
    if (result.results.bindings.length > 0) {
      const osmTag = result.results.bindings[0].osm_tag.value;
      setCache(cacheKey, osmTag);
      return osmTag;
    }
  } catch (e) {
    console.error('Error getting P1282:', e);
  }

  setCache(cacheKey, null);
  return null;
}

export async function getOsmObjectsByTag(tagKey, tagValue, bbox) {
  if (!bbox || bbox.length !== 4) {
    return {};
  }

  const [latMin, lonMin, latMax, lonMax] = bbox;
  const cacheKey = `osm:${tagKey}:${tagValue}:${bbox.join(',')}`;
  const cached = getCache(cacheKey);
  if (cached) return cached;

  const polygon = `POLYGON((${lonMin} ${latMin}, ${lonMax} ${latMin}, ${lonMax} ${latMax}, ${lonMin} ${latMax}, ${lonMin} ${latMin}))`;

  const query = `PREFIX osmkey: <https://www.openstreetmap.org/wiki/Key:>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX osm2rdfkey: <https://osm2rdf.cs.uni-freiburg.de/rdf/key#>
SELECT ?osm_id ?geometry ?wikidata WHERE {
  ?osm_id osmkey:${tagKey} "${tagValue}" .
  ?osm_id geo:hasGeometry/geo:asWKT ?geometry .
  OPTIONAL { ?osm_id osm2rdfkey:wikidata ?wikidata }
  FILTER(geof:sfIntersects(?geometry, "${polygon}"^^geo:wktLiteral))
}
LIMIT 500`;

  const result = await executeQuery(qleverOsm, query);

  const objects = {};
  try {
    for (const binding of result.results.bindings) {
      const osmId = binding.osm_id.value;
      const coords = parsePoint(binding.geometry.value);
      const wikidataRef = binding.wikidata?.value?.split('/').pop() || null;

      if (coords) {
        if (!objects[osmId]) {
          objects[osmId] = {osm_id: osmId, markers: [], wikidata_qid: wikidataRef};
        }
        objects[osmId].markers.push(coords);
      }
    }
  } catch (e) {
    console.error('Error parsing OSM results:', e);
  }

  setCache(cacheKey, objects);
  return objects;
}

export async function getNearbyOsmObjects(tagKey, tagValue, lat, lon, limit = 10) {
  const cacheKey = `osm_nearby:${tagKey}:${tagValue}:${lat.toFixed(4)}:${lon.toFixed(4)}:${limit}`;
  const cached = getCache(cacheKey);
  if (cached) return cached;

  const centerWkt = `Point(${lon} ${lat})`;

  const query = `PREFIX osmkey: <https://www.openstreetmap.org/wiki/Key:>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX geof: <http://www.opengis.net/def/function/geosparql#>
PREFIX osm2rdfkey: <https://osm2rdf.cs.uni-freiburg.de/rdf/key#>
SELECT ?osm_id ?geometry ?wikidata (geof:distance(?geometry, "${centerWkt}"^^geo:wktLiteral) AS ?distance) WHERE {
  ?osm_id osmkey:${tagKey} "${tagValue}" .
  ?osm_id geo:hasGeometry/geo:asWKT ?geometry .
  OPTIONAL { ?osm_id osm2rdfkey:wikidata ?wikidata }
}
ORDER BY ?distance
LIMIT ${limit}`;

  const result = await executeQuery(qleverOsm, query);

  const objects = [];
  try {
    for (const binding of result.results.bindings) {
      const osmId = binding.osm_id.value;
      const coords = parsePoint(binding.geometry.value);
      const wikidataRef = binding.wikidata?.value?.split('/').pop() || null;
      const distance = parseFloat(binding.distance.value);

      if (coords) {
        objects.push({
          osm_id: osmId,
          lat: coords.lat,
          lon: coords.lon,
          wikidata_qid: wikidataRef,
          distance,
        });
      }
    }
  } catch (e) {
    console.error('Error parsing nearby OSM results:', e);
  }

  setCache(cacheKey, objects);
  return objects;
}

export function parseOsmTag(p1282Value) {
  if (!p1282Value || !p1282Value.includes('=')) {
    return null;
  }
  const [key, value] = p1282Value.split('=');
  return {key: key.trim(), value: value.trim()};
}

export function clearCache() {
  qleverCache.clear();
}
