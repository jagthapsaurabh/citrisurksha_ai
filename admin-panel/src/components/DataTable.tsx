import React from 'react';
import { Link } from 'react-router-dom';
import { usePager } from './usePager';
import { ListTools } from './ListTools';
import { formatIndianDate, isDateKey, isIdKey } from '../utils/format';

type Column = { key: string; label: string; render?: (r: any) => any };
type Props = { title: string; items: any[]; columns: Column[]; addPath?: string; onView?: (r: any) => void; onToggle?: (r: any) => void; onDelete?: (r: any) => void; editPath?: (r: any) => string; search?: string; };

export function DataTable({ title, items, columns, addPath, onView, onToggle, onDelete, editPath, search = 'Search' }: Props) {
  const pager = usePager(items, 10);
  return <section>{title && <div className="tableHeader"><h2>{title}</h2>{addPath && <Link className="addBtn" to={addPath}>＋ Add</Link>}</div>}<ListTools pager={pager} placeholder={search}/><div className="dataTable"><table><thead><tr>{columns.map(c => <th key={c.key}>{c.label}</th>)}<th>Actions</th></tr></thead><tbody>{pager.data.map((r: any) => <tr key={r.id}>{columns.map(c => <td key={c.key}>{c.render ? c.render(r) : isDateKey(c.key) ? formatIndianDate(r[c.key]) : String(r[c.key] ?? '-')}</td>)}<td className="actionCell"><button className="iconBtn" title="View" onClick={() => onView?.(r)}>👁️</button>{editPath && <Link className="iconLink" title="Edit" to={editPath(r)}>✏️</Link>}{onToggle && <button className="iconBtn" title={r.is_active === false || r.published === false ? 'Enable' : 'Disable'} onClick={() => onToggle(r)}>{r.is_active === false || r.published === false ? '✅' : '🚫'}</button>}{onDelete && <button className="iconBtn dangerIcon" title="Delete" onClick={() => onDelete(r)}>🗑️</button>}</td></tr>)}</tbody></table>{pager.data.length === 0 && <p className="panel">Data not available</p>}</div></section>;
}

function prettyKey(k: string) { return k.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()); }
function renderValue(k:string, v: any): any {
  if (isIdKey(k)) return <span className="muted">Hidden</span>;
  if (v === null || v === undefined || v === '') return <span className="muted">Not available</span>;
  if (isDateKey(k)) return formatIndianDate(v);
  if (typeof v === 'boolean') return v ? 'Yes' : 'No';
  if (Array.isArray(v)) return <ul className="detailList">{v.map((x, i) => <li key={i}>{typeof x === 'object' ? renderValue('', x) : String(x)}</li>)}</ul>;
  if (typeof v === 'object') return <div className="detailNested">{Object.entries(v).filter(([key])=>!isIdKey(key)).map(([key, val]) => <div className="detailRow" key={key}><b>{prettyKey(key)}</b><div>{renderValue(key, val)}</div></div>)}</div>;
  return String(v);
}
export function DetailModal({ row, onClose }: { row: any; onClose: () => void }) { if (!row) return null; return <div className="modalBackdrop" onClick={onClose}><div className="modal" onClick={e => e.stopPropagation()}><button className="modalClose" onClick={onClose}>×</button><h2>Details</h2><div className="detailGrid">{Object.entries(row).filter(([k])=>!isIdKey(k)).map(([k, v]) => <div className="detailItem" key={k}><label>{prettyKey(k)}</label><div>{renderValue(k, v)}</div></div>)}</div></div></div>; }
