import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Row, 
  Col, 
  Button, 
  Table, 
  Tag, 
  Modal, 
  Form, 
  Input, 
  Select, 
  DatePicker, 
  Space, 
  message,
  Progress,
  Alert,
  Popconfirm,
  Tooltip
} from 'antd';
import { 
  PlusOutlined, 
  SearchOutlined, 
  ReloadOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  StopOutlined,
  EyeOutlined,
  DeleteOutlined,
  FilterOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

const { Option } = Select;
const { RangePicker } = DatePicker;

const ScansPage = () => {
  const [loading, setLoading] = useState(false);
  const [scans, setScans] = useState([]);
  const [total, setTotal] = useState(0);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    showSizeChanger: true,
    showQuickJumper: true,
    showTotal: (total, range) => `显示 ${range[0]}-${range[1]} 条，共 ${total} 条`
  });
  const [filters, setFilters] = useState({
    status: null,
    scan_type: null,
    target_type: null,
    date_range: null
  });
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [selectedScan, setSelectedScan] = useState(null);
  const [form] = Form.useForm();
  const navigate = useNavigate();

  const columns = [
    {
      title: '扫描名称',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <Button 
          type="link" 
          onClick={() => navigate(`/scans/${record.id}`)}
          style={{ padding: 0 }}
        >
          {text}
        </Button>
      ),
    },
    {
      title: '目标',
      dataIndex: 'target_url',
      key: 'target_url',
      render: (text, record) => (
        <div>
          <div>{text || record.target_ip}</div>
          <div style={{ fontSize: '12px', color: '#666' }}>
            {record.target_type?.toUpperCase()}
          </div>
        </div>
      ),
    },
    {
      title: '类型',
      dataIndex: 'scan_type',
      key: 'scan_type',
      render: (type) => (
        <Tag color={type === 'web' ? 'blue' : type === 'mobile' ? 'green' : 'orange'}>
          {type.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        const statusConfig = {
          pending: { color: 'default', text: '等待中', icon: <PlayCircleOutlined /> },
          running: { color: 'processing', text: '运行中', icon: <ReloadOutlined spin /> },
          completed: { color: 'success', text: '已完成', icon: <EyeOutlined /> },
          failed: { color: 'error', text: '失败', icon: <DeleteOutlined /> },
          cancelled: { color: 'warning', text: '已取消', icon: <StopOutlined /> },
        };
        const config = statusConfig[status] || statusConfig.pending;
        return (
          <Tag color={config.color} icon={config.icon}>
            {config.text}
          </Tag>
        );
      },
    },
    {
      title: '进度',
      dataIndex: 'progress',
      key: 'progress',
      render: (progress, record) => (
        <div>
          <Progress 
            percent={progress} 
            size="small" 
            status={progress === 100 ? 'success' : 'active'}
            style={{ width: '100px' }}
          />
          <div style={{ fontSize: '12px', color: '#666' }}>
            {record.started_at ? new Date(record.started_at).toLocaleString() : '未开始'}
          </div>
        </div>
      ),
    },
    {
      title: '发现',
      dataIndex: 'total_findings',
      key: 'total_findings',
      render: (total, record) => (
        <div>
          <div>总计: {total}</div>
          <div>
            <Tag color="red">严重: {record.critical_findings}</Tag>
            <Tag color="orange">高危: {record.high_findings}</Tag>
            <Tag color="yellow">中危: {record.medium_findings}</Tag>
            <Tag color="blue">低危: {record.low_findings}</Tag>
            <Tag color="default">提示: {record.info_findings}</Tag>
          </div>
        </div>
      ),
    },
    {
      title: '风险分数',
      dataIndex: 'risk_score',
      key: 'risk_score',
      render: (score, record) => {
        const riskLevel = record.risk_level || 'info';
        const color = riskLevel === 'critical' ? 'red' : 
                      riskLevel === 'high' ? 'orange' : 
                      riskLevel === 'medium' ? 'yellow' : 
                      riskLevel === 'low' ? 'blue' : 'default';
        return (
          <Tag color={color}>
            {score ? score.toFixed(1) : 'N/A'}
          </Tag>
        );
      },
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button 
            type="link" 
            icon={<EyeOutlined />}
            onClick={() => navigate(`/scans/${record.id}`)}
          >
            查看
          </Button>
          
          {record.status === 'pending' && (
            <Popconfirm
              title="确定要启动这个扫描吗？"
              onConfirm={() => handleScanAction(record.id, 'start')}
              okText="确定"
              cancelText="取消"
            >
              <Button type="link" icon={<PlayCircleOutlined />}>
                启动
              </Button>
            </Popconfirm>
          )}
          
          {record.status === 'running' && (
            <>
              <Popconfirm
                title="确定要暂停这个扫描吗？"
                onConfirm={() => handleScanAction(record.id, 'pause')}
                okText="确定"
                cancelText="取消"
              >
                <Button type="link" icon={<PauseCircleOutlined />}>
                  暂停
                </Button>
              </Popconfirm>
              
              <Popconfirm
                title="确定要取消这个扫描吗？"
                onConfirm={() => handleScanAction(record.id, 'cancel')}
                okText="确定"
                cancelText="取消"
              >
                <Button type="link" icon={<StopOutlined />} danger>
                  取消
                </Button>
              </Popconfirm>
            </>
          )}
          
          {record.status === 'completed' && (
            <Popconfirm
              title="确定要删除这个扫描吗？"
              onConfirm={() => handleScanAction(record.id, 'delete')}
              okText="确定"
              cancelText="取消"
            >
              <Button type="link" icon={<DeleteOutlined />} danger>
                删除
              </Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  useEffect(() => {
    fetchScans();
  }, [pagination.current, pagination.pageSize, filters]);

  const fetchScans = async () => {
    try {
      setLoading(true);
      const params = {
        page: pagination.current,
        limit: pagination.pageSize,
        ...filters
      };
      
      const response = await api.get('/scans', { params });
      setScans(response.data.data || response.data || []);
      setTotal(response.data.total || 0);
    } catch (error) {
      message.error('获取扫描列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleScanAction = async (scanId, action) => {
    try {
      setLoading(true);
      await api.post(`/scans/${scanId}/${action}`);
      message.success(`${action === 'start' ? '启动' : action === 'pause' ? '暂停' : action === 'cancel' ? '取消' : '删除'}成功`);
      fetchScans();
    } catch (error) {
      message.error(`${action === 'start' ? '启动' : action === 'pause' ? '暂停' : action === 'cancel' ? '取消' : '删除'}失败`);
    } finally {
      setLoading(false);
    }
  };

  const handleTableChange = (newPagination) => {
    setPagination(newPagination);
  };

  const handleSearch = (values) => {
    setFilters({
      ...filters,
      ...values
    });
    setPagination({
      ...pagination,
      current: 1
    });
  };

  const handleReset = () => {
    setFilters({
      status: null,
      scan_type: null,
      target_type: null,
      date_range: null
    });
    setPagination({
      ...pagination,
      current: 1
    });
  };

  const showCreateModal = () => {
    setCreateModalVisible(true);
  };

  const handleCreateScan = async (values) => {
    try {
      setLoading(true);
      await api.post('/scans', values);
      message.success('创建扫描成功');
      setCreateModalVisible(false);
      form.resetFields();
      fetchScans();
    } catch (error) {
      message.error('创建扫描失败');
    } finally {
      setLoading(false);
    }
  };

  const showDetailModal = (scan) => {
    setSelectedScan(scan);
    setDetailModalVisible(true);
  };

  return (
    <div>
      <div style={{ marginBottom: '20px' }}>
        <h1>扫描管理</h1>
      </div>

      <Card style={{ marginBottom: '20px' }}>
        <Row gutter={[16, 16]} align="middle">
          <Col>
            <Button 
              type="primary" 
              icon={<PlusOutlined />}
              onClick={showCreateModal}
            >
              创建扫描
            </Button>
          </Col>
          <Col>
            <Button 
              icon={<ReloadOutlined />}
              onClick={fetchScans}
              loading={loading}
            >
              刷新
            </Button>
          </Col>
          <Col>
            <Button 
              icon={<FilterOutlined />}
              onClick={() => {
                // 这里可以添加高级筛选功能
              }}
            >
              高级筛选
            </Button>
          </Col>
        </Row>

        <Row gutter={[16, 16]} style={{ marginTop: '16px' }}>
          <Col xs={24} sm={12} md={6}>
            <Form.Item name="status" label="状态">
              <Select allowClear placeholder="选择状态">
                <Option value="pending">等待中</Option>
                <Option value="running">运行中</Option>
                <Option value="completed">已完成</Option>
                <Option value="failed">失败</Option>
                <Option value="cancelled">已取消</Option>
              </Select>
            </Form.Item>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Form.Item name="scan_type" label="扫描类型">
              <Select allowClear placeholder="选择类型">
                <Option value="web">Web应用</Option>
                <Option value="mobile">移动应用</Option>
                <Option value="network">网络设备</Option>
              </Select>
            </Form.Item>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Form.Item name="target_type" label="目标类型">
              <Select allowClear placeholder="选择目标类型">
                <Option value="url">URL</Option>
                <Option value="ip">IP地址</Option>
                <Option value="domain">域名</Option>
              </Select>
            </Form.Item>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Form.Item name="date_range" label="日期范围">
              <RangePicker style={{ width: '100%' }} />
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={[16, 16]} style={{ marginTop: '16px' }}>
          <Col>
            <Button 
              type="primary" 
              icon={<SearchOutlined />}
              onClick={() => handleSearch(form.getFieldsValue())}
            >
              搜索
            </Button>
            <Button 
              style={{ marginLeft: '8px' }}
              onClick={handleReset}
            >
              重置
            </Button>
          </Col>
        </Row>
      </Card>

      <Card>
        <Table
          columns={columns}
          dataSource={scans}
          rowKey="id"
          loading={loading}
          pagination={pagination}
          onChange={handleTableChange}
        />
      </Card>

      <Modal
        title="创建扫描"
        visible={createModalVisible}
        onCancel={() => setCreateModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreateScan}
        >
          <Form.Item
            name="name"
            label="扫描名称"
            rules={[{ required: true, message: '请输入扫描名称' }]}
          >
            <Input placeholder="请输入扫描名称" />
          </Form.Item>

          <Form.Item
            name="scan_type"
            label="扫描类型"
            rules={[{ required: true, message: '请选择扫描类型' }]}
          >
            <Select placeholder="请选择扫描类型">
              <Option value="web">Web应用</Option>
              <Option value="mobile">移动应用</Option>
              <Option value="network">网络设备</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="target_type"
            label="目标类型"
            rules={[{ required: true, message: '请选择目标类型' }]}
          >
            <Select placeholder="请选择目标类型">
              <Option value="url">URL</Option>
              <Option value="ip">IP地址</Option>
              <Option value="domain">域名</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="target_url"
            label="目标URL"
            rules={[{ required: true, message: '请输入目标URL' }]}
          >
            <Input placeholder="https://example.com" />
          </Form.Item>

          <Form.Item
            name="target_ip"
            label="目标IP"
          >
            <Input placeholder="192.168.1.1" />
          </Form.Item>

          <Form.Item
            name="target_domain"
            label="目标域名"
          >
            <Input placeholder="example.com" />
          </Form.Item>

          <Form.Item
            name="scan_config"
            label="扫描配置"
          >
            <Input.TextArea 
              rows={4} 
              placeholder="JSON格式的扫描配置，例如：{\n  \"depth\": \"deep\",\n  \"include_subdomains\": true\n}" 
            />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                创建
              </Button>
              <Button onClick={() => setCreateModalVisible(false)}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="扫描详情"
        visible={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={800}
      >
        {selectedScan && (
          <div>
            <Descriptions bordered column={2}>
              <Descriptions.Item label="扫描名称">{selectedScan.name}</Descriptions.Item>
              <Descriptions.Item label="扫描类型">{selectedScan.scan_type}</Descriptions.Item>
              <Descriptions.Item label="目标URL">{selectedScan.target_url}</Descriptions.Item>
              <Descriptions.Item label="目标IP">{selectedScan.target_ip}</Descriptions.Item>
              <Descriptions.Item label="状态">{selectedScan.status}</Descriptions.Item>
              <Descriptions.Item label="进度">{selectedScan.progress}%</Descriptions.Item>
              <Descriptions.Item label="开始时间">
                {selectedScan.started_at ? new Date(selectedScan.started_at).toLocaleString() : '未开始'}
              </Descriptions.Item>
              <Descriptions.Item label="完成时间">
                {selectedScan.completed_at ? new Date(selectedScan.completed_at).toLocaleString() : '未完成'}
              </Descriptions.Item>
              <Descriptions.Item label="总发现">{selectedScan.total_findings}</Descriptions.Item>
              <Descriptions.Item label="风险分数">
                {selectedScan.risk_score ? selectedScan.risk_score.toFixed(1) : 'N/A'}
              </Descriptions.Item>
            </Descriptions>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default ScansPage;