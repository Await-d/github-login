import React, { useState } from 'react';
import { Form, Input, Button, Card, Typography, message, Tabs } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useAuth } from '../hooks/useAuth';

const { Title } = Typography;
const { TabPane } = Tabs;

const LoginForm: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const { login, register } = useAuth();

  const handleLogin = async (values: { username: string; password: string }) => {
    setLoading(true);
    try {
      const result = await login(values.username, values.password);
      if (result?.success) {
        message.success('登录成功');
        // useAuth会自动更新isAuthenticated状态，App组件会重新渲染
      } else {
        message.error(result?.message || '登录失败，请检查用户名和密码');
      }
    } catch (error: any) {
      message.error('网络错误，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (values: { username: string; password: string; confirmPassword: string }) => {
    if (values.password !== values.confirmPassword) {
      message.error('两次输入的密码不一致');
      return;
    }

    setLoading(true);
    try {
      const result = await register(values.username, values.password);
      if (result?.success) {
        message.success('注册成功，请登录');
      } else {
        message.error(result?.message || '注册失败');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', background: '#f0f2f5' }}>
      <Card style={{ width: 400, boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <Title level={2}>GitHub账号管理系统</Title>
        </div>
        
        <Tabs defaultActiveKey="login" centered>
          <TabPane tab="登录" key="login">
            <Form onFinish={handleLogin} layout="vertical">
              <Form.Item
                name="username"
                rules={[{ required: true, message: '请输入用户名' }]}
              >
                <Input
                  prefix={<UserOutlined />}
                  placeholder="用户名"
                  size="large"
                />
              </Form.Item>
              
              <Form.Item
                name="password"
                rules={[{ required: true, message: '请输入密码' }]}
              >
                <Input.Password
                  prefix={<LockOutlined />}
                  placeholder="密码"
                  size="large"
                />
              </Form.Item>
              
              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={loading}
                  block
                  size="large"
                >
                  登录
                </Button>
              </Form.Item>
            </Form>
          </TabPane>
          
          <TabPane tab="注册" key="register">
            <Form onFinish={handleRegister} layout="vertical">
              <Form.Item
                name="username"
                rules={[
                  { required: true, message: '请输入用户名' },
                  { min: 3, max: 20, message: '用户名长度为3-20个字符' }
                ]}
              >
                <Input
                  prefix={<UserOutlined />}
                  placeholder="用户名"
                  size="large"
                />
              </Form.Item>
              
              <Form.Item
                name="password"
                rules={[
                  { required: true, message: '请输入密码' },
                  { min: 6, message: '密码至少6个字符' }
                ]}
              >
                <Input.Password
                  prefix={<LockOutlined />}
                  placeholder="密码"
                  size="large"
                />
              </Form.Item>
              
              <Form.Item
                name="confirmPassword"
                rules={[{ required: true, message: '请确认密码' }]}
              >
                <Input.Password
                  prefix={<LockOutlined />}
                  placeholder="确认密码"
                  size="large"
                />
              </Form.Item>
              
              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={loading}
                  block
                  size="large"
                >
                  注册
                </Button>
              </Form.Item>
            </Form>
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
};

export default LoginForm;