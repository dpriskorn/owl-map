import axios from 'redaxios';

const api_base_url = import.meta.env.VITE_API_URL || '';

export function useApi() {
  const api_call = async (path, options = {}) => {
    const url = `${api_base_url}/api/1/${path}`;
    try {
      const response = await axios({url, ...options});
      return response;
    } catch (error) {
      const api_call_error_message = error.response?.data?.error || error.message;
      const api_call_error_traceback = error.response?.data?.traceback;
      throw {api_call_error_message, api_call_error_traceback};
    }
  };

  const fetchItems = async (bbox, types = [], itemType = '') => {
    const params = {
      bbox: bbox.join(','),
      types: types.join(','),
      type: itemType,
    };
    return api_call('items', {params});
  };

  const fetchItemCount = async (bbox, types = [], itemType = '') => {
    const params = {
      bbox: bbox.join(','),
      types: types.join(','),
      type: itemType,
    };
    return api_call('count', {params});
  };

  const fetchItemDetail = async (qid) => {
    return api_call(`item/Q${qid}`);
  };

  const fetchItemTags = async (qid) => {
    return api_call(`item/Q${qid}/tags`);
  };

  const fetchItemCandidates = async (qid, radius = 1000) => {
    return api_call(`item/Q${qid}/candidates`, {params: {radius}});
  };

  const fetchIsaCounts = async (bbox) => {
    return api_call('isa', {params: {bbox: bbox.join(',')}});
  };

  const fetchIsaSearch = async (query) => {
    return api_call('isa_search', {params: {q: query}});
  };

  const fetchMissing = async (qids, lat, lon) => {
    return api_call('missing', {params: {qids: qids.join(','), lat, lon}});
  };

  const fetchLocation = async (ip) => {
    return api_call('location', {params: {ip}});
  };

  const fetchOsmObjects = async (bbox, isaFilter = []) => {
    return api_call('osm', {
      params: {
        bounds: bbox.join(','),
        isa: isaFilter.join(','),
      },
    });
  };

  const fetchPlaceItems = async (osmType, osmId) => {
    return api_call(`place/${osmType}/${osmId}`);
  };

  const fetchPolygon = async (osmType, osmId) => {
    return api_call(`polygon/${osmType}/${osmId}`);
  };

  const search = async (query) => {
    return api_call('search', {params: {q: query}});
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

  return {
    api_call,
    fetchItems,
    fetchItemCount,
    fetchItemDetail,
    fetchItemTags,
    fetchItemCandidates,
    fetchIsaCounts,
    fetchIsaSearch,
    fetchMissing,
    fetchLocation,
    fetchOsmObjects,
    fetchPlaceItems,
    fetchPolygon,
    search,
    createEditSession,
    updateEditSession,
    getCommonsUrl,
    healthCheck,
    api_base_url,
  };
}
