import React, { useState } from 'react';
import {
  Modal,
  Tabs,
  Form,
  Input,
  Upload,
  Button,
  Space,
  Alert,
  Table,
  Tag,
  Divider,
  Typography,
  message
} from 'antd';
import {
  InboxOutlined,
  FileTextOutlined,
  TableOutlined,
  EyeOutlined,
  CheckOutlined,
  CloseOutlined
} from '@ant-design/icons';

const { TabPane } = Tabs;
const { TextArea } = Input;
const { Dragger } = Upload;
const { Text, Title } = Typography;

interface GitHubGroup {
  id: number;
  name: string;
  color: string | null;
  account_count: number;
}

interface BatchImportModalProps {
  visible: boolean;
  onCancel: () => void;
  onSubmit: (data: any[]) => Promise<void>;
  groups?: GitHubGroup[];
}

interface ParsedAccount {
  username: string;
  password: string;
  totp_secret: string;
  created_at: string;
  group_id?: number;
  group_name?: string;
  status: 'valid' | 'invalid';
  errors?: string[];
}

const BatchImportModal: React.FC<BatchImportModalProps> = ({
  visible,
  onCancel,
  onSubmit,
  groups = []
}) => {
  const [activeTab, setActiveTab] = useState('text');
  const [textInput, setTextInput] = useState('');
  const [parsedData, setParsedData] = useState<ParsedAccount[]>([]);
  const [previewVisible, setPreviewVisible] = useState(false);
  const [loading, setLoading] = useState(false);

  // 解析文本格式数据
  const parseTextData = (text: string): ParsedAccount[] => {
    const lines = text.trim().split('\n').filter(line => line.trim());
    const results: ParsedAccount[] = [];

    lines.forEach((line, index) => {
      const parts = line.split('----');
      const account: ParsedAccount = {
        username: '',
        password: '',
        totp_secret: '',
        created_at: '',
        status: 'valid',
        errors: []
      };

      if (parts.length !== 4) {
        account.status = 'invalid';
        account.errors = [`第${index + 1}行：格式错误，应为"账号----密码----密钥----日期"`];
      } else {
        account.username = parts[0].trim();
        account.password = parts[1].trim();
        account.totp_secret = parts[2].trim();
        account.created_at = parts[3].trim();

        // 数据验证
        const errors: string[] = [];
        if (!account.username) errors.push('用户名不能为空');
        if (!account.password) errors.push('密码不能为空');
        if (!account.totp_secret) errors.push('TOTP密钥不能为空');
        if (!account.created_at) errors.push('日期不能为空');
        
        // TOTP密钥格式验证
        if (account.totp_secret && !/^[A-Z2-7]{16,}$/.test(account.totp_secret)) {
          errors.push('TOTP密钥格式无效');
        }

        // 日期格式验证
        if (account.created_at && !/^\d{4}-\d{2}-\d{2}$/.test(account.created_at)) {
          errors.push('日期格式无效，应为YYYY-MM-DD');
        }

        if (errors.length > 0) {
          account.status = 'invalid';
          account.errors = errors;
        }
      }

      results.push(account);
    });

    return results;
  };

  // 处理文本输入
  const handleTextParse = () => {
    if (!textInput.trim()) {
      return;
    }
    const parsed = parseTextData(textInput);
    setParsedData(parsed);
    setPreviewVisible(true);
  };

  // 处理文件上传
  const handleFileUpload = (file: File) => {
    const fileExtension = file.name.split('.').pop()?.toLowerCase();
    
    if (!['txt', 'csv'].includes(fileExtension || '')) {
      message.error('不支持的文件格式，请上传 .txt 或 .csv 文件');
      return false;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target?.result as string;
      let parsed: ParsedAccount[] = [];
      
      if (fileExtension === 'csv') {
        // 处理CSV格式
        parsed = parseCSVData(text);
      } else {
        // 处理TXT格式
        parsed = parseTextData(text);
      }
      
      setParsedData(parsed);
      setPreviewVisible(true);
    };
    
    reader.onerror = () => {
      message.error('文件读取失败');
    };
    
    reader.readAsText(file, 'UTF-8');
    return false; // 阻止自动上传
  };

  // 解析CSV格式数据
  const parseCSVData = (csvText: string): ParsedAccount[] => {
    const lines = csvText.trim().split('\n').filter(line => line.trim());
    const results: ParsedAccount[] = [];

    // 检查并跳过标题行
    let startIndex = 0;
    if (lines.length > 0) {
      const firstLine = lines[0].toLowerCase();
      if (firstLine.includes('username') || firstLine.includes('用户名')) {
        startIndex = 1;
      }
    }

    const dataLines = lines.slice(startIndex);

    dataLines.forEach((line, index) => {
      // 处理CSV格式，可能包含逗号分隔或分号分隔
      let parts: string[] = [];

      if (line.includes('----')) {
        // 如果包含----分隔符，使用原来的解析方式
        parts = line.split('----').map(part => part.trim());
      } else {
        // 处理CSV中可能带引号的字段
        // 简单处理：分割后去除引号
        if (line.includes(',')) {
          parts = line.split(',').map(part => part.trim().replace(/^"|"$/g, ''));
        } else if (line.includes(';')) {
          parts = line.split(';').map(part => part.trim().replace(/^"|"$/g, ''));
        } else {
          parts = line.split(/\s+/).filter(part => part.trim());
        }
      }

      const account: ParsedAccount = {
        username: '',
        password: '',
        totp_secret: '',
        created_at: '',
        status: 'valid',
        errors: []
      };

      // 根据列数判断格式
      if (parts.length === 6) {
        // 新导出格式: 用户名,密码,TOTP密钥,所属分组,创建时间,更新时间
        account.username = parts[0].trim();
        account.password = parts[1].trim();
        account.totp_secret = parts[2].trim();

        // 处理分组
        const groupName = parts[3].trim();
        if (groupName && groupName !== '' && groupName !== '未分组') {
          account.group_name = groupName;
          const group = groups.find(g => g.name === groupName);
          if (group) {
            account.group_id = group.id;
          }
        }

        // 从创建时间提取日期（格式：2025/7/13 10:30:45 -> 2025-07-13）
        const createdAtStr = parts[4].trim();
        const dateMatch = createdAtStr.match(/(\d{4})[/-](\d{1,2})[/-](\d{1,2})/);
        if (dateMatch) {
          const [, year, month, day] = dateMatch;
          account.created_at = `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
        } else {
          account.created_at = createdAtStr;
        }
      } else if (parts.length === 4) {
        // 旧格式: 用户名,密码,TOTP密钥,日期
        account.username = parts[0].trim();
        account.password = parts[1].trim();
        account.totp_secret = parts[2].trim();
        account.created_at = parts[3].trim();
      } else {
        account.status = 'invalid';
        account.errors = [`第${index + 1}行：格式错误，应包含4列（旧格式）或6列（新导出格式）`];
        results.push(account);
        return;
      }

      // 数据验证
      const errors: string[] = [];
      if (!account.username) errors.push('用户名不能为空');
      if (!account.password) errors.push('密码不能为空');
      if (!account.totp_secret) errors.push('TOTP密钥不能为空');

      // TOTP密钥格式验证
      if (account.totp_secret && !/^[A-Z2-7]{16,}$/.test(account.totp_secret)) {
        errors.push('TOTP密钥格式无效');
      }

      // 日期格式验证（可选）
      if (account.created_at && !/^\d{4}-\d{1,2}-\d{1,2}$/.test(account.created_at)) {
        errors.push('日期格式无效，应为YYYY-MM-DD');
      }

      if (errors.length > 0) {
        account.status = 'invalid';
        account.errors = errors;
      }

      results.push(account);
    });

    return results;
  };

  // 确认导入
  const handleConfirmImport = async () => {
    const validData = parsedData.filter(item => item.status === 'valid');
    if (validData.length === 0) {
      return;
    }

    setLoading(true);
    try {
      await onSubmit(validData);
      handleCancel();
    } catch (error) {
      console.error('导入失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 关闭模态框
  const handleCancel = () => {
    setTextInput('');
    setParsedData([]);
    setPreviewVisible(false);
    setActiveTab('text');
    onCancel();
  };

  // 预览表格列定义
  const previewColumns = [
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status: string) => (
        <Tag color={status === 'valid' ? 'success' : 'error'} icon={status === 'valid' ? <CheckOutlined /> : <CloseOutlined />}>
          {status === 'valid' ? '有效' : '无效'}
        </Tag>
      )
    },
    {
      title: 'GitHub用户名',
      dataIndex: 'username',
      key: 'username',
      render: (text: string) => text || <Text type="secondary">未填写</Text>
    },
    {
      title: '密码',
      dataIndex: 'password',
      key: 'password',
      render: (text: string) => text ? '••••••••' : <Text type="secondary">未填写</Text>
    },
    {
      title: 'TOTP密钥',
      dataIndex: 'totp_secret',
      key: 'totp_secret',
      render: (text: string) => text ? `${text.slice(0, 4)}...` : <Text type="secondary">未填写</Text>
    },
    {
      title: '所属分组',
      dataIndex: 'group_name',
      key: 'group_name',
      render: (text: string, record: ParsedAccount) => {
        if (!text) {
          return <Text type="secondary">未分组</Text>;
        }
        if (record.group_id) {
          return <Tag color="blue">{text}</Tag>;
        }
        return <Tag color="warning">{text}（未找到）</Tag>;
      }
    },
    {
      title: '日期',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text: string) => text || <Text type="secondary">未填写</Text>
    },
    {
      title: '错误信息',
      dataIndex: 'errors',
      key: 'errors',
      render: (errors: string[]) => (
        <div>
          {errors?.map((error, index) => (
            <Text key={index} type="danger" style={{ display: 'block', fontSize: '12px' }}>
              {error}
            </Text>
          ))}
        </div>
      )
    }
  ];

  const validCount = parsedData.filter(item => item.status === 'valid').length;
  const invalidCount = parsedData.filter(item => item.status === 'invalid').length;

  return (
    <Modal
      title="批量导入GitHub账号"
      open={visible}
      onCancel={handleCancel}
      width={800}
      footer={null}
      destroyOnClose
    >
      {!previewVisible ? (
        <div>
          <Alert
            message="支持的数据格式"
            description={
              <div>
                <div>• 旧格式（4列）：账号----密码----密钥----日期</div>
                <div>• 新格式（6列）：用户名,密码,TOTP密钥,所属分组,创建时间,更新时间</div>
                <div style={{ marginTop: 8, fontSize: '12px', color: '#666' }}>
                  提示：直接导入从系统导出的CSV文件，会自动识别格式和分组信息
                </div>
              </div>
            }
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />

          <Tabs activeKey={activeTab} onChange={setActiveTab}>
            <TabPane
              tab={
                <span>
                  <FileTextOutlined />
                  文本导入
                </span>
              }
              key="text"
            >
              <Form layout="vertical">
                <Form.Item label="粘贴账号数据（每行一个账号）">
                  <TextArea
                    value={textInput}
                    onChange={(e) => setTextInput(e.target.value)}
                    placeholder="请粘贴账号数据，格式：账号----密码----密钥----日期&#10;例如：&#10;testuser1----testpass123----ABCDEFGHIJKLMNOP----2025-07-13&#10;testuser2----testpass456----QRSTUVWXYZ123456----2025-07-14"
                    rows={8}
                  />
                </Form.Item>
                <Form.Item>
                  <Button
                    type="primary"
                    onClick={handleTextParse}
                    disabled={!textInput.trim()}
                    icon={<EyeOutlined />}
                  >
                    解析并预览
                  </Button>
                </Form.Item>
              </Form>
            </TabPane>

            <TabPane
              tab={
                <span>
                  <InboxOutlined />
                  文件导入
                </span>
              }
              key="file"
            >
              <Dragger
                name="file"
                multiple={false}
                accept=".txt,.csv"
                beforeUpload={handleFileUpload}
                showUploadList={false}
              >
                <p className="ant-upload-drag-icon">
                  <InboxOutlined />
                </p>
                <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
                <p className="ant-upload-hint">
                  支持 .txt、.csv 格式文件<br/>
                  TXT格式：每行一个账号，使用"----"分隔<br/>
                  CSV格式：支持逗号、分号或空格分隔的4列数据
                </p>
              </Dragger>
            </TabPane>

            <TabPane
              tab={
                <span>
                  <TableOutlined />
                  Excel导入
                </span>
              }
              key="excel"
              disabled
            >
              <Alert
                message="Excel导入功能开发中"
                description="此功能将在后续版本中提供，敬请期待。"
                type="warning"
                showIcon
              />
            </TabPane>
          </Tabs>
        </div>
      ) : (
        <div>
          <div style={{ marginBottom: 16 }}>
            <Title level={4}>导入预览</Title>
            <Space>
              <Tag color="success">{validCount} 个有效账号</Tag>
              <Tag color="error">{invalidCount} 个无效账号</Tag>
            </Space>
          </div>

          <Table
            columns={previewColumns}
            dataSource={parsedData}
            rowKey={(record, index) => index || 0}
            pagination={false}
            scroll={{ y: 300 }}
            size="small"
          />

          <Divider />

          <Space>
            <Button onClick={() => setPreviewVisible(false)}>
              返回编辑
            </Button>
            <Button
              type="primary"
              onClick={handleConfirmImport}
              disabled={validCount === 0}
              loading={loading}
            >
              确认导入 {validCount} 个账号
            </Button>
          </Space>
        </div>
      )}
    </Modal>
  );
};

export default BatchImportModal;