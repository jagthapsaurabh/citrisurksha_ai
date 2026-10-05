import React, { useCallback, useEffect, useState } from 'react';
import { api } from '../api';
import { DetailModal } from '../components/DataTable';

const STATUS_COLORS: Record<string, string> = {
  production: '#116530', approved: '#2ea043', testing: '#c77800',
  training: '#0077b6', rejected: '#b00020', archived: '#667',
};

export function AIModels() {
  const [data, setData] = useState<any>({ models: [] });
  const [datasets, setDatasets] = useState<any[]>([]);
  const [err, setErr] = useState('');
  const [msg, setMsg] = useState('');
  const [view, setView] = useState<any>(null);
  const [busy, setBusy] = useState('');
  const [newDs, setNewDs] = useState('');
  const [yoloDs, setYoloDs] = useState('');
  const [clusters, setClusters] = useState<any>({ clusters: [] });

  const load = useCallback(() => {
    api.aiModels().then(setData).catch((e: any) => setErr(e.message));
    api.aiDatasets().then((r: any) => setDatasets(r.datasets || [])).catch(() => undefined);
    api.unknownClusters().then(setClusters).catch(() => undefined);
  }, []);
  useEffect(() => { load(); }, [load]);

  async function act(name: string, fn: () => Promise<any>) {
    setBusy(name); setErr(''); setMsg('');
    try { const r = await fn(); setMsg(typeof r === 'string' ? r : JSON.stringify(r).slice(0, 220)); load(); }
    catch (e: any) { setErr(e.message); }
    finally { setBusy(''); }
  }

  const models = data.models || [];
  return <section>
    <div className="dashHero"><div><h2>AI Model Governance</h2>
      <p>Evaluate on the frozen test set, compare with production, deploy or roll back. Nothing deploys without evidence.</p></div>
      <span>🤖</span></div>
    {err && <p className="error">{err}</p>}
    {msg && <p className="panel" style={{ color: '#116530', fontWeight: 800 }}>{msg}</p>}

    <div className="panel"><h3>Active (production) Model</h3>
      <p><b>Version:</b> {data.active?.version || 'Not trained'} · <b>Architecture:</b> {data.active?.architecture || '-'}</p>
      <button onClick={() => act('rollback', async () => { const r = await api.rollbackModel(); return `Rolled back to ${r.deployed}`; })} disabled={!!busy}>
        {busy === 'rollback' ? 'Working…' : ' Rollback to previous production'}
      </button>
    </div>

    <div className="trainGrid">
      <div className="panel">
        <h3>Model Versions</h3>
        <div className="dataTable"><table>
          <thead><tr><th>Version</th><th>Status</th><th>Dataset</th><th>Val acc / F1</th><th>Frozen eval</th><th>Comparison</th><th>Actions</th></tr></thead>
          <tbody>{models.map((m: any) => {
            const fe = m.metrics?.frozen_eval;
            const comp = m.metrics?.comparison;
            return <tr key={m.id}>
              <td><b>{m.version}</b>{m.is_active ? ' 🟢' : ''}<br /><small className="muted">{m.architecture}</small></td>
              <td><span style={{ background: STATUS_COLORS[m.status] || '#667', color: '#fff', borderRadius: 999, padding: '3px 10px', fontSize: 11, fontWeight: 900 }}>{m.status}</span></td>
              <td>{m.dataset_version || '-'}</td>
              <td>{m.metrics?.accuracy ?? '-'}{m.metrics?.macro_f1 != null ? ` / ${m.metrics.macro_f1}` : ''}</td>
              <td>{fe ? `✅ acc ${fe.accuracy ?? '-'}` : '—'}</td>
              <td>{comp ? <b style={{ color: comp.recommendation === 'deploy' ? '#116530' : comp.recommendation === 'reject' ? '#b00020' : '#c77800' }}>{comp.recommendation}</b> : '—'}</td>
              <td className="actionCell">
                <button className="iconBtn" title="Evaluate on frozen test set" disabled={!!busy} onClick={() => act(`ev-${m.id}`, () => api.evaluateModel(m.id))}>🧪</button>
                <button className="iconBtn" title="Compare vs production" disabled={!!busy} onClick={() => act(`cmp-${m.id}`, () => api.compareModel(m.id))}>⚖️</button>
                {m.status === 'testing' && <button className="iconBtn" title="Approve" disabled={!!busy} onClick={() => act(`ap-${m.id}`, () => api.setModelStatus(m.id, 'approved'))}>✅</button>}
                {(m.status === 'testing' || m.status === 'approved') && <button className="iconBtn dangerIcon" title="Reject" disabled={!!busy} onClick={() => act(`rj-${m.id}`, () => api.setModelStatus(m.id, 'rejected'))}>🚫</button>}
                {(m.status === 'approved' || m.status === 'archived') && <button className="iconBtn" title="Deploy to production" disabled={!!busy} onClick={() => act(`dep-${m.id}`, () => api.deployModel(m.id))}>🚀</button>}
                <button className="iconBtn" title="Details" onClick={() => setView(m)}>👁️</button>
              </td>
            </tr>;
          })}</tbody>
        </table></div>
      </div>

      <div>
        <div className="panel"><h3>Dataset Versions (frozen test set)</h3>
          {datasets.length === 0 && <p className="muted">No dataset versions yet. Create one from verified images.</p>}
          {datasets.map((d: any) => <p key={d.version}><b>{d.version}</b> — {d.image_count} imgs
            (train {d.train_count} / val {d.val_count} / test {d.test_count}) · dups removed {d.dups_removed}<br />
            <small className="muted">{d.created_at?.toString().slice(0, 19)}</small></p>)}
          <div className="two">
            <input placeholder="new version e.g. dataset-v1" value={newDs} onChange={e => setNewDs(e.target.value)} />
            <button disabled={!!busy || !newDs} onClick={() => act('ds', async () => { const r = await api.createDataset(newDs); setNewDs(''); return `Dataset ${r.dataset?.version} created (${r.dataset?.image_count} imgs)`; })}>
              {busy === 'ds' ? 'Building…' : '📦 Build dataset'}
            </button>
          </div>
        </div>
        <div className="panel"><h3>🕵️ Unknown pest candidates (visual clusters)</h3>
          <p className="muted">Unidentified scans are embedded and grouped; coherent clusters may be novel pests. {(clusters.total_unknowns ?? 0)} unknowns stored.</p>
          {(clusters.clusters || []).slice(0, 6).map((c: any, i: number) => <p key={i}>
            <b>Cluster {i + 1}</b> — {c.size} similar images {c.candidate_new_class ? <span style={{ background: '#d81b60', color: '#fff', borderRadius: 999, padding: '2px 8px', fontSize: 10, fontWeight: 900 }}>CANDIDATE NEW CLASS</span> : ''}<br />
            <small className="muted">AI guesses: {Object.entries(c.top_candidate_votes || {}).map(([k, v]) => `${k}×${v}`).join(', ') || 'none'}</small></p>)}
          {(clusters.clusters || []).length === 0 && <p className="muted">No clusters yet.</p>}
          <button disabled={!!busy} onClick={() => act('tune', async () => { const r = await api.tunePriority(); return `Priority proposal: ${JSON.stringify(r.proposed || r.note)}`; })}>
            {busy === 'tune' ? 'Tuning…' : '️ Tune review-priority weights from reviews'}
          </button>
        </div>
        <div className="panel"><h3>YOLO11 Detector (bootstrap boxes)</h3>
          <p className="muted">Trains the detector stage from verified images with full-image bootstrap boxes. Result lands in Model Versions as <i>testing</i>.</p>
          <div className="two">
            <input placeholder="dataset version" value={yoloDs} onChange={e => setYoloDs(e.target.value)} />
            <button disabled={!!busy} onClick={() => act('yolo', async () => { const r = await api.trainYolo({ dataset_version: yoloDs || 'yolo-bootstrap', epochs: 10 }); return r.status === 'completed' ? `YOLO ${r.version} trained` : `YOLO: ${r.status}`; })}>
              {busy === 'yolo' ? 'Training…' : '🎯 Train YOLO detector'}
            </button>
          </div>
        </div>
      </div>
    </div>
    <DetailModal row={view} onClose={() => setView(null)} />
  </section>;
}
