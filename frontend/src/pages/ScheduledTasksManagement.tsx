import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  message,
  Popconfirm,
  Typography,
  Tag,
  Modal,
  Form,
  Input,
  Select,
  Checkbox,
  Row,
  Col,
  Statistic,
  Tooltip,
  Divider
} from 'antd';
import {
  PlusOutlined,
  DeleteOutlined,
  EditOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  ClockCircleOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
  HistoryOutlined
} from '@ant-design/icons';
import { scheduledTasksAPI, githubAPI } from '../services/api';

const { Text } = Typography;
const { Option } = Select;
const { TextArea } = Input;

interface ScheduledTask {
  id: number;
  name: string;
  description: string;
  task_type: string;
  cron_expression: string;
  timezone: string;
  task_params: any;
  is_active: boolean;
  last_run_time: string;
  next_run_time: string;
  last_result: string;
  run_count: number;
  success_count: number;
  error_count: number;
  created_at: string;
  updated_at: string;
}

interface GitHubAccount {
  id: number;
  username: string;
}

interface TaskLog {
  id: number;
  task_id: number;
  start_time: string;
  end_time: string;
  duration: number;
  status: string;
  result_message: string;
  error_details: string;
  execution_data: any;
}

const ScheduledTasksManagement: React.FC = () => {
  const [tasks, setTasks] = useState<ScheduledTask[]>([]);
  const [githubAccounts, setGithubAccounts] = useState<GitHubAccount[]>([]);
  const [loading, setLoading] = useState(false);
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [logsModalVisible, setLogsModalVisible] = useState(false);
  const [currentTaskLogs, setCurrentTaskLogs] = useState<TaskLog[]>([]);
  const [logsLoading, setLogsLoading] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editingTask, setEditingTask] = useState<ScheduledTask | null>(null);
  const [form] = Form.useForm();
  const [editForm] = Form.useForm();

  useEffect(() => {
    loadTasks();
    loadGitHubAccounts();
  }, []);

  const loadTasks = async () => {
    setLoading(true);
    try {
      const response = await scheduledTasksAPI.getTasks();
      if (response.data.success) {
        setTasks(response.data.tasks || []);
      } else {
        message.error('获取定时任务列表失败');
      }
    } catch (error: any) {
      message.error('加载定时任务列表失败');
    } finally {
      setLoading(false);
    }
  };

  const loadGitHubAccounts = async () => {
    try {
      const response = await githubAPI.getAccounts();
      if (response.data.success) {
        setGithubAccounts(response.data.accounts || []);
      }
    } catch (error) {
      console.error('获取GitHub账号列表失败', error);
    }
  };

  const handleCreateTask = async (values: any) => {
    try {
      const response = await scheduledTasksAPI.createGitHubOAuthTask({
        name: values.name,
        description: values.description,
        cron_expression: values.cron_expression,
        github_account_ids: values.github_account_ids,
        target_website: values.target_website || 'https://anyrouter.top',
        retry_count: values.retry_count || 3,
        is_active: values.is_active !== false
      });

      if (response.data.success) {
        message.success('定时任务创建成功');
        setCreateModalVisible(false);
        form.resetFields();
        loadTasks();
      } else {
        message.error('创建失败: ' + response.data.message);
      }
    } catch (error: any) {
      message.error('创建失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleDeleteTask = async (id: number) => {
    try {
      const response = await scheduledTasksAPI.deleteTask(id);
      if (response.data.success) {
        message.success('删除成功');
        loadTasks();
      } else {
        message.error('删除失败');
      }
    } catch (error) {
      message.error('删除失败');
    }
  };

  const handleToggleTask = async (id: number) => {
    try {
      const response = await scheduledTasksAPI.toggleTask(id);
      if (response.data.success) {
        message.success(response.data.message);
        loadTasks();
      } else {
        message.error('操作失败');
      }
    } catch (error) {
      message.error('操作失败');
    }
  };

  const handleRunTask = async (id: number) => {
    const loadingMessage = message.loading('正在执行任务...', 0);
    try {
      const response = await scheduledTasksAPI.runTask(id);
      loadingMessage();
      
      if (response.data.success) {
        message.success('任务执行成功');
        loadTasks();
      } else {
        message.error('任务执行失败: ' + response.data.message);
      }
    } catch (error: any) {
      loadingMessage();
      message.error('任务执行失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleViewLogs = async (task: ScheduledTask) => {
    setLogsModalVisible(true);
    setCurrentTaskLogs([]);
    setLogsLoading(true);
    
    try {
      const response = await scheduledTasksAPI.getTaskLogs(task.id, 50);
      if (response.data.success) {
        setCurrentTaskLogs(response.data.logs || []);
      } else {
        message.error('获取执行日志失败');
      }
    } catch (error) {
      message.error('获取执行日志失败');
    } finally {
      setLogsLoading(false);
    }
  };

  const handleEditTask = (task: ScheduledTask) => {
    setEditingTask(task);
    editForm.setFieldsValue({
      name: task.name,
      description: task.description,
      cron_expression: task.cron_expression,
      github_account_ids: task.task_params?.github_account_ids || [],
      target_website: task.task_params?.target_website || 'https://anyrouter.top',
      retry_count: task.task_params?.retry_count || 3,
      is_active: task.is_active
    });
    setEditModalVisible(true);
  };

  const handleUpdateTask = async (values: any) => {
    if (!editingTask) return;

    try {
      const response = await scheduledTasksAPI.updateTask(editingTask.id, {
        name: values.name,
        description: values.description,
        cron_expression: values.cron_expression,
        task_params: {
          github_account_ids: values.github_account_ids,
          target_website: values.target_website || 'https://anyrouter.top',
          retry_count: values.retry_count || 3
        },
        is_active: values.is_active !== false
      });

      if (response.data.success) {
        message.success('定时任务更新成功');
        setEditModalVisible(false);
        setEditingTask(null);
        editForm.resetFields();
        loadTasks();
      } else {
        message.error('更新失败: ' + response.data.message);
      }
    } catch (error: any) {
      message.error('更新失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  // 预设的cron表达式
  const cronPresets = [
    { label: '每天上午9点', value: '0 9 * * *' },
    { label: '每天上午9点和下午6点', value: '0 9,18 * * *' },
    { label: '每6小时', value: '0 */6 * * *' },
    { label: '每2小时', value: '0 */2 * * *' },
    { label: '工作日上午9点', value: '0 9 * * 1-5' },
    { label: '每周日上午10点', value: '0 10 * * 0' },
    { label: '每月1号上午9点', value: '0 9 1 * *' }
  ];

  const columns = [
    {
      title: '任务名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: ScheduledTask) => (
        <div>
          <Text strong>{text}</Text>
          <br />
          <Text type="secondary" style={{ fontSize: '12px' }}>
            {record.description}
          </Text>
        </div>
      )
    },
    {
      title: '执行计划',
      dataIndex: 'cron_expression',
      key: 'cron_expression',
      render: (text: string, record: ScheduledTask) => (
        <div>
          <Text code>{text}</Text>
          <br />
          <Text type="secondary" style={{ fontSize: '12px' }}>
            下次: {record.next_run_time ? new Date(record.next_run_time).toLocaleString('zh-CN') : '-'}
          </Text>
        </div>
      )
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive: boolean) => (
        <Tag
          icon={isActive ? <CheckCircleOutlined /> : <PauseCircleOutlined />}
          color={isActive ? 'success' : 'default'}
        >
          {isActive ? '启用' : '禁用'}
        </Tag>
      )
    },
    {
      title: '执行统计',
      key: 'stats',
      render: (_: any, record: ScheduledTask) => (
        <div>
          <Text>总计: {record.run_count}</Text>
          <br />
          <Text type="success">成功: {record.success_count}</Text>
          {' / '}
          <Text type="danger">失败: {record.error_count}</Text>
        </div>
      )
    },
    {
      title: '最后执行',
      dataIndex: 'last_run_time',
      key: 'last_run_time',
      render: (text: string, record: ScheduledTask) => (
        <div>
          <Text style={{ fontSize: '12px' }}>
            {text ? new Date(text).toLocaleString('zh-CN') : '未执行'}
          </Text>
          {record.last_result && (
            <>
              <br />
              <Tooltip title={record.last_result}>
                <Text type="secondary" ellipsis style={{ fontSize: '11px' }}>
                  {record.last_result.length > 30 
                    ? record.last_result.substring(0, 30) + '...' 
                    : record.last_result}
                </Text>
              </Tooltip>
            </>
          )}
        </div>
      )
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: any, record: ScheduledTask) => (
        <Space>
          <Tooltip title={record.is_active ? '暂停任务' : '启用任务'}>
            <Button
              size="small"
              type={record.is_active ? 'default' : 'primary'}
              icon={record.is_active ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
              onClick={() => handleToggleTask(record.id)}
            />
          </Tooltip>
          <Tooltip title="立即执行">
            <Button
              size="small"
              type="primary"
              icon={<PlayCircleOutlined />}
              onClick={() => handleRunTask(record.id)}
            />
          </Tooltip>
          <Tooltip title="执行日志">
            <Button
              size="small"
              icon={<HistoryOutlined />}
              onClick={() => handleViewLogs(record)}
            />
          </Tooltip>
          <Tooltip title="编辑">
            <Button
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleEditTask(record)}
            />
          </Tooltip>
          <Popconfirm
            title="确定要删除这个定时任务吗？"
            onConfirm={() => handleDeleteTask(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Tooltip title="删除">
              <Button
                size="small"
                danger
                icon={<DeleteOutlined />}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      )
    }
  ];

  const logColumns = [
    {
      title: '执行时间',
      dataIndex: 'start_time',
      key: 'start_time',
      render: (text: string) => new Date(text).toLocaleString('zh-CN')
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const colorMap = {
          success: 'success',
          failed: 'error',
          running: 'processing'
        };
        return <Tag color={colorMap[status as keyof typeof colorMap] || 'default'}>{status}</Tag>;
      }
    },
    {
      title: '耗时',
      dataIndex: 'duration',
      key: 'duration',
      render: (duration: number) => duration ? `${duration.toFixed(2)}s` : '-'
    },
    {
      title: '执行结果',
      dataIndex: 'result_message',
      key: 'result_message',
      render: (text: string) => (
        <Tooltip title={text}>
          <Text ellipsis>{text?.length > 50 ? text.substring(0, 50) + '...' : text}</Text>
        </Tooltip>
      )
    }
  ];

  // 统计数据
  const totalTasks = tasks.length;
  const activeTasks = tasks.filter(t => t.is_active).length;
  const totalExecutions = tasks.reduce((sum, t) => sum + t.run_count, 0);
  const successRate = totalExecutions > 0 
    ? ((tasks.reduce((sum, t) => sum + t.success_count, 0) / totalExecutions) * 100).toFixed(1)
    : 0;

  return (
    <div style={{ padding: '24px' }}>
      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总任务数"
              value={totalTasks}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="启用任务"
              value={activeTasks}
              suffix={`/ ${totalTasks}`}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="总执行次数"
              value={totalExecutions}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="成功率"
              value={successRate}
              suffix="%"
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 主要内容 */}
      <Card
        title={
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <ClockCircleOutlined style={{ marginRight: 8 }} />
            <span>定时任务管理</span>
          </div>
        }
        extra={
          <Space>
            <Button
              icon={<ReloadOutlined />}
              onClick={loadTasks}
              loading={loading}
            >
              刷新
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setCreateModalVisible(true)}
            >
              创建定时任务
            </Button>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={tasks}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `显示 ${range[0]}-${range[1]} 条，共 ${total} 个任务`
          }}
        />
      </Card>

      {/* 创建任务模态框 */}
      <Modal
        title="创建GitHub OAuth定时任务"
        open={createModalVisible}
        onCancel={() => {
          setCreateModalVisible(false);
          form.resetFields();
        }}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreateTask}
          initialValues={{
            target_website: 'https://anyrouter.top',
            retry_count: 3,
            is_active: true
          }}
        >
          <Form.Item
            name="name"
            label="任务名称"
            rules={[{ required: true, message: '请输入任务名称' }]}
          >
            <Input placeholder="例如：每日anyrouter登录" />
          </Form.Item>

          <Form.Item
            name="description"
            label="任务描述"
          >
            <TextArea placeholder="任务描述信息" rows={2} />
          </Form.Item>

          <Form.Item
            name="cron_expression"
            label="执行计划"
            rules={[{ required: true, message: '请选择或输入cron表达式' }]}
          >
            <Select
              placeholder="选择预设计划或输入自定义cron表达式"
              allowClear
              showSearch
            >
              {cronPresets.map(preset => (
                <Option key={preset.value} value={preset.value}>
                  {preset.label} ({preset.value})
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="github_account_ids"
            label="选择GitHub账号"
            rules={[{ required: true, message: '请选择至少一个GitHub账号' }]}
          >
            <Select
              mode="multiple"
              placeholder="选择要执行登录的GitHub账号"
              showSearch
              optionFilterProp="children"
            >
              {githubAccounts.map(account => (
                <Option key={account.id} value={account.id}>
                  {account.username}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="target_website"
                label="目标网站"
              >
                <Input placeholder="https://anyrouter.top" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="retry_count"
                label="失败重试次数"
              >
                <Select>
                  <Option value={1}>1次</Option>
                  <Option value={2}>2次</Option>
                  <Option value={3}>3次</Option>
                  <Option value={5}>5次</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="is_active"
            valuePropName="checked"
          >
            <Checkbox>立即启用任务</Checkbox>
          </Form.Item>

          <Divider />

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => {
                setCreateModalVisible(false);
                form.resetFields();
              }}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                创建任务
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 编辑任务模态框 */}
      <Modal
        title="编辑定时任务"
        open={editModalVisible}
        onCancel={() => {
          setEditModalVisible(false);
          setEditingTask(null);
          editForm.resetFields();
        }}
        footer={null}
        width={600}
      >
        <Form
          form={editForm}
          layout="vertical"
          onFinish={handleUpdateTask}
        >
          <Form.Item
            name="name"
            label="任务名称"
            rules={[{ required: true, message: '请输入任务名称' }]}
          >
            <Input placeholder="例如：每日anyrouter登录" />
          </Form.Item>

          <Form.Item
            name="description"
            label="任务描述"
          >
            <TextArea placeholder="任务描述信息" rows={2} />
          </Form.Item>

          <Form.Item
            name="cron_expression"
            label="执行计划"
            rules={[{ required: true, message: '请选择或输入cron表达式' }]}
          >
            <Select
              placeholder="选择预设计划或输入自定义cron表达式"
              allowClear
              showSearch
            >
              {cronPresets.map(preset => (
                <Option key={preset.value} value={preset.value}>
                  {preset.label} ({preset.value})
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="github_account_ids"
            label="选择GitHub账号"
            rules={[{ required: true, message: '请选择至少一个GitHub账号' }]}
          >
            <Select
              mode="multiple"
              placeholder="选择要执行登录的GitHub账号"
              showSearch
              optionFilterProp="children"
            >
              {githubAccounts.map(account => (
                <Option key={account.id} value={account.id}>
                  {account.username}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="target_website"
                label="目标网站"
              >
                <Input placeholder="https://anyrouter.top" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="retry_count"
                label="失败重试次数"
              >
                <Select>
                  <Option value={1}>1次</Option>
                  <Option value={2}>2次</Option>
                  <Option value={3}>3次</Option>
                  <Option value={5}>5次</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="is_active"
            valuePropName="checked"
          >
            <Checkbox>启用任务</Checkbox>
          </Form.Item>

          <Divider />

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => {
                setEditModalVisible(false);
                setEditingTask(null);
                editForm.resetFields();
              }}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                保存更新
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 执行日志模态框 */}
      <Modal
        title="任务执行日志"
        open={logsModalVisible}
        onCancel={() => setLogsModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setLogsModalVisible(false)}>
            关闭
          </Button>
        ]}
        width={800}
      >
        <Table
          columns={logColumns}
          dataSource={currentTaskLogs}
          rowKey="id"
          loading={logsLoading}
          pagination={{
            pageSize: 10,
            showTotal: (total, range) => `显示 ${range[0]}-${range[1]} 条，共 ${total} 条日志`
          }}
          size="small"
        />
      </Modal>
    </div>
  );
};

export default ScheduledTasksManagement;