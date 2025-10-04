import React from 'react';
import { ConfigProvider, Spin } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import LoginForm from './components/LoginForm';
import MainLayout from './layouts/MainLayout';
import Dashboard from './pages/Dashboard';
import GitHubAccountManagement from './pages/GitHubAccountManagement';
import GitHubGroupsManagement from './pages/GitHubGroupsManagement';
import RepositoryStarManagement from './pages/RepositoryStarManagement';
import ScheduledTasksManagement from './pages/ScheduledTasksManagement';
import ApiWebsiteManagement from './pages/ApiWebsiteManagement';
import 'antd/dist/reset.css';
import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
} from 'react-router-dom';

const AppContent: React.FC = () => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh'
      }}>
        <Spin size="large" tip="加载中..." />
      </div>
    );
  }

  return (
    <ConfigProvider locale={zhCN}>
      <Routes>
        <Route
          path="/login"
          element={
            isAuthenticated ? <Navigate to="/dashboard" replace /> : <LoginForm />
          }
        />
        <Route
          path="/"
          element={
            isAuthenticated ? <MainLayout /> : <Navigate to="/login" replace />
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="github/accounts" element={<GitHubAccountManagement />} />
          <Route path="github/groups" element={<GitHubGroupsManagement />} />
          <Route path="github/repositories" element={<RepositoryStarManagement />} />
          <Route path="automation/tasks" element={<ScheduledTasksManagement />} />
          <Route path="automation/websites" element={<ApiWebsiteManagement />} />
        </Route>
        <Route
          path="*"
          element={
            <Navigate to={isAuthenticated ? '/dashboard' : '/login'} replace />
          }
        />
      </Routes>
    </ConfigProvider>
  );
};

const App: React.FC = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppContent />
      </BrowserRouter>
    </AuthProvider>
  );
};

export default App;
