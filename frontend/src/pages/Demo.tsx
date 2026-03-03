import Apply from './Apply'
import TestCall from './TestCall'

export default function Demo() {
  return (
    <>
      <h1 className="page-title">智能体 API 网关演示</h1>
      <p style={{ margin: '0 0 1.5rem', color: '#64748b', fontSize: '0.9375rem' }}>
        申请 API Key → 管理员审批 → 使用 Key 与智能体聊天。请求经 Apache APISIX 网关鉴权与限流。
      </p>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem' }}>
        <section>
          <Apply />
        </section>
        <section>
          <TestCall />
        </section>
      </div>
    </>
  )
}
