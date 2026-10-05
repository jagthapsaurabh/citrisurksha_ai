import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, setAdminToken } from '../api';

export function Login({ onLogin }: { onLogin: () => void }) {
  const [phone, setPhone] = useState('9999999999');
  const [password, setPassword] = useState('admin123');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState('');
  const navigate = useNavigate();
  async function submit(e: React.FormEvent) { e.preventDefault(); setErr(''); try { setLoading(true); if(!phone) throw new Error('Phone is required'); if(!password) throw new Error('Password is required'); const res = await api.login(phone, password); if (!['admin','agronomist','data_labeler','support'].includes(res.role)) throw new Error('Platform user account required'); setAdminToken(res.access_token); onLogin(); navigate('/'); } catch (e: any) { setErr(e.message || 'Login failed'); } finally { setLoading(false); } }
  return <main className="login"><form onSubmit={submit} className="loginCard premiumLogin"><img src="/logo.png" className="loginLogo"/><h1>CitriSuraksha AI</h1><p>Scan · Detect · Protect</p><input value={phone} onChange={e=>setPhone(e.target.value)} placeholder="Phone"/><div className="passwordRow loginPass"><span className="lockIcon">🔒</span><input value={password} onChange={e=>setPassword(e.target.value)} placeholder="Password" type={showPassword?'text':'password'}/><button type="button" className="eyeBtn" onClick={()=>setShowPassword(!showPassword)} title={showPassword?'Hide password':'Show password'}>{showPassword?'🔓':'🔒'}</button></div><button disabled={loading}>{loading?'Logging in...':'Login'}</button>{err && <b className="error">{err}</b>}</form></main>;
}
