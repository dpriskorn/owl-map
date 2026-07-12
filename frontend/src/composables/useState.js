import {reactive, computed} from 'vue';

export function useState() {
  const state = reactive({
    // Map state
    map: null,
    map_area: 0,
    loading: false,
    area_too_big: false,
    too_many_items: false,
    bounds_before_open: null,
    zoom_on_open: true,

    // Items
    items: {},
    item_count: 0,
    current_item: null,
    current_osm: null,
    selected_marker: null,
    selected_items: {},
    selected_circles: [],
    candidate_outline: null,

    // Search
    hits: [],
    current_hit: null,
    recent_search: null,

    // Edits
    edits: [],
    upload_state: undefined,
    upload_progress: 0,
    upload_error: null,
    changeset_id: null,
    changeset_comment: '+wikidata',
    view_edits: false,

    // Filters
    linked: true,
    not_linked: true,
    isa_ticked: [],
    show_item_type_filter: false,
    item_type_search: '',
    item_type_hits: [],
    wikidata_search_results: [],

    // OSM objects
    osm_objects: {},

    // Item detail
    wd_item: null,

    // Warnings
    p1282_warning: null,

    // Auth
    username: null,
    user: null,

    // Error
    api_call_error_message: null,
    api_call_error_traceback: null,
  });

  // Items computed
  const itemsList = computed(() => Object.values(state.items));

  const visibleItems = computed(() => {
    const result = itemsList.value.filter(item => {
      if (!item.markers || !item.markers.length) return false;
      return true;
    });
    console.debug('visibleItems computed', {filteredCount: result.length, allCount: itemsList.value.length});
    return result;
  });

  const itemCount = computed(() => Object.keys(state.items).length);

  // Search computed
  const hasSearchResults = computed(() => state.hits.length > 0);
  const hasOneSearchResult = computed(() => state.hits.length === 1);

  // Edits computed
  const hasEdits = computed(() => state.edits.length > 0);
  const editsCount = computed(() => state.edits.length);

  const uploadsGroupedByQid = computed(() => {
    const qidOrder = [];
    const lookup = {};
    state.edits.forEach(edit => {
      const qid = edit.item.qid;
      if (!lookup[qid]) {
        qidOrder.push(qid);
        lookup[qid] = {qid, wikidata: edit.item.wikidata, osm: []};
      }
      lookup[qid].osm.push(edit.osm);
    });
    return qidOrder.map(qid => lookup[qid]);
  });

  // Item actions
  const setItems = (itemsObj) => {
    console.debug('setItems called', {count: Object.keys(itemsObj).length, qids: Object.keys(itemsObj)});
    state.items = {...itemsObj};
    console.debug('setItems done', {itemCount: Object.keys(state.items).length});
  };

  const setOsmObjects = (osmObj) => {
    console.debug('setOsmObjects called', {count: Object.keys(osmObj).length});
    state.osm_objects = {...osmObj};
  };

  const setP1282Warning = (warning) => {
    state.p1282_warning = warning;
  };

  const clearP1282Warning = () => {
    state.p1282_warning = null;
  };

  const addItem = (qid, item) => {
    state.items[qid] = item;
  };

  const openItem = (item) => {
    state.current_item = item;
    state.current_osm = null;
    state.selected_marker = null;
    state.wd_item = null;
  };

  const closeItem = () => {
    state.current_item = null;
    state.current_osm = null;
    state.selected_marker = null;
  };

  const setWikidataDetail = (qid, detail) => {
    if (state.items[qid]) {
      state.items[qid].wikidata = detail;
    }
    if (state.current_item?.qid === qid) {
      state.wd_item = detail;
    }
  };

  // OSM actions
  const setCurrentOsm = (osm) => {
    state.current_osm = osm;
  };

  const selectOsm = (osm, selected) => {
    osm.selected = selected;
  };

  // Edit actions
  const addEdit = (item, osm) => {
    const idx = state.edits.findIndex(
      e => e.item.qid === item.qid && e.osm.identifier === osm.identifier
    );
    if (idx !== -1) {
      state.edits.splice(idx, 1);
    } else {
      state.edits.push({item, osm});
    }
  };

  const clearEdits = () => {
    state.edits = [];
  };

  // Search actions
  const setHits = (hits) => {
    state.hits = hits;
  };

  const setCurrentHit = (hit) => {
    state.current_hit = hit;
  };

  // Filter actions
  const toggleIsa = (qid) => {
    if (state.isa_ticked.includes(qid)) {
      state.isa_ticked = [];
    } else {
      state.isa_ticked = [qid];
    }
  };

  const clearIsaFilters = () => {
    state.isa_ticked = [];
    state.item_type_search = '';
  };

  const setItemTypeHits = (hits) => {
    state.item_type_hits = hits;
  };

  const setWikidataSearchResults = (results) => {
    state.wikidata_search_results = results;
  };

  // UI actions
  const setLoading = (loading) => {
    state.loading = loading;
  };

  const setAreaTooBig = (value) => {
    state.area_too_big = value;
  };

  const setTooManyItems = (value) => {
    state.too_many_items = value;
  };

  const setError = (message, traceback = null) => {
    state.api_call_error_message = message;
    state.api_call_error_traceback = traceback;
  };

  const clearError = () => {
    state.api_call_error_message = null;
    state.api_call_error_traceback = null;
  };

  const setUploadState = (uploadState, extra = {}) => {
    state.upload_state = uploadState;
    Object.assign(state, extra);
  };

  const resetUpload = () => {
    state.upload_state = undefined;
    state.upload_progress = 0;
    state.upload_error = null;
    state.changeset_id = null;
  };

  return {
    state,
    // Computed
    itemsList,
    visibleItems,
    itemCount,
    hasSearchResults,
    hasOneSearchResult,
    hasEdits,
    editsCount,
    uploadsGroupedByQid,
    // Item actions
    setItems,
    addItem,
    openItem,
    closeItem,
    setWikidataDetail,
    // OSM actions
    setCurrentOsm,
    selectOsm,
    // Edit actions
    addEdit,
    clearEdits,
    // Search actions
    setHits,
    setCurrentHit,
    // Filter actions
    toggleIsa,
    clearIsaFilters,
    setItemTypeHits,
    setWikidataSearchResults,
    // UI actions
    setLoading,
    setAreaTooBig,
    setTooManyItems,
    setError,
    clearError,
    setUploadState,
    resetUpload,
    // OSM
    setOsmObjects,
    setP1282Warning,
    clearP1282Warning,
  };
}
