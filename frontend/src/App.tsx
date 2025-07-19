import React, { useState } from 'react';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { useAuth } from './hooks/useAuth';
import LoginForm from './components/LoginForm';
import Dashboard from './pages/Dashboard';
import 'antd/dist/reset.css';

const App: React.FC = () => {
  const { isAuthenticated, loading } = useAuth();
  const [loginSuccess, setLoginSuccess] = useState(false);

  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh' 
      }}>
        加载中...
      </div>
    );
  }

  return (
    <ConfigProvider locale={zhCN}>
      {isAuthenticated || loginSuccess ? (
        <Dashboard />
      ) : (
        <LoginForm onLoginSuccess={() => setLoginSuccess(true)} />
      )}
    </ConfigProvider>
  );
};

export default App;