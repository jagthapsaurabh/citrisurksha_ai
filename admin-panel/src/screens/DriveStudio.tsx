import React, { useCallback, useEffect, useState } from 'react';
import { api } from '../api';

export function DriveStudio() {
  const [status, setStatus] = useState<any>({ classes: [], sources: {} });
  const [per, setPer] = useState(4);
  const [source, setSource] = useState('all');
  const [dsVersion, setDsVersion] = useState('');
  const [epochs, setEpochs] = useState(8);
  const [busy, setBusy] = useState('');
  const [err, setErr] = useState('');
  const [log, setLog] = useState('');

  const load = useCallback(() => api.driveStatus().then(setStatus).catch((e: any) => setErr(e.message)), []);
  useEffect(() => { load(); }, [load]);

  async function act(name: string, fn: () => Promise<any>, note: string) {
    setBusy(name); setErr(''); setLog(note + '…');
    try {
      const r = await fn();
      setLog(note + ' — done.\n' + JSON.stringify(r, null, 2).slice(0, 3000));
      load();
    } catch (e: any) { setErr(e.message); setLog(note + ' — failed.'); }
    finally { setBusy(''); }
  }

  return <section>
    <div className="dashHero"><div><h2>Data Drive Studio</h2>
      <p>Collect open-licensed transfer images, ingest with provenance, build datasets and run experimental training — production models still require expert verification.</p></div>
      <span>🚚</span></div>
    {err && <p className="error">{err}</p>}

    <div className="trainGrid">
      <div>
        <div className="panel">
          <h3>Drive status</h3>
          <p className="muted">Provenance records: <b>{status.provenance_records ?? 0}</b></p>
          <div className="coverageGrid">
            {(status.classes || []).map((c: any) => <span key={c.pest_id} className={c.images ? 'ok' : 'miss'}>{c.images ? '✓' : '!'} {c.pest_id} ({c.images})</span>)}
          </div>
          <p className="muted">Sources: {Object.entries(status.sources || {}).map(([k, v]) => `${k} ×${v}`).join(' · ') || 'none yet'}</p>
        </div>

        <div className="panel">
          <h3>1 · Fetch open-licensed images</h3>
          <p className="muted">MIT (IP102-format) + Apache-2.0 (leafminer) transfer classes. Small batches keep the call fast.</p>
          <div className="two">
            <input type="number" min={1} max={12} value={per} onChange={e => setPer(Number(e.target.value))} />
            <select value={source} onChange={e => setSource(e.target.value)}>
              <option value="all">all sources</option><option value="leafminer">leafminer (Apache-2.0)</option><option value="ip102">IP102 (MIT)</option>
            </select>
          </div>
          <button disabled={!!busy} onClick={() => act('fetch', () => api.driveFetch({ per_class: per, source }), 'Fetching open images')}>
            {busy === 'fetch' ? 'Fetching…' : '🌐 Fetch + ingest'}
          </button>
        </div>

        <div className="panel">
          <h3>2 · Build dataset version</h3>
          <div className="two">
            <input placeholder="e.g. dataset-drive-v3" value={dsVersion} onChange={e => setDsVersion(e.target.value)} />
            <button disabled={!!busy || !dsVersion} onClick={() => act('ds', () => api.createDataset(dsVersion), 'Building dataset')}>📦 Build (frozen test set)</button>
          </div>
        </div>

        <div className="panel">
          <h3>3 · Experimental training (transfer classes)</h3>
          <p className="muted">Experimental flag relaxes the 20-class gate for development only; models register as <i>testing</i> and never auto-deploy.</p>
          <div className="two">
            <input type="number" min={1} max={30} value={epochs} onChange={e => setEpochs(Number(e.target.value))} />
            <button disabled={!!busy} onClick={() => act('cnn', () => api.driveTrainCnn({ epochs, dataset_version: dsVersion || undefined }), 'Training CNN')}>🧠 Train CNN</button>
          </div>
          <button disabled={!!busy} onClick={() => act('yolo', () => api.driveTrainYolo({ epochs: Math.min(epochs, 5) }), 'Training YOLO (bootstrap)')}>
            {busy === 'yolo' ? 'Training…' : '🎯 Train YOLO detector'}
          </button>
          <p className="muted">Then evaluate & deploy from <b>AI Models</b> per the release runbook.</p>
        </div>
      </div>

      <div className="panel">
        <h3>Run console</h3>
        <pre className="consoleLog">{log || 'Actions and results appear here.'}</pre>
      </div>
    </div>
  </section>;
}
