import { Link } from 'react-router-dom'

export default function Home() {
  return (
    <>
      <h1 className="page-title">智能体 API 网关演示平台</h1>
      <div className="card">
        <p style={{ margin: 0 }}>
          本平台演示「用户申请 API Key → 管理员审批 → 用户带 Key 访问智能体 → 管理员调整配额」的完整闭环。
          所有对智能体的访问均经 <strong>Apache APISIX</strong> 网关，由网关完成 API Key 鉴权与每分钟配额限制。
        </p>
      </div>
      <div className="home-links">
        <Link to="/apply" className="home-link-card">
          <h3>申请 API Key</h3>
          <p>填写用户名、邮箱与申请原因，提交后等待管理员审批。</p>
        </Link>
        <Link to="/admin" className="home-link-card">
          <h3>管理后台</h3>
          <p>查看申请列表、审批通过/拒绝、管理已发放 Key、修改配额与启用/禁用。</p>
        </Link>
        <Link to="/test" className="home-link-card">
          <h3>测试调用</h3>
          <p>输入 API Key 与消息，经网关调用智能体接口，查看返回与超限提示。</p>
        </Link>
      </div>
    </>
  )
}
