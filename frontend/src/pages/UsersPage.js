import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Table, 
  Button, 
  Space, 
  Tag, 
  message, 
  Tooltip,
  Typography,
  Row,
  Col,
  Statistic,
  Alert,
  Modal,
  Form,
  Input,
  Select,
  Switch,
  Avatar,
  Divider,
  Badge
} from 'antd';
import { 
  UserOutlined, 
  TeamOutlined, 
  EditOutlined, 
  DeleteOutlined, 
  EyeOutlined,
  PlusOutlined,
  ReloadOutlined,
  LockOutlined,
  UnlockOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  CrownOutlined,
  SafetyOutlined,
  ClockCircleOutlined
} from '@ant-design/icons';
import { userAPI } from '../services/api';

const { Title, Text } = Typography;
const { Option } = Select;

const UsersPage = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [modalType, setModalType] = useState('create'); // 'create' or 'edit'
  const [form] = Form.useForm();
  const [selectedUser, setSelectedUser] = useState(null);

  // 统计数据
  const [stats, setStats] = useState({
    total: 0,
    active: 0,
    inactive: 0,
    admin: 0,
    analyst: 0,
    viewer: 0
  });

  useEffect(() => {
    fetchUsers();
    fetchStats();
  }, []);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const response = await userAPI.list();
      setUsers(response.data.users || []);
    } catch (error) {
      message.error('获取用户列表失败');
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await userAPI.list({ limit: 0 });
      const userList = response.data.users || [];
      
      setStats({
        total: userList.length,
        active: userList.filter(u => u.status === 'active').length,
        inactive: userList.filter(u => u.status === 'inactive').length,
        admin: userList.filter(u => u.role === 'admin').length,
        analyst: userList.filter(u => u.role === 'analyst').length,
        viewer: userList.filter(u => u.role === 'viewer').length
      });
    } catch (error) {
      console.error('获取统计信息失败:', error);
    }
  };

  const handleCreate = () => {
    setModalType('create');
    setModalVisible(true);
    form.resetFields();
  };

  const handleEdit = (user) => {
    setModalType('edit');
    setSelectedUser(user);
    setModalVisible(true);
    form.setFieldsValue(user);
  };

  const handleDelete = async (user) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除用户 "${user.username}" 吗？`,
      onOk: async () => {
        try {
          await userAPI.delete(user.id);
          message.success('删除成功');
          fetchUsers();
          fetchStats();
        } catch (error) {
          message.error('删除失败');
        }
      }
    });
  };

  const handleToggleStatus = async (user) => {
    try {
      const newStatus = user.status === 'active' ? 'inactive' : 'active';
      await userAPI.update(user.id, { status: newStatus });
      message.success(`用户状态已更新为${newStatus === 'active' ? '激活' : '禁用'}`);
      fetchUsers();
      fetchStats();
    } catch (error) {
      message.error('状态更新失败');
    }
  };

  const handleSubmit = async (values) => {
    try {
      if (modalType === 'create') {
        await userAPI.create(values);
        message.success('创建成功');
      } else {
        await userAPI.update(selectedUser.id, values);
        message.success('更新成功');
      }
      setModalVisible(false);
      fetchUsers();
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
      'locked': 'red'
    };
    return statusMap[status] || 'default';
  };

  const getRoleColor = (role) => {
    const roleMap = {
      'super_user': 'red',
      'admin': 'orange',
      'analyst': 'blue',
      'auditor': 'purple',
      'viewer': 'green'
    };
    return roleMap[role] || 'default';
  };

  const getRoleIcon = (role) => {
    const roleMap = {
      'super_user': <CrownOutlined style={{ color: '#ff4d4f' }} />,
      'admin': <SafetyOutlined style={{ color: '#fa8c16' }} />,
      'analyst': <UserOutlined style={{ color: '#1890ff' }} />,
      'auditor': <EyeOutlined style={{ color: '#722ed1' }} />,
      'viewer': <UserOutlined style={{ color: '#52c41a' }} />
    };
    return roleMap[role] || <UserOutlined />;
  };

  const columns = [
    {
      title: '用户',
      key: 'user',
      render: (_, record) => (
        <Space>
          <Avatar src={record.avatar_url} icon={<UserOutlined />} />
          <div>
            <Text strong>{record.full_name || record.username}</Text>
            <br />
            <Text type="secondary" style={{ fontSize: '12px' }}>
              {record.email}
            </Text>
          </div>
        </Space>
      )
    },
    {
      title: '角色',
      dataIndex: 'role',
      key: 'role',
      render: (role) => (
        <Tag color={getRoleColor(role)} icon={getRoleIcon(role)}>
          {role.toUpperCase()}
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
      title: '部门',
      dataIndex: 'department',
      key: 'department',
      render: (dept) => dept || '-'
    },
    {
      title: '职位',
      dataIndex: 'position',
      key: 'position',
      render: (pos) => pos || '-'
    },
    {
      title: '最后登录',
      dataIndex: 'last_login',
      key: 'last_login',
      render: (date) => {
        if (!date) return '-';
        const now = new Date();
        const login = new Date(date);
        const diff = now - login;
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));
        
        if (days === 0) {
          return '今天';
        } else if (days === 1) {
          return '昨天';
        } else if (days < 7) {
          return `${days}天前`;
        } else {
          return date.toLocaleDateString();
        }
      }
    },
    {
      title: '双因素认证',
      dataIndex: 'two_factor_enabled',
      key: 'two_factor_enabled',
      render: (enabled) => (
        <Badge status={enabled ? 'success' : 'default'} text={enabled ? '已启用' : '未启用'} />
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
          <Button 
            type="link" 
            size="small"
            icon={record.status === 'active' ? <LockOutlined /> : <UnlockOutlined />}
            onClick={() => handleToggleStatus(record)}
          >
            {record.status === 'active' ? '禁用' : '启用'}
          </Button>
        </Space>
      )
    }
  ];

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <Title level={2}>用户管理</Title>
        <Text type="secondary">管理系统用户和权限</Text>
      </div>

      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="用户总数"
              value={stats.total}
              prefix={<TeamOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="活跃用户"
              value={stats.active}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="管理员"
              value={stats.admin}
              prefix={<SafetyOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="分析师"
              value={stats.analyst}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 操作区域 */}
      <Card 
        title="用户列表" 
        extra={
          <Space>
            <Button 
              type="primary" 
              icon={<PlusOutlined />}
              onClick={handleCreate}
            >
              添加用户
            </Button>
            <Button 
              icon={<ReloadOutlined />}
              onClick={fetchUsers}
              loading={loading}
            >
              刷新
            </Button>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={users}
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

      {/* 用户模态框 */}
      <Modal
        title={modalType === 'create' ? '添加用户' : '编辑用户'}
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
            name="username"
            label="用户名"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input placeholder="请输入用户名" />
          </Form.Item>

          <Form.Item
            name="email"
            label="邮箱"
            rules={[{ required: true, message: '请输入邮箱' }]}
          >
            <Input type="email" placeholder="请输入邮箱" />
          </Form.Item>

          <Form.Item
            name="full_name"
            label="姓名"
            rules={[{ required: true, message: '请输入姓名' }]}
          >
            <Input placeholder="请输入姓名" />
          </Form.Item>

          {modalType === 'create' && (
            <Form.Item
              name="password"
              label="密码"
              rules={[{ required: true, message: '请输入密码' }]}
            >
              <Input.Password placeholder="请输入密码" />
            </Form.Item>
          )}

          <Form.Item
            name="role"
            label="角色"
            rules={[{ required: true, message: '请选择角色' }]}
          >
            <Select placeholder="请选择角色">
              <Option value="super_user">超级管理员</Option>
              <Option value="admin">管理员</Option>
              <Option value="analyst">分析师</Option>
              <Option value="auditor">审计员</Option>
              <Option value="viewer">查看者</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="department"
            label="部门"
          >
            <Input placeholder="请输入部门" />
          </Form.Item>

          <Form.Item
            name="position"
            label="职位"
          >
            <Input placeholder="请输入职位" />
          </Form.Item>

          <Form.Item
            name="phone"
            label="电话"
          >
            <Input placeholder="请输入电话" />
          </Form.Item>

          <Form.Item
            name="status"
            label="状态"
            initialValue="active"
          >
            <Select>
              <Option value="active">激活</Option>
              <Option value="inactive">禁用</Option>
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

export default UsersPage;