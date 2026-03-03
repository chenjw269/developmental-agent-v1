import { useState, useEffect } from 'react'
import {
  listApplications,
  approveApplication,
  rejectApplication,
  deleteApplication,
} from '../api/applications'
import {
  listCredentials,
  updateQuota,
  updateBalance,
  setBalanceByTarget,
  disableCredential,
  enableCredential,
  deleteCredential,
} from '../api/credentials'
import type { Application, Credential } from '../types'
import type { ApiError } from '../api/client'

const ADMIN_KEY_STORAGE = 'gateway_demo_admin_key'

export default function Admin() {
  const [adminKey, setAdminKey] = useState(() => localStorage.getItem(ADMIN_KEY_STORAGE) || '')
  const [applications, setApplications] = useState<Application[]>([])
  const [credentials, setCredentials] = useState<Credential[]>([])
  const [loadingApps, setLoadingApps] = useState(false)
  const [loadingCreds, setLoadingCreds] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [quotaEditId, setQuotaEditId] = useState<number | null>(null)
  const [quotaValue, setQuotaValue] = useState('')
  const [balanceEditId, setBalanceEditId] = useState<number | null>(null)
  const [balanceValue, setBalanceValue] = useState('')
  const [setBalanceTarget, setSetBalanceTarget] = useState<'consumer_name' | 'username'>('consumer_name')
  const [setBalanceKey, setSetBalanceKey] = useState('')
  const [setBalanceAmount, setSetBalanceAmount] = useState('')
  const [setBalanceLoading, setSetBalanceLoading] = useState(false)

  const loadApplications = async () => {
    setLoadingApps(true)
    setError(null)
    try {
      const res = await listApplications({ limit: 50 }, adminKey || undefined)
      setApplications(res.items)
    } catch (e) {
      setError((e as ApiError).message || '加载申请列表失败')
    } finally {
      setLoadingApps(false)
    }
  }

  const loadCredentials = async () => {
    setLoadingCreds(true)
    setError(null)
    try {
      const res = await listCredentials({ limit: 50 }, adminKey || undefined)
      setCredentials(res.items)
    } catch (e) {
      setError((e as ApiError).message || '加载凭证列表失败')
    } finally {
      setLoadingCreds(false)
    }
  }

  useEffect(() => {
    loadApplications()
    loadCredentials()
  }, [])

  const saveAdminKey = () => {
    if (adminKey) localStorage.setItem(ADMIN_KEY_STORAGE, adminKey)
    else localStorage.removeItem(ADMIN_KEY_STORAGE)
    setSuccess('已保存')
    setTimeout(() => setSuccess(null), 2000)
    loadApplications()
    loadCredentials()
  }

  const handleApprove = async (id: number) => {
    setError(null)
    setSuccess(null)
    try {
      const res = await approveApplication(id, adminKey || undefined)
      setSuccess(`已通过，API Key: ${res.api_key}，初始 Token 余额: ${res.token_balance ?? 10}（请妥善保存）`)
      loadApplications()
      loadCredentials()
    } catch (e) {
      setError((e as ApiError).message || '审批失败')
    }
  }

  const handleReject = async (id: number) => {
    setError(null)
    setSuccess(null)
    try {
      await rejectApplication(id, adminKey || undefined)
      setSuccess('已拒绝')
      loadApplications()
    } catch (e) {
      setError((e as ApiError).message || '操作失败')
    }
  }

  const handleQuotaSubmit = async (credId: number) => {
    const n = parseInt(quotaValue, 10)
    if (isNaN(n) || n < 1 || n > 10000) {
      setError('请输入 1–10000 的整数')
      return
    }
    setError(null)
    setSuccess(null)
    try {
      await updateQuota(credId, n, adminKey || undefined)
      setSuccess('配额已更新')
      setQuotaEditId(null)
      loadCredentials()
    } catch (e) {
      setError((e as ApiError).message || '更新失败')
    }
  }

  const handleBalanceSubmit = async (credId: number) => {
    const n = parseInt(balanceValue, 10)
    if (isNaN(n) || n < 0) {
      setError('请输入不小于 0 的整数')
      return
    }
    setError(null)
    setSuccess(null)
    try {
      await updateBalance(credId, n, adminKey || undefined)
      setSuccess('Token 余额已更新')
      setBalanceEditId(null)
      loadCredentials()
    } catch (e) {
      setError((e as ApiError).message || '更新失败')
    }
  }

  const handleSetBalanceByTarget = async (e: React.FormEvent) => {
    e.preventDefault()
    const amount = parseInt(setBalanceAmount, 10)
    if (isNaN(amount) || amount < 0) {
      setError('Token 数量须为不小于 0 的整数')
      return
    }
    if (!setBalanceKey.trim()) {
      setError(setBalanceTarget === 'consumer_name' ? '请输入 Consumer 名称' : '请输入用户名')
      return
    }
    setError(null)
    setSuccess(null)
    setSetBalanceLoading(true)
    try {
      const res = await setBalanceByTarget(
        setBalanceTarget === 'consumer_name'
          ? { consumer_name: setBalanceKey.trim(), token_balance: amount }
          : { username: setBalanceKey.trim(), token_balance: amount },
        adminKey || undefined
      )
      setSuccess(res.message + (res.updated?.length ? `，已更新 ${res.updated.length} 条` : ''))
      setSetBalanceKey('')
      setSetBalanceAmount('')
      loadCredentials()
    } catch (e) {
      setError((e as ApiError).message || '设置失败')
    } finally {
      setSetBalanceLoading(false)
    }
  }

  const handleDisable = async (id: number) => {
    setError(null)
    setSuccess(null)
    try {
      await disableCredential(id, adminKey || undefined)
      setSuccess('已禁用')
      loadCredentials()
    } catch (e) {
      setError((e as ApiError).message || '操作失败')
    }
  }

  const handleEnable = async (id: number) => {
    setError(null)
    setSuccess(null)
    try {
      await enableCredential(id, adminKey || undefined)
      setSuccess('已启用')
      loadCredentials()
    } catch (e) {
      setError((e as ApiError).message || '操作失败')
    }
  }

  const handleDeleteCredential = async (id: number) => {
    if (!window.confirm('确定要永久删除该 API Key？删除后无法恢复。')) return
    setError(null)
    setSuccess(null)
    try {
      await deleteCredential(id, adminKey || undefined)
      setSuccess('已删除')
      loadCredentials()
    } catch (e) {
      setError((e as ApiError).message || '删除失败')
    }
  }

  const handleDeleteApplication = async (id: number) => {
    if (!window.confirm('确定要删除该申请记录？若已通过将同时删除对应 API Key。')) return
    setError(null)
    setSuccess(null)
    try {
      await deleteApplication(id, adminKey || undefined)
      setSuccess('已删除')
      loadApplications()
      loadCredentials()
    } catch (e) {
      setError((e as ApiError).message || '删除失败')
    }
  }

  return (
    <>
      <h1 className="page-title">管理后台</h1>

      <div className="card">
        <h3>管理员密钥</h3>
        <p style={{ margin: '0 0 0.75rem', fontSize: '0.875rem', color: '#64748b' }}>
          若后端配置了 ADMIN_API_KEY，请在此填写并保存，以便调用管理接口。
        </p>
        <div className="form-group" style={{ maxWidth: 320 }}>
          <input
            type="password"
            value={adminKey}
            onChange={(e) => setAdminKey(e.target.value)}
            placeholder="X-Admin-Key（选填）"
          />
        </div>
        <button type="button" className="btn btn-secondary" onClick={saveAdminKey}>
          保存并刷新
        </button>
        {success && <span style={{ marginLeft: '0.5rem', color: '#16a34a', fontSize: '0.875rem' }}>{success}</span>}
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {success && error === null && <div className="alert alert-success">{success}</div>}

      <div className="card">
        <h3>设置 Token 数量</h3>
        <p style={{ margin: '0 0 0.75rem', fontSize: '0.875rem', color: '#64748b' }}>
          按 API Key 对应的 Consumer 名称或按用户名，批量设置 token 数量。
        </p>
        <form onSubmit={handleSetBalanceByTarget} style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', alignItems: 'flex-end' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <input
              type="radio"
              name="setBalanceTarget"
              checked={setBalanceTarget === 'consumer_name'}
              onChange={() => setSetBalanceTarget('consumer_name')}
            />
            按 Consumer 名称
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <input
              type="radio"
              name="setBalanceTarget"
              checked={setBalanceTarget === 'username'}
              onChange={() => setSetBalanceTarget('username')}
            />
            按用户名
          </label>
          <input
            type="text"
            value={setBalanceKey}
            onChange={(e) => setSetBalanceKey(e.target.value)}
            placeholder={setBalanceTarget === 'consumer_name' ? '例如 consumer_1' : '例如 张三'}
            style={{ width: 160 }}
          />
          <input
            type="number"
            min={0}
            value={setBalanceAmount}
            onChange={(e) => setSetBalanceAmount(e.target.value)}
            placeholder="Token 数量"
            style={{ width: 100 }}
          />
          <button type="submit" className="btn btn-primary" disabled={setBalanceLoading}>
            {setBalanceLoading ? '设置中…' : '设置'}
          </button>
        </form>
      </div>

      <div className="card">
        <h3>申请列表</h3>
        <button type="button" className="btn btn-secondary" onClick={loadApplications} disabled={loadingApps}>
          {loadingApps ? '加载中…' : '刷新'}
        </button>
        {loadingApps && <span className="loading" style={{ marginLeft: '0.5rem' }}>加载中…</span>}
        <div className="table-wrap" style={{ marginTop: '1rem' }}>
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>用户名</th>
                <th>邮箱</th>
                <th>原因</th>
                <th>状态</th>
                <th>创建时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {applications.length === 0 && !loadingApps && (
                <tr><td colSpan={7} style={{ color: '#64748b' }}>暂无申请</td></tr>
              )}
              {applications.map((a) => (
                <tr key={a.id}>
                  <td>{a.id}</td>
                  <td>{a.user_username ?? '-'}</td>
                  <td>{a.user_email ?? '-'}</td>
                  <td>{(a.reason || '').slice(0, 40)}{(a.reason && a.reason.length > 40) ? '…' : ''}</td>
                  <td>
                    <span className={`badge badge-${a.status === 'pending' ? 'pending' : a.status === 'approved' ? 'approved' : 'rejected'}`}>
                      {a.status}
                    </span>
                  </td>
                  <td>{new Date(a.created_at).toLocaleString()}</td>
                  <td>
                    {a.status === 'pending' && (
                      <>
                        <button type="button" className="btn btn-success" onClick={() => handleApprove(a.id)}>通过</button>
                        <button type="button" className="btn btn-danger" onClick={() => handleReject(a.id)}>拒绝</button>
                      </>
                    )}
                    <button type="button" className="btn btn-secondary" style={{ marginLeft: 4 }} onClick={() => handleDeleteApplication(a.id)} title="删除该申请记录">删除</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="card">
        <h3>已发放 API Key</h3>
        <button type="button" className="btn btn-secondary" onClick={loadCredentials} disabled={loadingCreds}>
          {loadingCreds ? '加载中…' : '刷新'}
        </button>
        <div className="table-wrap" style={{ marginTop: '1rem' }}>
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Consumer</th>
                <th>Key（脱敏）</th>
                <th>配额/分钟</th>
                <th>Token 余额</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {credentials.length === 0 && !loadingCreds && (
                <tr><td colSpan={7} style={{ color: '#64748b' }}>暂无凭证</td></tr>
              )}
              {credentials.map((c) => (
                <tr key={c.id}>
                  <td>{c.id}</td>
                  <td>{c.consumer_name}</td>
                  <td><code>{c.api_key}</code></td>
                  <td>
                    {quotaEditId === c.id ? (
                      <>
                        <input
                          type="number"
                          min={1}
                          max={10000}
                          value={quotaValue}
                          onChange={(e) => setQuotaValue(e.target.value)}
                          style={{ width: 80 }}
                        />
                        <button type="button" className="btn btn-primary" onClick={() => handleQuotaSubmit(c.id)}>保存</button>
                        <button type="button" className="btn btn-secondary" onClick={() => setQuotaEditId(null)}>取消</button>
                      </>
                    ) : (
                      <>
                        {c.quota_per_minute}
                        <button type="button" className="btn btn-secondary" style={{ marginLeft: 8 }} onClick={() => { setQuotaEditId(c.id); setQuotaValue(String(c.quota_per_minute)) }}>修改</button>
                      </>
                    )}
                  </td>
                  <td>
                    {balanceEditId === c.id ? (
                      <>
                        <input
                          type="number"
                          min={0}
                          value={balanceValue}
                          onChange={(e) => setBalanceValue(e.target.value)}
                          style={{ width: 80 }}
                        />
                        <button type="button" className="btn btn-primary" onClick={() => handleBalanceSubmit(c.id)}>保存</button>
                        <button type="button" className="btn btn-secondary" onClick={() => setBalanceEditId(null)}>取消</button>
                      </>
                    ) : (
                      <>
                        {c.token_balance ?? 0}
                        <button type="button" className="btn btn-secondary" style={{ marginLeft: 8 }} onClick={() => { setBalanceEditId(c.id); setBalanceValue(String(c.token_balance ?? 0)) }}>修改</button>
                      </>
                    )}
                  </td>
                  <td>{c.is_active ? <span className="badge badge-approved">启用</span> : <span className="badge badge-rejected">禁用</span>}</td>
                  <td>
                    {c.is_active ? (
                      <button type="button" className="btn btn-danger" onClick={() => handleDisable(c.id)}>禁用</button>
                    ) : (
                      <button type="button" className="btn btn-success" onClick={() => handleEnable(c.id)}>启用</button>
                    )}
                    <button type="button" className="btn btn-secondary" style={{ marginLeft: 4 }} onClick={() => handleDeleteCredential(c.id)} title="永久删除该 Key">删除</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  )
}
