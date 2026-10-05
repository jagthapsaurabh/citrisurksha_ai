import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';

const statRoutes: Record<string, string> = {
  users: '/users',
  pests: '/pest-management',
  detections: '/farmer-uploads',
  unreviewed_detections: '/farmer-uploads',
  training_images_total: '/train-ai',
  training_images_verified: '/train-ai',
  training_jobs: '/train-ai',
  user_feedback: '/farmer-uploads',
  ai_knowledge_items: '/train-ai',
  farmers_with_fcm_token: '/farmers',
};

const statIcons: Record<string, string> = {
  users: '🧑‍💼', pests: '🌿', detections: '🖼️', unreviewed_detections: '🆕', training_images_total: '🧠', training_images_verified: '✅', training_jobs: '⚙️', user_feedback: '💬', ai_knowledge_items: '📚', farmers_with_fcm_token: '📲'
};

export function Dashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState<any>({});
  const [msg, setMsg] = useState('');
  useEffect(() => { api.dashboard().then(setStats).catch((e: any) => setMsg(e.message)); }, []);
  return <section><div className="dashHero"><div><h2>Dashboard Overview</h2><p>Monitor farmers, scans, AI training, notifications and pest data.</p></div></div>{msg && <p className="error">{msg}</p>}<div className="grid">{Object.entries(stats).map(([k, v]) => <button type="button" className="stat statClickable" key={k} onClick={() => navigate(statRoutes[k] || '/') }><i>{statIcons[k] || '📌'}</i><span>{String(v)}</span><label>{k.replaceAll('_', ' ')}</label></button>)}</div></section>;
}
