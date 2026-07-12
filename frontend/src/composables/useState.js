import {reactive, computed} from 'vue';

export function useState() {
  const state = reactive({
    // Map state
    loading: false,
    area_too_big: false,
    too_many_items: false,

    // Items
    items: {},
    item_count: 0,
    current_item: null,
    current_osm: null,
    selected_marker: null,

    // Search
    hits: [],
    current_hit: null,
    recent_search: null,

    // Filters
    item_type_ticked: [],
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

    // Error
    error: null,
  });

  // Items computed
  const itemsList = computed(() => Object.values(state.items));

  const visibleItems = computed(() => {
    return itemsList.value.filter(item => {
      if (!item.markers || !item.markers.length) return false;
      return true;
    });
  });

  const itemCount = computed(() => Object.keys(state.items).length);

  // Search computed
  const hasSearchResults = computed(() => state.hits.length > 0);
  const hasOneSearchResult = computed(() => state.hits.length === 1);

  // Item actions
  const setItems = (itemsObj) => {
    console.debug('setItems called', {count: Object.keys(itemsObj).length});
    state.items = {...itemsObj};
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

  // Search actions
  const setHits = (hits) => {
    state.hits = hits;
  };

  const setCurrentHit = (hit) => {
    state.current_hit = hit;
  };

  // Filter actions
  const toggleItemType = (qid) => {
    if (state.item_type_ticked.includes(qid)) {
      state.item_type_ticked = [];
    } else {
      state.item_type_ticked = [qid];
    }
  };

  const clearItemTypeFilters = () => {
    state.item_type_ticked = [];
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

  const setError = (message) => {
    state.error = message;
  };

  const clearError = () => {
    state.error = null;
  };

  return {
    state,
    // Computed
    itemsList,
    visibleItems,
    itemCount,
    hasSearchResults,
    hasOneSearchResult,
    // Item actions
    setItems,
    openItem,
    closeItem,
    setWikidataDetail,
    // OSM
    setOsmObjects,
    setP1282Warning,
    clearP1282Warning,
    // Search actions
    setHits,
    setCurrentHit,
    // Filter actions
    toggleItemType,
    clearItemTypeFilters,
    setItemTypeHits,
    setWikidataSearchResults,
    // UI actions
    setLoading,
    setAreaTooBig,
    setTooManyItems,
    setError,
    clearError,
  };
}
