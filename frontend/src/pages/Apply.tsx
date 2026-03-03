import { useState } from 'react'
import { createApplication, getApplicationStatus } from '../api/applications'
import type { ApiError } from '../api/client'
import type { ApplicationStatusResponse } from '../types'

export default function Apply() {
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [reason, setReason] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [lastApplicationId, setLastApplicationId] = useState<number | null>(null)

  const [queryId, setQueryId] = useState('')
  const [queryEmail, setQueryEmail] = useState('')
  const [queryLoading, setQueryLoading] = useState(false)
  const [queryError, setQueryError] = useState<string | null>(null)
  const [statusResult, setStatusResult] = useState<ApplicationStatusResponse | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccess(null)
    setLoading(true)
    try {
      const app = await createApplication({
        username: username.trim(),
        email: email.trim(),
        reason: reason.trim() || undefined,
      })
      setLastApplicationId(app.id)
      setSuccess(`申请已提交。您的申请编号：${app.id}，请保存。审批通过后可凭申请编号与邮箱在下方查询并获取 API Key。`)
      setUsername('')
      setEmail('')
      setReason('')
    } catch (err) {
      const apiErr = err as ApiError
      setError(apiErr.message || apiErr.detail || '提交失败')
    } finally {
      setLoading(false)
    }
  }

  const handleQuery = async (e: React.FormEvent) => {
    e.preventDefault()
    const id = parseInt(queryId, 10)
    if (isNaN(id) || id < 1) {
      setQueryError('请输入有效的申请编号')
      return
    }
    if (!queryEmail.trim()) {
      setQueryError('请输入申请时填写的邮箱')
      return
    }
    setQueryError(null)
    setStatusResult(null)
    setQueryLoading(true)
    try {
      const res = await getApplicationStatus(id, queryEmail.trim())
      setStatusResult(res)
    } catch (err) {
      const apiErr = err as ApiError
      setQueryError(apiErr.message || apiErr.detail || '查询失败')
    } finally {
      setQueryLoading(false)
    }
  }

  return (
    <>
      <h1 className="page-title">申请 API Key</h1>
      <div className="card">
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>用户名</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="用于标识申请人"
              required
            />
          </div>
          <div className="form-group">
            <label>邮箱</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="your@example.com"
              required
            />
          </div>
          <div className="form-group">
            <label>申请原因（选填）</label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="简要说明用途"
            />
          </div>
          {error && <div className="alert alert-error">{error}</div>}
          {success && <div className="alert alert-success">{success}</div>}
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? '提交中…' : '提交申请'}
          </button>
        </form>
      </div>

      <div className="card">
        <h3>查询审批结果与 API Key</h3>
        <p style={{ margin: '0 0 1rem', fontSize: '0.875rem', color: '#64748b' }}>
          审批通过后，请使用申请编号与申请时填写的邮箱查询，即可获取您的 API Key。
        </p>
        <form onSubmit={handleQuery} style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', alignItems: 'flex-end' }}>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label>申请编号</label>
            <input
              type="number"
              min={1}
              value={queryId}
              onChange={(e) => setQueryId(e.target.value)}
              placeholder={lastApplicationId ? String(lastApplicationId) : '例如 1'}
            />
          </div>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label>邮箱</label>
            <input
              type="email"
              value={queryEmail}
              onChange={(e) => setQueryEmail(e.target.value)}
              placeholder="申请时填写的邮箱"
            />
          </div>
          <button type="submit" className="btn btn-primary" disabled={queryLoading}>
            {queryLoading ? '查询中…' : '查询'}
          </button>
        </form>
        {queryError && <div className="alert alert-error" style={{ marginTop: '1rem' }}>{queryError}</div>}
        {statusResult && (
          <div className="alert alert-success" style={{ marginTop: '1rem' }}>
            <div><strong>状态：</strong>
              <span className={`badge badge-${statusResult.status === 'approved' ? 'approved' : statusResult.status === 'rejected' ? 'rejected' : 'pending'}`}>
                {statusResult.status === 'approved' ? '已通过' : statusResult.status === 'rejected' ? '已拒绝' : '待审批'}
              </span>
            </div>
            {statusResult.status === 'approved' && statusResult.api_key && (
              <>
                <div style={{ marginTop: 8 }}>
                  <strong>您的 API Key：</strong>
                  <code style={{ display: 'block', marginTop: 4, padding: 8, background: '#f1f5f9', borderRadius: 4, wordBreak: 'break-all' }}>
                    {statusResult.api_key}
                  </code>
                  <p style={{ margin: '4px 0 0', fontSize: '0.875rem', color: '#64748b' }}>
                    请妥善保存，切勿泄露。可在「测试调用」页使用此 Key 调用智能体。
                  </p>
                </div>
                {statusResult.token_balance != null && (
                  <div style={{ marginTop: 4, fontSize: '0.875rem' }}>当前 Token 余额：{statusResult.token_balance}</div>
                )}
              </>
            )}
          </div>
        )}
      </div>
    </>
  )
}
