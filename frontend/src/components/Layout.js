import React, { useState, useEffect } from 'react';
import { Layout, Menu, Avatar, Dropdown, Button, Badge, Space } from 'antd';
import { UserOutlined, LogoutOutlined, SettingOutlined, DashboardOutlined, TargetOutlined, ScanOutlined, TeamOutlined, BellOutlined, ToolOutlined } from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { authAPI } from '../services/api';

const { Header, Sider, Content } = Layout;

const MainLayout = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    // 获取当前用户信息
    const fetchUser = async () => {
      try {
        const response = await authAPI.getCurrentUser();
        setUser(response.data);
      } catch (error) {
        console.error('Failed to fetch user:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchUser();
  }, []);

  const handleLogout = async () => {
    try {
      await authAPI.logout();
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      navigate('/login');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const userMenu = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人资料',
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '设置',
      onClick: () => navigate('/settings'),
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ];

  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: '仪表板',
    },
    {
      key: '/targets',
      icon: <TargetOutlined />,
      label: '目标管理',
    },
    {
      key: '/scans',
      icon: <ScanOutlined />,
      label: '扫描管理',
    },
    {
      key: '/users',
      icon: <TeamOutlined />,
      label: '用户管理',
    },
    {
      key: '/settings',
      icon: <ToolOutlined />,
      label: '系统设置',
    },
  ];

  const handleMenuClick = ({ key }) => {
    navigate(key);
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <div>Loading...</div>
      </div>
    );
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        style={{
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
        }}
      >
        <div style={{ 
          height: '64px', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          background: '#001529',
          color: 'white',
          fontSize: '18px',
          fontWeight: 'bold'
        }}>
          {collapsed ? 'AI' : 'AI渗透测试'}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
        />
      </Sider>
      <Layout style={{ marginLeft: collapsed ? 80 : 200 }}>
        <Header style={{ 
          padding: '0 24px', 
          background: '#fff', 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }}>
          <div>
            <h1 style={{ margin: 0, fontSize: '20px', fontWeight: 'bold' }}>
              AI自动化渗透测试平台
            </h1>
            <p style={{ margin: 0, color: '#666', fontSize: '14px' }}>
              智能安全评估，自动化渗透测试
            </p>
          </div>
          <Space>
            <Badge count={3} size="small">
              <BellOutlined style={{ fontSize: '20px', cursor: 'pointer' }} />
            </Badge>
            <Dropdown menu={userMenu} placement="bottomRight">
              <Space style={{ cursor: 'pointer' }}>
                <Avatar src={user?.avatar_url} icon={<UserOutlined />} />
                <span>{user?.full_name || user?.username}</span>
              </Space>
            </Dropdown>
          </Space>
        </Header>
        <Content style={{ 
          margin: '24px', 
          padding: '24px', 
          background: '#fff', 
          borderRadius: '8px',
          minHeight: '280px',
        }}>
          {children}
        </Content>
      </Layout>
    </Layout>
  );
};

export default MainLayout;