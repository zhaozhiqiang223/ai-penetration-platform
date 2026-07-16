import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Button, 
  Space, 
  Tag, 
  message, 
  Typography,
  Row,
  Col,
  Statistic,
  Alert,
  Descriptions,
  Timeline,
  Table,
  Modal,
  Form,
  Input,
  Select,
  Switch,
  Divider,
  Badge,
  Progress
} from 'antd';
import { 
  ArrowLeftOutlined, 
  EditOutlined, 
  DeleteOutlined, 
  EyeOutlined,
  GlobalOutlined,
  ClusterOutlined,
  DesktopOutlined,
  BugOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ClockCircleOutlined,
  ReloadOutlined,
  PlayCircleOutlined,
  FileTextOutlined,
  BarChartOutlined
} from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import { targetAPI, scanAPI } from '../services/api';

const { Title, Text } = Typography;
const { Option } = Select;

const TargetDetailPage = () => {
  const { targetId } = useParams();
  const navigate = useNavigate();
  
  const [target, setTarget] = useState(null);
  const [loading, setLoading] = useState(false);
  const [scans, setScans] = useState([]);
  const [vulnerabilities, setVulnerabilities] = useState([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    if (targetId) {
      fetchTargetDetail();
      fetchTargetScans();
      fetchTargetVulnerabilities();
    }
  }, [targetId]);

  const fetchTargetDetail = async () => {
    setLoading(true);
    try {
      const response = await targetAPI.get(targetId);
      setTarget(response.data);
    } catch (error) {
      message.error('获取目标详情失败');
    } finally {
      setLoading(false);
    }
  };

  const fetchTargetScans = async () => {
    try {
      const response = await scanAPI.list({ target_id: targetId });
      setScans(response.data.scans || []);
    } catch (error) {
      console.error('获取扫描列表失败:', error);
    }
  };

  const fetchTargetVulnerabilities = async () => {
    try {
      const response = await targetAPI.get(`${targetId}/vulnerabilities`);
      setVulnerabilities(response.data.vulnerabilities || []);
    } catch (error) {
      console.error('获取漏洞信息失败:', error);
    }
  };

  const handleEdit = () => {
    setModalVisible(true);
    form.setFieldsValue(target);
  };

  const handleDelete = () => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除目标 "${target.name}" 吗？此操作不可恢复！`,
      onOk: async () => {
        try {
          await targetAPI.delete(targetId);
          message.success('删除成功');
          navigate('/targets');
        } catch (error) {
          message.error('删除失败');
        }
      }
    });
  };

  const handleSubmit = async (values) => {
    try {
      await targetAPI.update(targetId, values);
      message.success('更新成功');
      setModalVisible(false);
      fetchTargetDetail();
    } catch (error) {
      message.error('更新失败');
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

  const getSeverityColor = (severity) => {
    const severityMap = {
      'critical': 'red',
      'high': 'orange',
      'medium': 'yellow',
      'low': 'blue',
      'info': 'green'
    };
    return severityMap[severity] || 'default';
  };

  const scanColumns = [
    {
      title: '扫描名称',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <Space>
          <FileTextOutlined style={{ color: '#1890ff' }} />
          <Text strong>{text}</Text>
        </Space>
      )
    },
    {
      title: '类型',
      dataIndex: 'scan_type',
      key: 'scan_type',
      render: (type) => (
        <Tag color={type === 'vulnerability' ? 'orange' : type === 'penetration' ? 'red' : 'blue'}>
          {type.toUpperCase()}
        </Tag>
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
      title: '进度',
      dataIndex: 'progress',
      key: 'progress',
      render: (progress) => (
        <Progress 
          percent={progress || 0} 
          size="small" 
          status={progress === 100 ? 'success' : 'active'}
        />
      )
    },
    {
      title: '漏洞发现',
      key: 'vulnerabilities',
      render: (_, record) => (
        <Space>
          {record.critical_findings > 0 && (
            <Tag color="red">严重: {record.critical_findings}</Tag>
          )}
          {record.high_findings > 0 && (
            <Tag color="orange">高危: {record.high_findings}</Tag>
          )}
          {record.medium_findings > 0 && (
            <Tag color="yellow">中危: {record.medium_findings}</Tag>
          )}
          {record.low_findings > 0 && (
            <Tag color="blue">低危: {record.low_findings}</Tag>
          )}
        </Space>
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
            onClick={() => navigate(`/scans/${record.id}`)}
          >
            查看
          </Button>
        </Space>
      )
    }
  ];

  const vulnerabilityColumns = [
    {
      title: '漏洞名称',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <Space>
          <BugOutlined style={{ color: getSeverityColor(record.severity) }} />
          <Text strong>{text}</Text>
        </Space>
      )
    },
    {
      title: '严重程度',
      dataIndex: 'severity',
      key: 'severity',
      render: (severity) => (
        <Tag color={getSeverityColor(severity)}>
          {severity.toUpperCase()}
        </Tag>
      )
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type'
    },
    {
      title: '发现时间',
      dataIndex: 'discovered_at',
      key: 'discovered_at',
      render: (date) => (
        <Text type="secondary">
          {date ? new Date(date).toLocaleString() : 'N/A'}
        </Text>
      )
    }
  ];

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '200px' }}>
        <div>Loading...</div>
      </div>
    );
  }

  if (!target) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Text type="danger">目标不存在</Text>
      </div>
    );
  }

  // 计算统计数据
  const stats = {
    totalScans: scans.length,
    completedScans: scans.filter(s => s.status === 'completed').length,
    criticalVulnerabilities: vulnerabilities.filter(v => v.severity === 'critical').length,
    highVulnerabilities: vulnerabilities.filter(v => v.severity === 'high').length,
    totalVulnerabilities: vulnerabilities.length
  };

  return (
    <div>
      {/* 返回按钮 */}
      <div style={{ marginBottom: '24px' }}>
        <Button 
          icon={<ArrowLeftOutlined />} 
          onClick={() => navigate('/targets')}
        >
          返回目标列表
        </Button>
      </div>

      {/* 目标概览 */}
      <Card title="目标概览" style={{ marginBottom: '24px' }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="目标名称"
              value={target.name}
              prefix={getTargetTypeIcon(target.target_type)}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="目标类型"
              value={target.target_type.toUpperCase()}
              prefix={<ClusterOutlined />}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="目标状态"
              value={target.status.toUpperCase()}
              prefix={target.status === 'active' ? <CheckCircleOutlined /> : <ExclamationCircleOutlined />}
              valueStyle={{ color: getStatusColor(target.status) === 'green' ? '#52c41a' : '#ff4d4f' }}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="创建时间"
              value={target.created_at ? new Date(target.created_at).toLocaleDateString() : 'N/A'}
              prefix={<ClockCircleOutlined />}
            />
          </Col>
        </Row>

        <Descriptions title="详细信息" style={{ marginTop: '16px' }}>
          <Descriptions.Item label="目标地址">
            {target.target_url || 'N/A'}
          </Descriptions.Item>
          <Descriptions.Item label="端口">
            {target.port || 'N/A'}
          </Descriptions.Item>
          <Descriptions.Item label="协议">
            {target.protocol || 'N/A'}
          </Descriptions.Item>
          <Descriptions.Item label="标签">
            {target.tags ? target.tags.map(tag => (
              <Tag key={tag} color="blue">{tag}</Tag>
            )) : 'N/A'}
          </Descriptions.Item>
          <Descriptions.Item label="描述" span={3}>
            {target.description || '暂无描述'}
          </Descriptions.Item>
        </Descriptions>

        <Divider />

        <Space>
          <Button 
            type="primary" 
            icon={<EditOutlined />}
            onClick={handleEdit}
          >
            编辑目标
          </Button>
          <Button 
            type="primary" 
            icon={<PlayCircleOutlined />}
            onClick={() => navigate('/scans?target_id=' + targetId)}
          >
            创建扫描
          </Button>
          <Button 
            icon={<ReloadOutlined />}
            onClick={fetchTargetDetail}
            loading={loading}
          >
            刷新
          </Button>
          <Button 
            danger
            icon={<DeleteOutlined />}
            onClick={handleDelete}
          >
            删除目标
          </Button>
        </Space>
      </Card>

      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="总扫描数"
              value={stats.totalScans}
              prefix={<FileTextOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="已完成扫描"
              value={stats.completedScans}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="严重漏洞"
              value={stats.criticalVulnerabilities}
              prefix={<ExclamationCircleOutlined />}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="高危漏洞"
              value={stats.highVulnerabilities}
              prefix={<BugOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 扫描历史 */}
      <Card title="扫描历史" style={{ marginBottom: '24px' }}>
        <Table
          columns={scanColumns}
          dataSource={scans}
          rowKey="id"
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `显示 ${range[0]}-${range[1]} 条，共 ${total} 条`
          }}
        />
      </Card>

      {/* 漏洞历史 */}
      <Card title="漏洞历史">
        <Table
          columns={vulnerabilityColumns}
          dataSource={vulnerabilities}
          rowKey="id"
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `显示 ${range[0]}-${range[1]} 条，共 ${total} 条`
          }}
        />
      </Card>

      {/* 编辑目标模态框 */}
      <Modal
        title="编辑目标"
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={700}
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
                更新
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

export default TargetDetailPage;