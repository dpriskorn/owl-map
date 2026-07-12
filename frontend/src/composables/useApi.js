import axios from 'redaxios';

const api_base_url = import.meta.env.VITE_API_URL || '';
const wikidata_api_url = 'https://www.wikidata.org/w/rest.php/wikibase/v1';
const user_agent = 'owl-map/1.0 (https://github.com/dpriskorn/owl-map)';

export function useApi() {
  const api_call = async (path, options = {}) => {
    const url = `${api_base_url}/api/1/${path}`;
    console.debug('api_call starting', {url, path, hasSignal: !!options.signal});
    try {
      const response = await axios({url, ...options});
      console.debug('api_call completed', {url, status: response.status});
      return response;
    } catch (error) {
      console.error('api_call failed', {url, err: error.message, status: error.response?.status});
      const api_call_error_message = error.response?.data?.error || error.message;
      const api_call_error_traceback = error.response?.data?.traceback;
      throw {api_call_error_message, api_call_error_traceback};
    }
  };

  let itemsAbort = null;

  const fetchItems = async (bbox, isaTypes = null) => {
    if (itemsAbort) {
      console.debug('fetchItems: aborting previous request');
      itemsAbort.abort();
    }
    itemsAbort = new AbortController();
    const params = {bbox: bbox.join(',')};
    if (isaTypes && isaTypes.length > 0) {
      params.isa = isaTypes.join(',');
    }
    console.debug('fetchItems: making request', {params});
    try {
      const result = await api_call('items', {params, signal: itemsAbort.signal});
      console.debug('fetchItems: got result', {itemCount: Object.keys(result.data.items || {}).length});
      return result;
    } catch (err) {
      if (axios.isCancel(err) || err.name === 'CanceledError') {
        console.debug('fetchItems: request was cancelled');
        return {data: {items: {}}};
      }
      console.error('fetchItems: request failed', {err});
      throw err;
    }
  };

  const fetchItemCount = async (bbox) => {
    const params = {bbox: bbox.join(',')};
    return api_call('count', {params});
  };

  let isaAbort = null;

  const fetchIsaCounts = async (bbox) => {
    if (isaAbort) isaAbort.abort();
    isaAbort = new AbortController();
    try {
      return await api_call('isa', {params: {bbox: bbox.join(',')}, signal: isaAbort.signal});
    } catch (err) {
      if (axios.isCancel(err) || err.name === 'CanceledError') return {data: {isa_count: []}};
      throw err;
    }
  };

  const fetchLocation = async (ip) => {
    return api_call('location', {params: {ip}});
  };

  const fetchOsmObjects = async (bbox) => {
    return api_call('osm', {params: {bounds: bbox.join(',')}});
  };

  const search = async (query, bbox = null) => {
    const params = {q: query};
    if (bbox) {
      params.bbox = bbox.join(',');
    }
    return api_call('search', {params});
  };

  const createEditSession = async (comment, editList) => {
    return api_call('edit', {
      method: 'POST',
      data: {comment, edit_list: editList},
    });
  };

  const updateEditSession = async (sessionId, editList) => {
    return api_call(`edit/${sessionId}`, {
      method: 'POST',
      data: {edit_list: editList},
    });
  };

  const getCommonsUrl = (filename) => `${api_base_url}/commons/${filename}`;

  const healthCheck = async () => {
    try {
      const response = await axios.get(`${api_base_url}/health`);
      return response.data?.status === 'ok';
    } catch {
      return false;
    }
  };

  const getBrowserLanguage = () => {
    const lang = navigator.language || navigator.userLanguage || 'en';
    return lang.split('-')[0];
  };

  const fetchLabels = async (qids, language = null) => {
    if (!qids || qids.length === 0) return {};
    const lang = language || getBrowserLanguage();
    const results = {};
    await Promise.all(
      qids.map(async (qid) => {
        try {
          const response = await axios.get(
            `${wikidata_api_url}/entities/items/${qid}/labels`,
            {headers: {'User-Agent': user_agent}, params: {language: lang}, timeout: 10000}
          );
          results[qid] = response.data;
        } catch {
          results[qid] = {};
        }
      })
    );
    return results;
  };

  const wikidataCache = new Map();

  const fetchWikidataDetails = async (qids, language = null) => {
    if (!qids || qids.length === 0) return {};
    const lang = language || getBrowserLanguage();
    const results = {};
    const uncached = [];

    for (const qid of qids) {
      const cacheKey = `${qid}:${lang}`;
      if (wikidataCache.has(cacheKey)) {
        results[qid] = wikidataCache.get(cacheKey);
      } else {
        uncached.push(qid);
      }
    }

    if (uncached.length > 0) {
      await Promise.all(
        uncached.map(async (qid) => {
          const cacheKey = `${qid}:${lang}`;
          try {
            const [labelRes, descRes] = await Promise.all([
              axios.get(
                `${wikidata_api_url}/entities/items/${qid}/labels/${lang}`,
                {headers: {'User-Agent': user_agent}, timeout: 10000}
              ),
              axios.get(
                `${wikidata_api_url}/entities/items/${qid}/descriptions/${lang}`,
                {headers: {'User-Agent': user_agent}, timeout: 10000}
              ).catch(() => ({data: null})),
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
  };

  const clearWikidataCache = () => {
    wikidataCache.clear();
  };

  let wikidataSearchAbort = null;

  const searchWikidata = async (query, language = null) => {
    if (!query || query.length < 3) return [];
    const lang = language || getBrowserLanguage();
    if (wikidataSearchAbort) {
      wikidataSearchAbort.abort();
    }
    wikidataSearchAbort = new AbortController();
    try {
      const response = await axios.get(`${api_base_url}/api/1/wikidata_search`, {
        params: {q: query, language: lang},
        timeout: 10000,
        signal: wikidataSearchAbort.signal,
      });
      return response.data.results || [];
    } catch (err) {
      if (axios.isCancel(err) || err.name === 'CanceledError') return [];
      return [];
    }
  };

  return {
    api_call,
    fetchItems,
    fetchItemCount,
    fetchIsaCounts,
    fetchLocation,
    fetchOsmObjects,
    search,
    createEditSession,
    updateEditSession,
    getCommonsUrl,
    healthCheck,
    fetchLabels,
    fetchWikidataDetails,
    clearWikidataCache,
    searchWikidata,
    api_base_url,
  };
}
