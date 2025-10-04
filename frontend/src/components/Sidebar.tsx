import React from 'react';
import { Layout, Menu } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  DashboardOutlined,
  GithubOutlined,
  StarOutlined,
  ClockCircleOutlined,
  GlobalOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined
} from '@ant-design/icons';
import type { MenuProps } from 'antd';

const { Sider } = Layout;

interface SidebarProps {
  collapsed: boolean;
  onCollapse: (collapsed: boolean) => void;
}

type MenuItem = Required<MenuProps>['items'][number];

const Sidebar: React.FC<SidebarProps> = ({ collapsed, onCollapse }) => {
  const navigate = useNavigate();
  const location = useLocation();

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
          label: '账号管理',
          onClick: () => navigate('/github/accounts')
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
    </Sider>
  );
};

export default Sidebar;
