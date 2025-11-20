import React, { useState, useEffect } from 'react';
import { Layout, Menu, Typography } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  DashboardOutlined,
  GithubOutlined,
  StarOutlined,
  ClockCircleOutlined,
  GlobalOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  FolderOutlined,
  UserOutlined,
  ScheduleOutlined
} from '@ant-design/icons';
import type { MenuProps } from 'antd';
import { systemAPI } from '../services/api';

const { Sider } = Layout;
const { Text } = Typography;

interface SidebarProps {
  collapsed: boolean;
  onCollapse: (collapsed: boolean) => void;
}

type MenuItem = Required<MenuProps>['items'][number];

const Sidebar: React.FC<SidebarProps> = ({ collapsed, onCollapse }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [version, setVersion] = useState<string>('');

  useEffect(() => {
    // 获取版本号
    const fetchVersion = async () => {
      try {
        const res = await systemAPI.getVersion();
        setVersion(res.data.version || 'unknown');
      } catch (error) {
        console.error('获取版本号失败', error);
        setVersion('unknown');
      }
    };
    fetchVersion();
  }, []);

  const menuItems: MenuItem[] = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: '仪表盘',
      onClick: () => navigate('/dashboard')
    },
    {
      key: 'github',
      icon: <GithubOutlined />,
      label: 'GitHub管理',
      children: [
        {
          key: '/github/accounts',
          icon: <UserOutlined />,
          label: '账号管理',
          onClick: () => navigate('/github/accounts')
        },
        {
          key: '/github/groups',
          icon: <FolderOutlined />,
          label: '分组管理',
          onClick: () => navigate('/github/groups')
        },
        {
          key: '/github/repositories',
          icon: <StarOutlined />,
          label: '仓库收藏',
          onClick: () => navigate('/github/repositories')
        }
      ]
    },
    {
      key: 'automation',
      icon: <ClockCircleOutlined />,
      label: '自动化工具',
      children: [
        {
          key: '/automation/tasks',
          icon: <ScheduleOutlined />,
          label: '定时任务',
          onClick: () => navigate('/automation/tasks')
        },
        {
          key: '/automation/websites',
          icon: <GlobalOutlined />,
          label: 'API网站',
          onClick: () => navigate('/automation/websites')
        }
      ]
    }
  ];

  // 根据当前路径确定选中的菜单项和打开的子菜单
  const getSelectedKeys = () => {
    return [location.pathname];
  };

  const getOpenKeys = () => {
    if (location.pathname.startsWith('/github')) {
      return ['github'];
    }
    if (location.pathname.startsWith('/automation')) {
      return ['automation'];
    }
    return [];
  };

  return (
    <Sider
      collapsible
      collapsed={collapsed}
      onCollapse={onCollapse}
      breakpoint="lg"
      collapsedWidth={80}
      width={220}
      style={{
        overflow: 'auto',
        height: '100vh',
        position: 'sticky',
        top: 0,
        left: 0,
      }}
      trigger={
        collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />
      }
    >
      <div style={{
        height: 64,
        margin: 16,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#fff',
        fontSize: collapsed ? 16 : 20,
        fontWeight: 'bold',
        background: 'rgba(255, 255, 255, 0.1)',
        borderRadius: 8
      }}>
        {collapsed ? '⚡' : 'GitHub管理'}
      </div>
      <Menu
        theme="dark"
        mode="inline"
        selectedKeys={getSelectedKeys()}
        defaultOpenKeys={getOpenKeys()}
        items={menuItems}
        style={{ borderRight: 0 }}
      />
      <div style={{
        position: 'absolute',
        bottom: 16,
        left: 0,
        right: 0,
        padding: '0 16px',
        textAlign: 'center',
        color: 'rgba(255, 255, 255, 0.65)'
      }}>
        {!collapsed && (
          <Text style={{ fontSize: 12, color: 'rgba(255, 255, 255, 0.45)' }}>
            版本 {version}
          </Text>
        )}
      </div>
    </Sider>
  );
};

export default Sidebar;
