import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Table, 
  Button, 
  Space, 
  Modal, 
  Form, 
  Input, 
  Select, 
  Tag, 
  message, 
  Tooltip,
  Typography,
  Row,
  Col,
  Statistic,
  Alert,
  Divider
} from 'antd';
import { 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined, 
  EyeOutlined, 
  SearchOutlined,
  ReloadOutlined,
  GlobalOutlined,
  ClusterOutlined,
  DesktopOutlined,
  BugOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import { targetAPI } from '../services/api';

const { Title, Text } = Typography;
const { Option } = Select;

const TargetsPage = () => {
  const [targets, setTargets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [modalType, setModalType] = useState('create'); // 'create' or 'edit'
  const [form] = Form.useForm();
  const [selectedTarget, setSelectedTarget] = useState(null);

  // 统计数据
  const [stats, setStats] = useState({
    total: 0,
    active: 0,
    inactive: 0,
    web: 0,
    network: 0,
    system: 0
  });

  useEffect(() => {
    fetchTargets();
    fetchStats();
  }, []);

  const fetchTargets = async () => {
    setLoading(true);
    try {
      const response = await targetAPI.list();
      setTargets(response.data.targets || []);
    } catch (error) {
      message.error('获取目标列表失败');
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await targetAPI.statistics();
      setStats(response.data);
    } catch (error) {
      console.error('获取统计信息失败:', error);
    }
  };

  const handleCreate = () => {
    setModalType('create');
    setModalVisible(true);
    form.resetFields();
  };

  const handleEdit = (target) => {
    setModalType('edit');
    setSelectedTarget(target);
    setModalVisible(true);
    form.setFieldsValue(target);
  };

  const handleDelete = async (target) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除目标 "${target.name}" 吗？`,
      onOk: async () => {
        try {
          await targetAPI.delete(target.id);
          message.success('删除成功');
          fetchTargets();
          fetchStats();
        } catch (error) {
          message.error('删除失败');
        }
      }
    });
  };

  const handleSubmit = async (values) => {
    try {
      if (modalType === 'create') {
        await targetAPI.create(values);
        message.success('创建成功');
      } else {
        await targetAPI.update(selectedTarget.id, values);
        message.success('更新成功');
      }
      setModalVisible(false);
      fetchTargets();
      fetchStats();
    } catch (error) {
      message.error('操作失败');
    }
  };

  const getStatusColor = (status) => {
    const statusMap = {
      'active': 'green',
      'inactive': 'red',
      'pending': 'orange',
      'scanning': 'blue'
    };
    return statusMap[status] || 'default';
  };

  const getTargetTypeIcon = (type) => {
    const typeMap = {
      'web': <GlobalOutlined style={{ color: '#1890ff' }} />,
      'network': <ClusterOutlined style={{ color: '#52c41a' }} />,
      'system': <DesktopOutlined style={{ color: '#fa8c16' }} />
    };
    return typeMap[type] || <BugOutlined style={{ color: '#722ed1' }} />;
  };

  const columns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <Space>
          {getTargetTypeIcon(record.target_type)}
          <Text strong>{text}</Text>
        </Space>
      )
    },
    {
      title: '类型',
      dataIndex: 'target_type',
      key: 'target_type',
      render: (type) => (
        <Tag color={type === 'web' ? 'blue' : type === 'network' ? 'green' : 'orange'}>
          {type.toUpperCase()}
        </Tag>
      )
    },
    {
      title: '地址',
      dataIndex: 'target_url',
      key: 'target_url',
      render: (url) => (
        <Tooltip title={url}>
          <Text ellipsis style={{ maxWidth: 200 }}>
            {url || 'N/A'}
          </Text>
        </Tooltip>
      )
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => (
        <Tag color={getStatusColor(status)}>
          {status.toUpperCase()}
        </Tag>
      )
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => (
        <Text type="secondary">
          {date ? new Date(date).toLocaleDateString() : 'N/A'}
        </Text>
      )
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button 
            type="link" 
            size="small" 
            icon={<EyeOutlined />}
            onClick={() => handleEdit(record)}
          >
            查看
          </Button>
          <Button 
            type="link" 
            size="small" 
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Button 
            type="link" 
            size="small" 
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record)}
          >
            删除
          </Button>
        </Space>
      )
    }
  ];

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <Title level={2}>目标管理</Title>
        <Text type="secondary">管理和配置扫描目标</Text>
      </div>

      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="目标总数"
              value={stats.total || 0}
              prefix={<ClusterOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="活跃目标"
              value={stats.active || 0}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Web目标"
              value={stats.web || 0}
              prefix={<GlobalOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="网络目标"
              value={stats.network || 0}
              prefix={<DesktopOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 操作区域 */}
      <Card 
        title="目标列表" 
        extra={
          <Space>
            <Button 
              type="primary" 
              icon={<PlusOutlined />}
              onClick={handleCreate}
            >
              添加目标
            </Button>
            <Button 
              icon={<ReloadOutlined />}
              onClick={fetchTargets}
              loading={loading}
            >
              刷新
            </Button>
          </Space>
        }
        style={{ marginBottom: '16px' }}
      >
        <Table
          columns={columns}
          dataSource={targets}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `显示 ${range[0]}-${range[1]} 条，共 ${total} 条`
          }}
        />
      </Card>

      {/* 模态框 */}
      <Modal
        title={modalType === 'create' ? '添加目标' : '编辑目标'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="name"
            label="目标名称"
            rules={[{ required: true, message: '请输入目标名称' }]}
          >
            <Input placeholder="请输入目标名称" />
          </Form.Item>

          <Form.Item
            name="target_type"
            label="目标类型"
            rules={[{ required: true, message: '请选择目标类型' }]}
          >
            <Select placeholder="请选择目标类型">
              <Option value="web">Web应用</Option>
              <Option value="network">网络设备</Option>
              <Option value="system">系统</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="target_url"
            label="目标地址"
            rules={[{ required: true, message: '请输入目标地址' }]}
          >
            <Input placeholder="请输入目标地址" />
          </Form.Item>

          <Form.Item
            name="description"
            label="描述"
          >
            <Input.TextArea 
              placeholder="请输入目标描述" 
              rows={3}
            />
          </Form.Item>

          <Form.Item
            name="status"
            label="状态"
            initialValue="active"
          >
            <Select>
              <Option value="active">活跃</Option>
              <Option value="inactive">非活跃</Option>
              <Option value="pending">待处理</Option>
            </Select>
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                {modalType === 'create' ? '创建' : '更新'}
              </Button>
              <Button onClick={() => setModalVisible(false)}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default TargetsPage;