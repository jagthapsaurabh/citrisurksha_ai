import React,{useEffect,useMemo,useState}from'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { api, clearAdminToken } from '../api';

const allNav = [
  ['/', '📊', 'Dashboard', ['admin','agronomist','data_labeler','support']],
  ['/users', '🧑‍💼', 'User Management', ['admin']],
  ['/farmers', '👨‍🌾', 'Farmers', ['admin','agronomist','support']],
  ['/register-insecticide', '🐛', 'Register Insecticide', ['admin','agronomist']],
  ['/pest-management', '🌿', 'Pest Management', ['admin','agronomist']],
  ['/farmer-uploads', '🖼️', 'Farmer Uploads', ['admin','agronomist','data_labeler']],
  ['/blogs', '📰', 'Blog', ['admin','support']],
  ['/train-ai', '🧠', 'Train AI', ['admin','data_labeler','agronomist']],
  ['/drive-studio', '🚚', 'Data Drive', ['admin','data_labeler','agronomist']],
  ['/ai-models', '🤖', 'AI Models', ['admin','data_labeler','agronomist']],
  ['/events', '📅', 'Events', ['admin','support']],
  ['/calendar-operation', '🗓️', 'Calendar of Operation', ['admin','agronomist','support']],
  ['/admin-notifications', '🔔', 'Notification', ['admin','agronomist','data_labeler','support']],
  ['/push-notifications', '📣', 'Push Notification', ['admin','support']],
  ['/chat', '💬', 'Farmer Chat', ['admin','support','agronomist']],
  ['/settings', '⚙️', 'Settings', ['admin','agronomist','data_labeler','support']],
] as const;

export function Layout({ onLogout }: { onLogout: () => void }) {
  const navigate = useNavigate();
  const [me,setMe]=useState<any>(null); const [notif,setNotif]=useState(0); const [chat,setChat]=useState(0);
  useEffect(()=>{api.me().then(setMe).catch(()=>undefined); const load=()=>{api.adminNotificationCount().then(r=>setNotif(r.count||0)).catch(()=>setNotif(0)); api.adminNotifications().then((rows:any[])=>setChat(rows.filter(n=>!n.is_read&&n.data?.type==='chat').length)).catch(()=>setChat(0));}; load(); const t=setInterval(load,30000); return()=>clearInterval(t)},[]);
  const role=me?.role||'admin';
  const nav=useMemo(()=>allNav.filter(n=>(n[3] as readonly string[]).includes(role)),[role]);
  function logout() { clearAdminToken(); onLogout(); navigate('/login'); }
  return <div><header><div className="brand"><img src="/logo.png" className="brandLogo"/><div><h1>CitriSuraksha AI</h1><small>{me?.name||'Admin'} · {role}</small></div></div><button className="logoutBtn" onClick={logout}>Logout</button></header><aside>{nav.map(([to, icon, label]) => <NavLink to={to} key={to} end={to === '/'}>{icon} <span>{label}</span>{to==='/admin-notifications'&&notif>0?<b className="navBadge">{notif}</b>:null}{to==='/chat'&&chat>0?<b className="navBadge">{chat}</b>:null}</NavLink>)}</aside><main className="content"><Outlet /></main></div>;
}
