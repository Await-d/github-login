import React, { useState } from 'react';
import {
  Modal,
  Form,
  Input,
  Button,
  message,
  Tabs,
  Space,
  Typography,
  Divider
} from 'antd';
import {
  UserOutlined,
  LockOutlined,
  EyeInvisibleOutlined,
  EyeTwoTone
} from '@ant-design/icons';
import { authAPI } from '../services/api';

const { TabPane } = Tabs;
const { Title, Text } = Typography;

interface UserSettingsModalProps {
  visible: boolean;
  onCancel: () => void;
  user: any;
  onUserUpdate: (user: any) => void;
}

const UserSettingsModal: React.FC<UserSettingsModalProps> = ({
  visible,
  onCancel,
  user,
  onUserUpdate
}) => {
  const [userForm] = Form.useForm();
  const [passwordForm] = Form.useForm();
  const [userLoading, setUserLoading] = useState(false);
  const [passwordLoading, setPasswordLoading] = useState(false);

  const handleUserInfoUpdate = async (values: any) => {
    setUserLoading(true);
    try {
      const response = await authAPI.updateUser({
        username: values.username
      });
      
      if (response.data.success) {
        message.success('用户信息更新成功');
        onUserUpdate(response.data.user);
        userForm.resetFields();
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '更新失败');
    } finally {
      setUserLoading(false);
    }
  };

  const handlePasswordChange = async (values: any) => {
    setPasswordLoading(true);
    try {
      const response = await authAPI.changePassword({
        current_password: values.currentPassword,
        new_password: values.newPassword
      });
      
      if (response.data.success) {
        message.success('密码修改成功');
        passwordForm.resetFields();
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '密码修改失败');
    } finally {
      setPasswordLoading(false);
    }
  };

  const handleCancel = () => {
    userForm.resetFields();
    passwordForm.resetFields();
    onCancel();
  };

  return (
    <Modal
      title="用户设置"
      open={visible}
      onCancel={handleCancel}
      footer={null}
      width={500}
    >
      <Tabs defaultActiveKey="profile" type="card">
        <TabPane
          tab={
            <span>
              <UserOutlined />
              个人资料
            </span>
          }
          key="profile"
        >
          <div style={{ padding: '16px 0' }}>
            <Title level={5}>当前用户信息</Title>
            <Space direction="vertical" style={{ width: '100%', marginBottom: 24 }}>
              <div>
                <Text type="secondary">用户名：</Text>
                <Text strong>{user?.username}</Text>
              </div>
              <div>
                <Text type="secondary">创建时间：</Text>
                <Text>{user?.created_at ? new Date(user.created_at).toLocaleString('zh-CN') : '-'}</Text>
              </div>
            </Space>
            
            <Divider />
            
            <Title level={5}>修改用户名</Title>
            <Form
              form={userForm}
              layout="vertical"
              onFinish={handleUserInfoUpdate}
              initialValues={{ username: user?.username }}
            >
              <Form.Item
                label="新用户名"
                name="username"
                rules={[
                  { required: true, message: '请输入用户名' },
                  { min: 3, message: '用户名至少3个字符' },
                  { max: 20, message: '用户名不能超过20个字符' }
                ]}
              >
                <Input
                  prefix={<UserOutlined />}
                  placeholder="输入新用户名"
                />
              </Form.Item>
              
              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={userLoading}
                  block
                >
                  更新用户名
                </Button>
              </Form.Item>
            </Form>
          </div>
        </TabPane>
        
        <TabPane
          tab={
            <span>
              <LockOutlined />
              修改密码
            </span>
          }
          key="password"
        >
          <div style={{ padding: '16px 0' }}>
            <Title level={5}>修改登录密码</Title>
            <Form
              form={passwordForm}
              layout="vertical"
              onFinish={handlePasswordChange}
            >
              <Form.Item
                label="当前密码"
                name="currentPassword"
                rules={[
                  { required: true, message: '请输入当前密码' }
                ]}
              >
                <Input.Password
                  prefix={<LockOutlined />}
                  placeholder="输入当前密码"
                  iconRender={(visible) => (visible ? <EyeTwoTone /> : <EyeInvisibleOutlined />)}
                />
              </Form.Item>
              
              <Form.Item
                label="新密码"
                name="newPassword"
                rules={[
                  { required: true, message: '请输入新密码' },
                  { min: 6, message: '密码至少6个字符' }
                ]}
              >
                <Input.Password
                  prefix={<LockOutlined />}
                  placeholder="输入新密码"
                  iconRender={(visible) => (visible ? <EyeTwoTone /> : <EyeInvisibleOutlined />)}
                />
              </Form.Item>
              
              <Form.Item
                label="确认新密码"
                name="confirmPassword"
                dependencies={['newPassword']}
                rules={[
                  { required: true, message: '请确认新密码' },
                  ({ getFieldValue }) => ({
                    validator(_, value) {
                      if (!value || getFieldValue('newPassword') === value) {
                        return Promise.resolve();
                      }
                      return Promise.reject(new Error('两次输入的密码不一致'));
                    },
                  }),
                ]}
              >
                <Input.Password
                  prefix={<LockOutlined />}
                  placeholder="再次输入新密码"
                  iconRender={(visible) => (visible ? <EyeTwoTone /> : <EyeInvisibleOutlined />)}
                />
              </Form.Item>
              
              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={passwordLoading}
                  block
                >
                  修改密码
                </Button>
              </Form.Item>
            </Form>
          </div>
        </TabPane>
      </Tabs>
    </Modal>
  );
};

export default UserSettingsModal;