import axios from 'redaxios';

const WIKIDATA_API_URL = 'https://www.wikidata.org/w/api.php';
const WIKIDATA_REST_URL = 'https://www.wikidata.org/w/rest.php/wikibase/v1';
const USER_AGENT = 'owl-map/1.0 (https://github.com/dpriskorn/owl-map; User:So9q)';

const wikidataApi = axios.create({
  baseURL: WIKIDATA_API_URL,
  headers: {'User-Agent': USER_AGENT},
});

const wikidataRestApi = axios.create({
  baseURL: WIKIDATA_REST_URL,
  headers: {'User-Agent': USER_AGENT},
});

export const wikidataCache = new Map();
const NEARCOORD_TTL = 60 * 60 * 1000;
const SEARCH_TTL = 5 * 60 * 1000;

function getCache(key, ttl = SEARCH_TTL) {
  const cached = wikidataCache.get(key);
  if (cached && Date.now() - cached.timestamp < ttl) {
    return cached.data;
  }
  return null;
}

function setCache(key, data) {
  wikidataCache.set(key, {data, timestamp: Date.now()});
}

export async function searchEntities(query, language = 'en') {
  if (!query || query.length < 3) return [];

  const cacheKey = `search:${query}:${language}`;
  const cached = getCache(cacheKey);
  if (cached) return cached;

  try {
    const response = await wikidataApi.get('', {
      params: {
        action: 'wbsearchentities',
        search: query,
        language: language,
        type: 'item',
        limit: 50,
        format: 'json',
      },
    });

    const results = response.data.search?.map(item => ({
      id: item.id,
      label: item.label || item.id,
      description: item.description || null,
    })) || [];

    setCache(cacheKey, results);
    return results;
  } catch (error) {
    console.error('Wikidata search failed:', error);
    if (error.response?.status === 429) {
      throw new Error('Too many requests to Wikidata. Please wait a moment and try again.');
    }
    throw new Error('Failed to search Wikidata. Check your internet connection.');
  }
}

export async function getNearbyQids(lat, lon, radiusKm) {
  const radiusM = Math.round(radiusKm * 1000);
  const cacheKey = `nearcoord:${lat.toFixed(4)}_${lon.toFixed(4)}_${radiusKm}`;

  const cached = getCache(cacheKey, NEARCOORD_TTL);
  if (cached) return cached;

  try {
    const response = await wikidataApi.get('', {
      params: {
        action: 'query',
        format: 'json',
        formatversion: 2,
        prop: 'coordinates',
        colimit: 'max',
        generator: 'search',
        gsrsearch: `nearcoord:${radiusM}m,${lat},${lon}`,
        gsrnamespace: 0,
        gsrlimit: 300,
      },
    });

    const qids = [];
    if (response.data.query?.pages) {
      const pages = response.data.query.pages;
      if (Array.isArray(pages)) {
        for (const page of pages) {
          if (page.title?.startsWith('Q')) {
            qids.push(page.title);
          }
        }
      } else {
        for (const page of Object.values(pages)) {
          if (page.title?.startsWith('Q')) {
            qids.push(page.title);
          }
        }
      }
    }

    setCache(cacheKey, qids);
    return qids;
  } catch (error) {
    console.error('Wikidata nearcoord failed:', error);
    if (error.response?.status === 429) {
      throw new Error('Too many requests to Wikidata. Please wait a moment and try again.');
    }
    throw new Error('Failed to find nearby items. Check your internet connection.');
  }
}

export async function getLabels(qids, language = 'en') {
  if (!qids || qids.length === 0) return {};

  const results = {};
  const uncached = [];

  for (const qid of qids) {
    const cacheKey = `label:${qid}:${language}`;
    const cached = wikidataCache.get(cacheKey);
    if (cached) {
      results[qid] = cached;
    } else {
      uncached.push(qid);
    }
  }

  if (uncached.length > 0) {
    await Promise.all(
      uncached.map(async (qid) => {
        const cacheKey = `label:${qid}:${language}`;
        try {
          const [labelRes, descRes] = await Promise.all([
            wikidataRestApi.get(`/entities/items/${qid}/labels/${language}`),
            wikidataRestApi.get(`/entities/items/${qid}/descriptions/${language}`).catch(() => ({data: null})),
          ]);

          const result = {
            label: labelRes.data || qid,
            description: descRes.data || null,
          };
          wikidataCache.set(cacheKey, result);
          results[qid] = result;
        } catch {
          const result = {label: qid, description: null};
          wikidataCache.set(cacheKey, result);
          results[qid] = result;
        }
      })
    );
  }

  return results;
}

export function clearCache() {
  wikidataCache.clear();
}
