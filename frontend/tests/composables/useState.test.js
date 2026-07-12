import {describe, it, expect, beforeEach} from 'vitest';
import {useState} from '../../src/composables/useState.js';

describe('useState', () => {
  let state, visibleItems, itemCount;
  let setItems, openItem, closeItem, setWikidataDetail, setLoading, setError;
  let clearError, setHits, setCurrentHit;
  let toggleItemType, clearItemTypeFilters;
  let setOsmObjects, setP1282Warning, clearP1282Warning;

  beforeEach(() => {
    const result = useState();
    state = result.state;
    visibleItems = result.visibleItems;
    itemCount = result.itemCount;
    setItems = result.setItems;
    openItem = result.openItem;
    closeItem = result.closeItem;
    setWikidataDetail = result.setWikidataDetail;
    setLoading = result.setLoading;
    setError = result.setError;
    clearError = result.clearError;
    setHits = result.setHits;
    setCurrentHit = result.setCurrentHit;
    toggleItemType = result.toggleItemType;
    clearItemTypeFilters = result.clearItemTypeFilters;
    setOsmObjects = result.setOsmObjects;
    setP1282Warning = result.setP1282Warning;
    clearP1282Warning = result.clearP1282Warning;
  });

  describe('state initial values', () => {
    it('has correct initial state', () => {
      expect(state.loading).toBe(false);
      expect(state.items).toEqual({});
      expect(state.current_item).toBe(null);
      expect(state.hits).toEqual([]);
      expect(state.item_type_ticked).toEqual([]);
      expect(state.error).toBe(null);
      expect(state.osm_objects).toEqual({});
      expect(state.p1282_warning).toBe(null);
    });
  });

  describe('setItems', () => {
    it('sets items', () => {
      const items = {Q1: {qid: 'Q1', label: 'Test'}, Q2: {qid: 'Q2', label: 'Test2'}};
      setItems(items);
      expect(state.items).toEqual(items);
    });
  });

  describe('setOsmObjects', () => {
    it('sets OSM objects', () => {
      const osmObjects = {'node/1': {osm_id: 'node/1', markers: [{lat: 1, lon: 1}]}};
      setOsmObjects(osmObjects);
      expect(state.osm_objects).toEqual(osmObjects);
    });
  });

  describe('setP1282Warning / clearP1282Warning', () => {
    it('sets and clears P1282 warning', () => {
      const warning = {type: 'no_p1282', message: 'No P1282', url: 'https://wikidata.org'};
      setP1282Warning(warning);
      expect(state.p1282_warning).toEqual(warning);
      clearP1282Warning();
      expect(state.p1282_warning).toBe(null);
    });
  });

  describe('openItem / closeItem', () => {
    it('opens an item', () => {
      const item = {qid: 'Q1', label: 'Test'};
      openItem(item);
      expect(state.current_item).toStrictEqual(item);
      expect(state.current_osm).toBe(null);
    });

    it('closes an item', () => {
      state.current_item = {qid: 'Q1'};
      state.current_osm = {id: 1};
      state.selected_marker = {};
      closeItem();
      expect(state.current_item).toBe(null);
      expect(state.current_osm).toBe(null);
      expect(state.selected_marker).toBe(null);
    });
  });

  describe('setWikidataDetail', () => {
    it('updates wikidata detail for item in items', () => {
      state.items.Q1 = {qid: 'Q1'};
      setWikidataDetail('Q1', {label: 'Updated'});
      expect(state.items.Q1.wikidata).toEqual({label: 'Updated'});
    });

    it('updates wd_item when current_item matches', () => {
      state.items.Q1 = {qid: 'Q1'};
      state.current_item = {qid: 'Q1'};
      setWikidataDetail('Q1', {label: 'Detail'});
      expect(state.wd_item).toEqual({label: 'Detail'});
    });
  });

  describe('setLoading', () => {
    it('sets loading state', () => {
      setLoading(true);
      expect(state.loading).toBe(true);
      setLoading(false);
      expect(state.loading).toBe(false);
    });
  });

  describe('setError / clearError', () => {
    it('sets error message', () => {
      setError('Something went wrong');
      expect(state.error).toBe('Something went wrong');
    });

    it('clears error', () => {
      setError('Error');
      clearError();
      expect(state.error).toBe(null);
    });
  });

  describe('setHits / setCurrentHit', () => {
    it('sets search hits', () => {
      const hits = [{qid: 'Q1', name: 'Place1'}];
      setHits(hits);
      expect(state.hits).toEqual(hits);
    });

    it('sets current hit', () => {
      const hit = {qid: 'Q1', name: 'Place'};
      setCurrentHit(hit);
      expect(state.current_hit).toEqual(hit);
    });
  });

  describe('toggleItemType / clearItemTypeFilters', () => {
    it('replaces item_type filter when not present (single select)', () => {
      toggleItemType('Q1');
      expect(state.item_type_ticked).toEqual(['Q1']);
    });

    it('clears item_type filter when same one is clicked', () => {
      state.item_type_ticked = ['Q1'];
      toggleItemType('Q1');
      expect(state.item_type_ticked).toEqual([]);
    });

    it('replaces item_type filter when different one is clicked', () => {
      state.item_type_ticked = ['Q1'];
      toggleItemType('Q2');
      expect(state.item_type_ticked).toEqual(['Q2']);
    });

    it('clears all item_type filters', () => {
      state.item_type_ticked = ['Q1', 'Q2'];
      clearItemTypeFilters();
      expect(state.item_type_ticked).toEqual([]);
    });
  });

  describe('visibleItems', () => {
    it('filters items with markers', () => {
      setItems({
        Q1: {qid: 'Q1', markers: [{lat: 1, lon: 1}]},
        Q2: {qid: 'Q2', markers: []},
      });
      expect(visibleItems.value.length).toBe(1);
      expect(visibleItems.value[0].qid).toBe('Q1');
    });

    it('shows all items with markers', () => {
      setItems({
        Q1: {qid: 'Q1', markers: [{lat: 1, lon: 1}]},
        Q2: {qid: 'Q2', markers: [{lat: 2, lon: 2}]},
      });
      expect(visibleItems.value.length).toBe(2);
    });
  });
});
