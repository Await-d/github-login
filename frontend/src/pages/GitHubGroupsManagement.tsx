import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  message,
  Popconfirm,
  Tag,
  Modal,
  Input,
  Form,
  ColorPicker
} from 'antd';
import {
  PlusOutlined,
  DeleteOutlined,
  EditOutlined,
  ReloadOutlined,
  FolderOutlined
} from '@ant-design/icons';
import { githubGroupsAPI } from '../services/api';
import type { Color } from 'antd/es/color-picker';

const { TextArea } = Input;

interface GitHubGroup {
  id: number;
  user_id: number;
  name: string;
  description: string | null;
  color: string | null;
  created_at: string;
  updated_at: string;
  account_count: number;
}

const GitHubGroupsManagement: React.FC = () => {
  const [groups, setGroups] = useState<GitHubGroup[]>([]);
  const [loading, setLoading] = useState(false);

  // 添加/编辑分组对话框
  const [modalVisible, setModalVisible] = useState(false);
  const [modalLoading, setModalLoading] = useState(false);
  const [editingGroup, setEditingGroup] = useState<GitHubGroup | null>(null);
  const [form] = Form.useForm();
  const [selectedColor, setSelectedColor] = useState<string>('#1890ff');

  useEffect(() => {
    loadGroups();
  }, []);

  const loadGroups = async () => {
    setLoading(true);
    try {
      const response = await githubGroupsAPI.getGroups();
      if (response.data.success) {
        setGroups(response.data.groups || []);
      }
    } catch (error: any) {
      message.error('加载分组列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = () => {
    setEditingGroup(null);
    form.resetFields();
    setSelectedColor('#1890ff');
    setModalVisible(true);
  };

  const handleEdit = (group: GitHubGroup) => {
    setEditingGroup(group);
    form.setFieldsValue({
      name: group.name,
      description: group.description,
    });
    setSelectedColor(group.color || '#1890ff');
    setModalVisible(true);
  };

  const handleModalSubmit = async () => {
    try {
      const values = await form.validateFields();
      setModalLoading(true);

      const data = {
        name: values.name,
        description: values.description,
        color: selectedColor,
      };

      if (editingGroup) {
        // 更新分组
        const response = await githubGroupsAPI.updateGroup(editingGroup.id, data);
        if (response.data.success) {
          message.success('分组更新成功');
          setModalVisible(false);
          loadGroups();
        }
      } else {
        // 创建分组
        const response = await githubGroupsAPI.createGroup(data);
        if (response.data.success) {
          message.success('分组创建成功');
          setModalVisible(false);
          loadGroups();
        }
      }
    } catch (error: any) {
      if (error.response?.data?.detail) {
        message.error(error.response.data.detail);
      } else {
        message.error(editingGroup ? '更新分组失败' : '创建分组失败');
      }
    } finally {
      setModalLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      const response = await githubGroupsAPI.deleteGroup(id);
      if (response.data.success) {
        message.success('分组删除成功');
        loadGroups();
      }
    } catch (error: any) {
      message.error('删除分组失败');
    }
  };

  const columns = [
    {
      title: '分组名称',
      key: 'name',
      render: (_: any, record: GitHubGroup) => (
        <Space>
          {record.color && (
            <div
              style={{
                width: 12,
                height: 12,
                borderRadius: '50%',
                backgroundColor: record.color,
              }}
            />
          )}
          <FolderOutlined style={{ color: record.color || '#666' }} />
          <span>{record.name}</span>
        </Space>
      ),
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      render: (text: string | null) => text || '-',
    },
    {
      title: '账号数量',
      dataIndex: 'account_count',
      key: 'account_count',
      render: (count: number) => (
        <Tag color={count > 0 ? 'blue' : 'default'}>{count} 个账号</Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text: string) => new Date(text).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: any, record: GitHubGroup) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个分组吗？"
            description="分组中的账号不会被删除，只会解除分组关联"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Card
        title="GitHub 账号分组管理"
        extra={
          <Space>
            <Button icon={<ReloadOutlined />} onClick={loadGroups} loading={loading}>
              刷新
            </Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
              添加分组
            </Button>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={groups}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `显示 ${range[0]}-${range[1]} 条，共 ${total} 个分组`,
          }}
        />
      </Card>

      {/* 添加/编辑分组对话框 */}
      <Modal
        title={editingGroup ? '编辑分组' : '添加分组'}
        open={modalVisible}
        onOk={handleModalSubmit}
        onCancel={() => setModalVisible(false)}
        confirmLoading={modalLoading}
        width={500}
      >
        <Form form={form} layout="vertical" style={{ marginTop: 20 }}>
          <Form.Item
            name="name"
            label="分组名称"
            rules={[
              { required: true, message: '请输入分组名称' },
              { max: 50, message: '分组名称不能超过50个字符' },
            ]}
          >
            <Input placeholder="例如：主力账号、备用账号" />
          </Form.Item>

          <Form.Item name="description" label="描述">
            <TextArea rows={3} placeholder="可选，描述这个分组的用途" />
          </Form.Item>

          <Form.Item label="分组颜色">
            <ColorPicker
              value={selectedColor}
              onChange={(color: Color) => setSelectedColor(color.toHexString())}
              showText
              presets={[
                {
                  label: '推荐颜色',
                  colors: [
                    '#1890ff',
                    '#52c41a',
                    '#faad14',
                    '#f5222d',
                    '#722ed1',
                    '#eb2f96',
                    '#13c2c2',
                    '#fa8c16',
                  ],
                },
              ]}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default GitHubGroupsManagement;
