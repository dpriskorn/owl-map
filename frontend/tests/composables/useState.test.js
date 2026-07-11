import {describe, it, expect, beforeEach} from 'vitest';
import {useState} from '../../src/composables/useState.js';

describe('useState', () => {
  let state, visibleItems, itemsList, itemCount, uploadsGroupedByQid;
  let setItems, openItem, closeItem, setWikidataDetail, setLoading, setError;
  let clearError, setUploadState, resetUpload, setHits, setCurrentHit;
  let toggleIsa, clearIsaFilters, addEdit, clearEdits;

  beforeEach(() => {
    const result = useState();
    state = result.state;
    visibleItems = result.visibleItems;
    itemsList = result.itemsList;
    itemCount = result.itemCount;
    uploadsGroupedByQid = result.uploadsGroupedByQid;
    setItems = result.setItems;
    openItem = result.openItem;
    closeItem = result.closeItem;
    setWikidataDetail = result.setWikidataDetail;
    setLoading = result.setLoading;
    setError = result.setError;
    clearError = result.clearError;
    setUploadState = result.setUploadState;
    resetUpload = result.resetUpload;
    setHits = result.setHits;
    setCurrentHit = result.setCurrentHit;
    toggleIsa = result.toggleIsa;
    clearIsaFilters = result.clearIsaFilters;
    addEdit = result.addEdit;
    clearEdits = result.clearEdits;
  });

  describe('state initial values', () => {
    it('has correct initial state', () => {
      expect(state.loading).toBe(false);
      expect(state.items).toEqual({});
      expect(state.current_item).toBe(null);
      expect(state.edits).toEqual([]);
      expect(state.upload_state).toBe(undefined);
      expect(state.hits).toEqual([]);
      expect(state.isa_ticked).toEqual([]);
    });
  });

  describe('setItems', () => {
    it('sets items and updates item_count', () => {
      const items = {Q1: {qid: 'Q1', label: 'Test'}, Q2: {qid: 'Q2', label: 'Test2'}};
      setItems(items);
      expect(state.items).toEqual(items);
      expect(state.item_count).toBe(2);
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
    it('sets error message and traceback', () => {
      setError('Something went wrong', 'traceback here');
      expect(state.api_call_error_message).toBe('Something went wrong');
      expect(state.api_call_error_traceback).toBe('traceback here');
    });

    it('clears error', () => {
      setError('Error');
      clearError();
      expect(state.api_call_error_message).toBe(null);
      expect(state.api_call_error_traceback).toBe(null);
    });
  });

  describe('setUploadState / resetUpload', () => {
    it('sets upload state', () => {
      setUploadState('uploading', {upload_progress: 50});
      expect(state.upload_state).toBe('uploading');
      expect(state.upload_progress).toBe(50);
    });

    it('resets upload state', () => {
      state.upload_state = 'uploading';
      state.upload_progress = 75;
      state.upload_error = 'some error';
      state.changeset_id = 123;
      resetUpload();
      expect(state.upload_state).toBe(undefined);
      expect(state.upload_progress).toBe(0);
      expect(state.upload_error).toBe(null);
      expect(state.changeset_id).toBe(null);
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

  describe('toggleIsa / clearIsaFilters', () => {
    it('adds isa filter when not present', () => {
      toggleIsa('Q1');
      expect(state.isa_ticked).toContain('Q1');
    });

    it('removes isa filter when already present', () => {
      state.isa_ticked = ['Q1', 'Q2'];
      toggleIsa('Q1');
      expect(state.isa_ticked).toEqual(['Q2']);
    });

    it('clears all isa filters', () => {
      state.isa_ticked = ['Q1', 'Q2'];
      clearIsaFilters();
      expect(state.isa_ticked).toEqual([]);
    });
  });

  describe('addEdit / clearEdits', () => {
    it('adds a new edit', () => {
      const item = {qid: 'Q1'};
      const osm = {identifier: 'node/1'};
      addEdit(item, osm);
      expect(state.edits.length).toBe(1);
      expect(state.edits[0].item).toStrictEqual(item);
      expect(state.edits[0].osm).toStrictEqual(osm);
    });

    it('removes existing edit (toggle)', () => {
      const item = {qid: 'Q1'};
      const osm = {identifier: 'node/1'};
      addEdit(item, osm);
      addEdit(item, osm);
      expect(state.edits.length).toBe(0);
    });

    it('clears all edits', () => {
      state.edits = [{item: {qid: 'Q1'}, osm: {identifier: 'node/1'}}];
      clearEdits();
      expect(state.edits).toEqual([]);
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

    it('shows all items with markers when no filters set', () => {
      setItems({
        Q1: {qid: 'Q1', markers: [{lat: 1, lon: 1}]},
        Q2: {qid: 'Q2', markers: [{lat: 2, lon: 2}]},
      });
      expect(visibleItems.value.length).toBe(2);
    });
  });

  describe('uploadsGroupedByQid', () => {
    it('groups edits by qid', () => {
      state.edits = [
        {item: {qid: 'Q1', wikidata: {label: 'Item1'}}, osm: {identifier: 'node/1'}},
        {item: {qid: 'Q1', wikidata: {label: 'Item1'}}, osm: {identifier: 'node/2'}},
        {item: {qid: 'Q2', wikidata: {label: 'Item2'}}, osm: {identifier: 'way/1'}},
      ];
      const grouped = uploadsGroupedByQid.value;
      expect(grouped.length).toBe(2);
      expect(grouped[0].qid).toBe('Q1');
      expect(grouped[0].osm.length).toBe(2);
      expect(grouped[1].qid).toBe('Q2');
      expect(grouped[1].osm.length).toBe(1);
    });
  });
});
