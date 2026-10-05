import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Login } from './screens/Login';
import { Dashboard } from './screens/Dashboard';
import { UserManagement, UserForm } from './screens/UserManagement';
import { Farmers } from './screens/Farmers';
import { PestList, PestEditor } from './screens/PestForm';
import { RegisterInsecticideList, InsecticideForm } from './screens/RegisterInsecticide';
import { FarmerUploads } from './screens/FarmerUploads';
import { BlogList, BlogForm } from './screens/Blogs';
import { TrainAI } from './screens/TrainAI';
import { AIModels } from './screens/AIModels';
import { DriveStudio } from './screens/DriveStudio';
import { EventsList, EventForm } from './screens/Events';
import { CalendarOperationList, CalendarOperationForm } from './screens/CalendarOperation';
import { FarmerChat } from './screens/FarmerChat';
import { AdminNotifications } from './screens/AdminNotifications';
import { PushNotifications } from './screens/PushNotifications';
import { Settings } from './screens/Settings';
import { ErrorBoundary } from './components/ErrorBoundary';
import './styles.css';

function Protected({ logged, children }: { logged: boolean; children: React.ReactNode }) {
  return logged ? <>{children}</> : <Navigate to="/login" replace />;
}

function App() {
  const [logged, setLogged] = useState(Boolean(localStorage.getItem('admin_token')));
  return <ErrorBoundary><BrowserRouter>
    <Routes>
      <Route path="/login" element={<Login onLogin={() => setLogged(true)} />} />
      <Route element={<Protected logged={logged}><Layout onLogout={() => setLogged(false)} /></Protected>}>
        <Route index element={<Dashboard />} />
        <Route path="users" element={<UserManagement />} />
        <Route path="users/add" element={<UserForm />} />
        <Route path="users/:id/edit" element={<UserForm />} />
        <Route path="farmers" element={<Farmers />} />
        <Route path="register-insecticide" element={<RegisterInsecticideList />} />
        <Route path="register-insecticide/add" element={<InsecticideForm />} />
        <Route path="register-insecticide/:id/edit" element={<InsecticideForm />} />
        <Route path="pest-management" element={<PestList />} />
        <Route path="pest-management/add" element={<PestEditor />} />
        <Route path="pest-management/:id/edit" element={<PestEditor />} />
        <Route path="farmer-uploads" element={<FarmerUploads />} />
        <Route path="blogs" element={<BlogList />} />
        <Route path="blogs/add" element={<BlogForm />} />
        <Route path="blogs/:id/edit" element={<BlogForm />} />
        <Route path="train-ai" element={<TrainAI />} />
        <Route path="drive-studio" element={<DriveStudio />} />
        <Route path="ai-models" element={<AIModels />} />
        <Route path="events" element={<EventsList />} />
        <Route path="events/add" element={<EventForm />} />
        <Route path="events/:id/edit" element={<EventForm />} />
        <Route path="calendar-operation" element={<CalendarOperationList />} />
        <Route path="calendar-operation/add" element={<CalendarOperationForm />} />
        <Route path="calendar-operation/:id/edit" element={<CalendarOperationForm />} />
        <Route path="chat" element={<FarmerChat />} />
        <Route path="admin-notifications" element={<AdminNotifications />} />
        <Route path="push-notifications" element={<PushNotifications />} />
        <Route path="settings" element={<Settings onLogout={() => setLogged(false)} />} />
      </Route>
    </Routes>
  </BrowserRouter></ErrorBoundary>;
}

createRoot(document.getElementById('root')!).render(<App />);
