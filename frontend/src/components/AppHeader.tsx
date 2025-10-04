import React, { useState } from 'react';
import { Layout, Space, Button, Typography, Dropdown } from 'antd';
import {
  LogoutOutlined,
  SettingOutlined,
  UserOutlined,
  DownOutlined
} from '@ant-design/icons';
import type { MenuProps } from 'antd';
import { useAuth } from '../contexts/AuthContext';
import UserSettingsModal from './UserSettingsModal';

const { Header } = Layout;
const { Text } = Typography;

const AppHeader: React.FC = () => {
  const { user, logout } = useAuth();
  const [userSettingsVisible, setUserSettingsVisible] = useState(false);

  const handleUserUpdate = (updatedUser: any) => {
    const currentUserData = JSON.parse(localStorage.getItem('user') || '{}');
    const newUserData = { ...currentUserData, ...updatedUser };
    localStorage.setItem('user', JSON.stringify(newUserData));
    window.location.reload();
  };

  const userMenuItems: MenuProps['items'] = [
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '用户设置',
      onClick: () => setUserSettingsVisible(true)
    },
    {
      type: 'divider'
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: logout,
      danger: true
    }
  ];

  return (
    <>
      <Header style={{
        padding: '0 24px',
        background: '#fff',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
        position: 'sticky',
        top: 0,
        zIndex: 1
      }}>
        <Text style={{ fontSize: 16, color: '#595959' }}>
          欢迎回来，{user?.username}！
        </Text>
        <Space>
          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
            <Button type="text" icon={<UserOutlined />}>
              <Space>
                {user?.username}
                <DownOutlined style={{ fontSize: 12 }} />
              </Space>
            </Button>
          </Dropdown>
        </Space>
      </Header>

      <UserSettingsModal
        visible={userSettingsVisible}
        onCancel={() => setUserSettingsVisible(false)}
        user={user}
        onUserUpdate={handleUserUpdate}
      />
    </>
  );
};

export default AppHeader;
