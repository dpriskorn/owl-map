import {describe, it, expect} from 'vitest';
import {useEdits} from '../../src/composables/useEdits.js';

describe('useEdits', () => {
  const {findEditIndex, toggleEdit, buildEditList, handleUploadEvent} = useEdits();

  describe('findEditIndex', () => {
    it('returns -1 when edits is empty', () => {
      const item = {qid: 'Q1'};
      const osm = {identifier: 'node/1'};
      const edits = [];
      expect(findEditIndex(edits, item, osm)).toBe(-1);
    });

    it('returns index when edit exists', () => {
      const item = {qid: 'Q1'};
      const osm = {identifier: 'node/1'};
      const edits = [{item, osm}];
      expect(findEditIndex(edits, item, osm)).toBe(0);
    });

    it('returns -1 when edit does not exist', () => {
      const item1 = {qid: 'Q1'};
      const item2 = {qid: 'Q2'};
      const osm1 = {identifier: 'node/1'};
      const osm2 = {identifier: 'node/2'};
      const edits = [{item: item1, osm: osm1}];
      expect(findEditIndex(edits, item2, osm2)).toBe(-1);
    });

    it('matches by qid and identifier', () => {
      const item = {qid: 'Q1'};
      const osm = {identifier: 'node/1'};
      const edits = [{item, osm}];
      expect(findEditIndex(edits, {qid: 'Q1'}, {identifier: 'node/1'})).toBe(0);
      expect(findEditIndex(edits, {qid: 'Q2'}, {identifier: 'node/1'})).toBe(-1);
    });
  });

  describe('toggleEdit', () => {
    it('adds new edit when not exists', () => {
      const edits = [];
      const item = {qid: 'Q1'};
      const osm = {identifier: 'node/1'};
      toggleEdit(edits, item, osm);
      expect(edits.length).toBe(1);
      expect(edits[0].item).toBe(item);
      expect(edits[0].osm).toBe(osm);
    });

    it('removes existing edit when already in list (toggle)', () => {
      const edits = [];
      const item = {qid: 'Q1'};
      const osm = {identifier: 'node/1'};
      toggleEdit(edits, item, osm);
      toggleEdit(edits, item, osm);
      expect(edits.length).toBe(0);
    });
  });

  describe('buildEditList', () => {
    it('builds edit list with add op for selected osm', () => {
      const edits = [{
        item: {qid: 'Q1'},
        osm: {identifier: 'node/1', selected: true, tags: {}},
      }];
      const result = buildEditList(edits);
      expect(result[0]).toEqual({qid: 'Q1', osm: 'node/1', op: 'add'});
    });

    it('builds edit list with change op when wikidata tag differs', () => {
      const edits = [{
        item: {qid: 'Q1'},
        osm: {identifier: 'node/1', selected: true, tags: {wikidata: 'Q2'}},
      }];
      const result = buildEditList(edits);
      expect(result[0].op).toBe('change');
    });

    it('builds edit list with remove op for unselected osm', () => {
      const edits = [{
        item: {qid: 'Q1'},
        osm: {identifier: 'node/1', selected: false, tags: {}},
      }];
      const result = buildEditList(edits);
      expect(result[0].op).toBe('remove');
    });

    it('handles multiple edits', () => {
      const edits = [
        {item: {qid: 'Q1'}, osm: {identifier: 'node/1', selected: true, tags: {}}},
        {item: {qid: 'Q2'}, osm: {identifier: 'way/1', selected: false, tags: {}}},
      ];
      const result = buildEditList(edits);
      expect(result.length).toBe(2);
      expect(result[0].op).toBe('add');
      expect(result[1].op).toBe('remove');
    });
  });

  describe('handleUploadEvent', () => {
    it('handles auth-fail event', () => {
      const app = {};
      handleUploadEvent(app, {type: 'auth-fail'});
      expect(app.upload_state).toBe('auth-fail');
    });

    it('handles changeset-error event', () => {
      const app = {};
      handleUploadEvent(app, {type: 'changeset-error', error: 'Too many changes'});
      expect(app.upload_state).toBe('changeset-error');
      expect(app.upload_error).toBe('Too many changes');
    });

    it('handles open event', () => {
      const app = {};
      handleUploadEvent(app, {type: 'open', id: 123});
      expect(app.upload_state).toBe('uploading');
      expect(app.changeset_id).toBe(123);
    });

    it('handles progress event', () => {
      const app = {edits: [{}, {}, {}], beforeUnloadListener: () => {}};
      handleUploadEvent(app, {type: 'progress', num: 1});
      expect(app.upload_progress).toBeCloseTo(66.67, 1);
    });

    it('handles saved event', () => {
      const app = {edits: [{osm: {}}, {osm: {}}]};
      handleUploadEvent(app, {type: 'saved', num: 0});
      expect(app.edits[0].osm.upload_state).toBe('saved');
    });

    it('handles closing event', () => {
      const app = {};
      handleUploadEvent(app, {type: 'closing'});
      expect(app.upload_state).toBe('closing');
    });

    it('handles done event', () => {
      const app = {beforeUnloadListener: () => {}};
      handleUploadEvent(app, {type: 'done'});
      expect(app.upload_state).toBe('done');
    });
  });
});
