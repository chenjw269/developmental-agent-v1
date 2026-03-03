import { useState } from 'react'
import { postAgentChat } from '../api/agent'
import type { AgentChatResponse } from '../types'

export default function TestCall() {
  const [apiKey, setApiKey] = useState('')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<AgentChatResponse | null>(null)

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setResult(null)
    if (!apiKey.trim()) {
      setError('请输入 API Key')
      return
    }
    setLoading(true)
    try {
      const res = await postAgentChat(apiKey.trim(), { message: message.trim() || '（无内容）' })
      setResult(res)
    } catch (err: unknown) {
      const o = err as { message?: string; status?: number }
      if (o.status === 429) {
        setError('请求过于频繁，已超过每分钟配额限制，请稍后再试。')
      } else if (o.status === 402) {
        setError(o.message || 'Token 余额已耗尽，请联系管理员充值。')
      } else if (o.status === 401) {
        setError('API Key 无效或已失效，请检查后重试。')
      } else {
        setError(o.message || '请求失败')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <h1 className="page-title">测试调用智能体</h1>
      <div className="card">
        <p style={{ margin: '0 0 1rem', fontSize: '0.875rem', color: '#64748b' }}>
          请求将经 <strong>APISIX 网关</strong> 转发到智能体服务。请使用已审批通过的 API Key；超限时网关返回 429，页面会提示配额限制。
        </p>
        <form onSubmit={handleSend}>
          <div className="form-group">
            <label>API Key</label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="从管理后台审批通过后获得"
            />
          </div>
          <div className="form-group">
            <label>消息内容</label>
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="例如：你好"
            />
          </div>
          {error && <div className="alert alert-error">{error}</div>}
          {result && (
            <div className="alert alert-success">
              <div><strong>回复：</strong>{result.reply}</div>
              <div style={{ marginTop: 4, fontSize: '0.875rem' }}>
                consumer: {result.consumer}, stored: {String(result.stored)}
                {result.remaining_tokens != null && (
                  <span style={{ marginLeft: 8 }}>剩余 Token: <strong>{result.remaining_tokens}</strong></span>
                )}
              </div>
            </div>
          )}
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? '发送中…' : '发送'}
          </button>
        </form>
      </div>
    </>
  )
}
