export function matchWikidataToOsm(wikidataItems, osmObjects) {
  const matched = [];
  const wikidataOnly = [];
  const osmOnly = [];

  const wikidataQids = new Set(Object.keys(wikidataItems));

  for (const [osmId, osmObj] of Object.entries(osmObjects)) {
    const wikidataQid = osmObj.wikidata_qid;
    if (wikidataQid && wikidataQids.has(wikidataQid)) {
      matched.push({
        osm_id: osmId,
        osm: osmObj,
        wikidata_qid: wikidataQid,
        wikidata: wikidataItems[wikidataQid],
      });
    } else {
      osmOnly.push({
        osm_id: osmId,
        osm: osmObj,
        wikidata_qid: wikidataQid,
      });
    }
  }

  const matchedWikidataQids = new Set(matched.map(m => m.wikidata_qid));
  for (const [qid, item] of Object.entries(wikidataItems)) {
    if (!matchedWikidataQids.has(qid)) {
      wikidataOnly.push({
        wikidata_qid: qid,
        wikidata: item,
      });
    }
  }

  return {
    matched,
    wikidata_only: wikidataOnly,
    osm_only: osmOnly,
  };
}

export function enrichItemsWithMatchStatus(items, matchResult) {
  const enriched = {};

  for (const [qid, item] of Object.entries(items)) {
    enriched[qid] = {
      ...item,
      match_status: 'wikidata_only',
      osm_id: null,
    };
  }

  for (const match of matchResult.matched) {
    if (enriched[match.wikidata_qid]) {
      enriched[match.wikidata_qid].match_status = 'matched';
      enriched[match.wikidata_qid].osm_id = match.osm_id;
    }
  }

  return enriched;
}
