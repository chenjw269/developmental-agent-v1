import { useState } from 'react'
import { createApplication } from '../api/applications'
import type { ApiError } from '../api/client'

export default function Apply() {
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [reason, setReason] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccess(null)
    setLoading(true)
    try {
      await createApplication({ username: username.trim(), email: email.trim(), reason: reason.trim() || undefined })
      setSuccess('申请已提交，请等待管理员审批。')
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
    </>
  )
}
