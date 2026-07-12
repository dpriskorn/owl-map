import {
  searchEntities as wikidataSearchEntities,
  getNearbyQids,
  getLabels as wikidataGetLabels,
  clearCache as clearWikidataCache,
} from '../services/wikidataApi.js';

import {
  getItemsByQids,
  getP1282,
  getOsmObjectsByTag,
  getNearbyOsmObjects,
  parseOsmTag,
  clearCache as clearQleverCache,
} from '../services/qleverApi.js';

import {
  matchWikidataToOsm,
  enrichItemsWithMatchStatus,
} from '../services/matcher.js';

export function useApi() {
  let itemsAbort = null;

  const fetchItems = async (bbox, isaType = null) => {
    if (itemsAbort) {
      console.debug('fetchItems: aborting previous request');
      itemsAbort.abort();
    }
    itemsAbort = new AbortController();

    try {
      const [latMin, lonMin, latMax, lonMax] = bbox;
      const centerLat = (latMin + latMax) / 2;
      const centerLon = (lonMin + lonMax) / 2;

      const latRangeKm = (latMax - latMin) * 111.0;
      const lonRangeKm = (lonMax - lonMin) * 111.0 * Math.cos(Math.radians(centerLat));
      const radiusKm = Math.sqrt(latRangeKm ** 2 + lonRangeKm ** 2) / 2 + 1;
      const effectiveRadius = Math.max(radiusKm, 5);

      console.debug('fetchItems: finding nearby QIDs', {centerLat, centerLon, radiusKm: effectiveRadius});
      const qids = await getNearbyQids(centerLat, centerLon, effectiveRadius);
      console.debug('fetchItems: got QIDs', {count: qids.length});

      if (qids.length === 0) {
        return {data: {items: {}, osm_objects: {}, warnings: []}};
      }

      console.debug('fetchItems: fetching Wikidata items', {isaType, qidCount: qids.length});
      const wikidataResult = await getItemsByQids(qids, isaType);
      let items = wikidataResult.items;

      const filteredItems = {};
      for (const [qid, item] of Object.entries(items)) {
        const validMarkers = item.markers.filter(m =>
          latMin <= m.lat && m.lat <= latMax &&
          lonMin <= m.lon && m.lon <= lonMax
        );
        if (validMarkers.length > 0) {
          filteredItems[qid] = {...item, markers: validMarkers};
        }
      }
      items = filteredItems;

      console.debug('fetchItems: Wikidata items after bbox filter', {count: Object.keys(items).length});

      const warnings = [];
      let osmObjects = {};
      let osmTagInfo = null;

      if (isaType) {
        const p1282Value = await getP1282(isaType);
        if (p1282Value) {
          osmTagInfo = parseOsmTag(p1282Value);
          if (osmTagInfo) {
            console.debug('fetchItems: querying OSM for', osmTagInfo);
            osmObjects = await getOsmObjectsByTag(osmTagInfo.key, osmTagInfo.value, bbox);
            console.debug('fetchItems: OSM objects found', {count: Object.keys(osmObjects).length});
          }
        } else {
          warnings.push({
            type: 'no_p1282',
            message: `ISA type ${isaType} has no P1282 OSM tag`,
            url: `https://www.wikidata.org/wiki/${isaType}`,
          });
        }
      }

      const matchResult = matchWikidataToOsm(items, osmObjects);
      const enrichedItems = enrichItemsWithMatchStatus(items, matchResult);

      console.debug('fetchItems: results', {
        wikidata: Object.keys(enrichedItems).length,
        osm: Object.keys(osmObjects).length,
        matched: matchResult.matched.length,
        wikidata_only: matchResult.wikidata_only.length,
        osm_only: matchResult.osm_only.length,
      });

      return {
        data: {
          items: enrichedItems,
          osm_objects: osmObjects,
          warnings,
        },
      };
    } catch (error) {
      console.error('fetchItems error:', error);
      throw error;
    }
  };

  const fetchNearbyOsmObjects = async (osmTagKey, osmTagValue, lat, lon, limit = 10) => {
    try {
      return await getNearbyOsmObjects(osmTagKey, osmTagValue, lat, lon, limit);
    } catch (error) {
      console.error('fetchNearbyOsmObjects error:', error);
      throw error;
    }
  };

  const searchWikidata = async (query, language = null) => {
    try {
      const lang = language || navigator.language?.split('-')[0] || 'en';
      return await wikidataSearchEntities(query, lang);
    } catch (error) {
      console.error('searchWikidata error:', error);
      throw error;
    }
  };

  const fetchLabels = async (qids, language = null) => {
    try {
      return await wikidataGetLabels(qids, language);
    } catch (error) {
      console.error('fetchLabels error:', error);
      throw error;
    }
  };

  const clearAllCaches = () => {
    clearWikidataCache();
    clearQleverCache();
  };

  return {
    fetchItems,
    fetchNearbyOsmObjects,
    searchWikidata,
    fetchLabels,
    clearAllCaches,
  };
}
