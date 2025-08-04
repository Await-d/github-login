import React, { useEffect } from 'react';
import { Modal, Form, Input, Button, Select, message } from 'antd';
import { LinkOutlined, UserOutlined, LockOutlined, GlobalOutlined } from '@ant-design/icons';

const { Option } = Select;

interface ApiWebsite {
  id: number;
  name: string;
  type: string;
  login_url: string;
  username: string;
  password?: string;
  is_logged_in: string;
  balance: number;
  created_at: string;
  updated_at: string;
}

interface ApiWebsiteFormProps {
  visible: boolean;
  onCancel: () => void;
  onSubmit: (values: any) => Promise<void>;
  website?: ApiWebsite;
}

const ApiWebsiteForm: React.FC<ApiWebsiteFormProps> = ({
  visible,
  onCancel,
  onSubmit,
  website
}) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = React.useState(false);

  useEffect(() => {
    if (visible) {
      if (website) {
        // 编辑模式，填充表单
        form.setFieldsValue({
          name: website.name,
          type: website.type,
          login_url: website.login_url,
          username: website.username,
          password: website.password || ''
        });
      } else {
        // 新增模式，重置表单
        form.resetFields();
        // 设置默认值
        form.setFieldsValue({
          type: 'api网站1',
          login_url: 'https://anyrouter.top/login'
        });
      }
    }
  }, [visible, website, form]);

  const handleSubmit = async (values: any) => {
    setLoading(true);
    try {
      await onSubmit(values);
      form.resetFields();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '操作失败');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    form.resetFields();
    onCancel();
  };

  return (
    <Modal
      title={website ? '编辑API网站' : '添加API网站'}
      open={visible}
      onCancel={handleCancel}
      footer={null}
      width={600}
      destroyOnClose
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={{
          type: 'api网站1',
          login_url: 'https://anyrouter.top/login'
        }}
      >
        <Form.Item
          name="name"
          label="网站名称"
          rules={[
            { required: true, message: '请输入网站名称' },
            { max: 100, message: '网站名称不能超过100个字符' }
          ]}
        >
          <Input
            prefix={<GlobalOutlined />}
            placeholder="例如：anyrouter.top"
            size="large"
          />
        </Form.Item>

        <Form.Item
          name="type"
          label="网站类型"
          rules={[{ required: true, message: '请选择网站类型' }]}
        >
          <Select size="large" placeholder="选择网站类型">
            <Option value="api网站1">api网站1</Option>
            <Option value="api网站2">api网站2</Option>
            <Option value="其他">其他</Option>
          </Select>
        </Form.Item>

        <Form.Item
          name="login_url"
          label="登录URL"
          rules={[
            { required: true, message: '请输入登录URL' },
            { type: 'url', message: '请输入有效的URL' }
          ]}
        >
          <Input
            prefix={<LinkOutlined />}
            placeholder="https://anyrouter.top/login"
            size="large"
          />
        </Form.Item>

        <Form.Item
          name="username"
          label="登录用户名"
          rules={[
            { required: true, message: '请输入登录用户名' },
            { max: 50, message: '用户名不能超过50个字符' }
          ]}
        >
          <Input
            prefix={<UserOutlined />}
            placeholder="网站登录用户名"
            size="large"
          />
        </Form.Item>

        <Form.Item
          name="password"
          label="登录密码"
          rules={[
            { required: !website, message: '请输入登录密码' },
            { min: 1, message: '密码不能为空' }
          ]}
        >
          <Input.Password
            prefix={<LockOutlined />}
            placeholder={website ? "留空则不修改密码" : "网站登录密码"}
            size="large"
          />
        </Form.Item>

        <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
          <Button onClick={handleCancel} style={{ marginRight: 8 }}>
            取消
          </Button>
          <Button
            type="primary"
            htmlType="submit"
            loading={loading}
            size="large"
          >
            {website ? '更新' : '添加'}
          </Button>
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default ApiWebsiteForm;