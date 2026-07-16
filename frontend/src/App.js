import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import Layout from './components/Layout';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import TargetsPage from './pages/TargetsPage';
import TargetDetailPage from './pages/TargetDetailPage';
import ScansPage from './pages/ScansPage';
import ScanDetailPage from './pages/ScanDetailPage';
import UsersPage from './pages/UsersPage';
import SettingsPage from './pages/SettingsPage';
import NotFoundPage from './pages/NotFoundPage';
import './App.css';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    // 检查用户是否已登录
    const token = localStorage.getItem('accessToken');
    setIsAuthenticated(!!token);
  }, []);

  const ProtectedRoute = ({ children }) => {
    if (!isAuthenticated) {
      return <Navigate to="/login" replace />;
    }
    return children;
  };

  return (
    <ConfigProvider locale={zhCN}>
      <Router>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            } />
            <Route path="targets" element={
              <ProtectedRoute>
                <TargetsPage />
              </ProtectedRoute>
            } />
            <Route path="targets/:targetId" element={
              <ProtectedRoute>
                <TargetDetailPage />
              </ProtectedRoute>
            } />
            <Route path="scans" element={
              <ProtectedRoute>
                <ScansPage />
              </ProtectedRoute>
            } />
            <Route path="scans/:scanId" element={
              <ProtectedRoute>
                <ScanDetailPage />
              </ProtectedRoute>
            } />
            <Route path="users" element={
              <ProtectedRoute>
                <UsersPage />
              </ProtectedRoute>
            } />
            <Route path="settings" element={
              <ProtectedRoute>
                <SettingsPage />
              </ProtectedRoute>
            } />
          </Route>
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </Router>
    </ConfigProvider>
  );
}

export default App;