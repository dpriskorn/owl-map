import {describe, it, expect, vi, beforeEach} from 'vitest';
import axios from 'redaxios';

vi.mock('redaxios');

import {useApi} from '../../src/composables/useApi.js';

describe('useApi', () => {
  let api;

  beforeEach(() => {
    vi.clearAllMocks();
    api = useApi();
  });

  describe('api_call', () => {
    it('returns response on success', async () => {
      const mockResponse = {data: {items: [{qid: 'Q1'}]}};
      axios.mockResolvedValue(mockResponse);

      const result = await api.api_call('items');
      expect(result).toEqual(mockResponse);
      expect(axios).toHaveBeenCalledWith(expect.objectContaining({
        url: expect.stringContaining('/api/1/items'),
      }));
    });

    it('throws error with message on failure', async () => {
      const errorResponse = {
        response: {
          data: {error: 'Not found', traceback: 'some trace'},
        },
      };
      axios.mockRejectedValue(errorResponse);

      await expect(api.api_call('item/Q999')).rejects.toMatchObject({
        api_call_error_message: 'Not found',
        api_call_error_traceback: 'some trace',
      });
    });

    it('uses error.message when no response data', async () => {
      const error = {message: 'Network error'};
      axios.mockRejectedValue(error);

      await expect(api.api_call('items')).rejects.toMatchObject({
        api_call_error_message: 'Network error',
      });
    });
  });

  describe('fetchItems', () => {
    it('calls items endpoint with bbox', async () => {
      axios.mockResolvedValue({data: {items: []}});
      await api.fetchItems([1, 2, 3, 4]);
      expect(axios).toHaveBeenCalledWith(expect.objectContaining({
        url: expect.stringContaining('/api/1/items'),
      }));
    });
  });

  describe('search', () => {
    it('calls search endpoint with query', async () => {
      axios.mockResolvedValue({data: []});
      await api.search('Cambridge');
      expect(axios).toHaveBeenCalledWith(expect.objectContaining({
        url: expect.stringContaining('/api/1/search'),
      }));
    });
  });

  describe('getCommonsUrl', () => {
    it('returns correct commons URL', () => {
      const url = api.getCommonsUrl('test.png');
      expect(url).toContain('/commons/test.png');
    });
  });
});
