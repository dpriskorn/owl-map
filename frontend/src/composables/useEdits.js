export function useEdits() {
  const findEditIndex = (edits, item, osm) => {
    return edits.findIndex(
      e => e.item.qid === item.qid && e.osm.identifier === osm.identifier
    );
  };

  const toggleEdit = (edits, item, osm) => {
    const idx = findEditIndex(edits, item, osm);
    if (idx !== -1) {
      edits.splice(idx, 1);
    } else {
      edits.push({item, osm});
    }
  };

  const buildEditList = (edits) => {
    return edits.map(edit => {
      const {item, osm} = edit;
      const qid = item.qid;
      const entry = {qid, osm: osm.identifier};

      if (osm.selected) {
        entry.op = osm.tags.wikidata !== undefined && osm.tags.wikidata !== qid
          ? 'change'
          : 'add';
      } else {
        entry.op = 'remove';
      }

      return entry;
    });
  };

  const handleUploadEvent = (app, data) => {
    const {type, event: eventType} = data;
    const eventName = type || eventType;

    switch (eventName) {
      case 'auth-fail':
        app.upload_state = 'auth-fail';
        break;
      case 'changeset-error':
        app.upload_state = 'changeset-error';
        app.upload_error = data.error;
        break;
      case 'open':
        app.upload_state = 'uploading';
        app.changeset_id = data.id;
        break;
      case 'progress': {
        const edit = app.edits[data.num];
        app.upload_progress = ((data.num + 1) * 100) / app.edits.length;
        if (edit?.osm) edit.osm.upload_state = 'progress';
        break;
      }
      case 'saved': {
        const savedEdit = app.edits[data.num];
        if (savedEdit?.osm) savedEdit.osm.upload_state = 'saved';
        break;
      }
      case 'closing':
        app.upload_state = 'closing';
        break;
      case 'done':
        app.upload_state = 'done';
        removeEventListener('beforeunload', app.beforeUnloadListener, {capture: true});
        break;
    }
  };

  return {
    findEditIndex,
    toggleEdit,
    buildEditList,
    handleUploadEvent,
  };
}
