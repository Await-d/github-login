import React, { useEffect } from 'react';
import { Modal, Form, Input, DatePicker } from 'antd';
import dayjs from 'dayjs';

interface GitHubAccount {
  id?: number;
  username: string;
  password: string;
  totp_secret: string;
  created_at: string;
}

interface Props {
  visible: boolean;
  onCancel: () => void;
  onSubmit: (values: GitHubAccount) => Promise<void>;
  account?: GitHubAccount;
  loading?: boolean;
}

const GitHubAccountForm: React.FC<Props> = ({
  visible,
  onCancel,
  onSubmit,
  account,
  loading = false
}) => {
  const [form] = Form.useForm();

  useEffect(() => {
    if (visible) {
      if (account) {
        form.setFieldsValue({
          ...account,
          created_at: account.created_at ? dayjs(account.created_at) : dayjs()
        });
      } else {
        form.resetFields();
        form.setFieldsValue({
          created_at: dayjs()
        });
      }
    }
  }, [visible, account, form]);

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      const formattedValues = {
        ...values,
        created_at: values.created_at.format('YYYY-MM-DD')
      };
      await onSubmit(formattedValues);
      form.resetFields();
    } catch (error) {
      console.error('Form validation failed:', error);
    }
  };

  return (
    <Modal
      title={account ? '编辑GitHub账号' : '添加GitHub账号'}
      open={visible}
      onCancel={onCancel}
      onOk={handleSubmit}
      confirmLoading={loading}
      width={500}
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={{
          created_at: dayjs()
        }}
      >
        <Form.Item
          name="username"
          label="GitHub用户名"
          rules={[{ required: true, message: '请输入GitHub用户名' }]}
        >
          <Input placeholder="请输入GitHub用户名" />
        </Form.Item>

        <Form.Item
          name="password"
          label="GitHub密码"
          rules={[{ required: true, message: '请输入GitHub密码' }]}
        >
          <Input.Password placeholder="请输入GitHub密码" />
        </Form.Item>

        <Form.Item
          name="totp_secret"
          label="TOTP密钥"
          rules={[
            { required: true, message: '请输入TOTP密钥' },
            { 
              pattern: /^[A-Z2-7]{16,32}$/, 
              message: 'TOTP密钥格式不正确（应为16-32位大写字母和数字2-7）' 
            }
          ]}
          extra="请输入16-32位的TOTP密钥，例如：ABCDEFGHIJKLMNOP"
        >
          <Input 
            placeholder="请输入TOTP密钥" 
            style={{ fontFamily: 'monospace' }}
          />
        </Form.Item>

        <Form.Item
          name="created_at"
          label="创建日期"
          rules={[{ required: true, message: '请选择创建日期' }]}
        >
          <DatePicker
            style={{ width: '100%' }}
            format="YYYY-MM-DD"
            placeholder="请选择创建日期"
          />
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default GitHubAccountForm;