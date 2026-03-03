import { Routes, Route, Link } from 'react-router-dom'
import Demo from './pages/Demo'
import Home from './pages/Home'
import Apply from './pages/Apply'
import Admin from './pages/Admin'
import TestCall from './pages/TestCall'

function App() {
  return (
    <div className="app-shell">
      <nav style={{ marginBottom: '1.5rem', padding: '0.5rem 0', borderBottom: '1px solid #e2e8f0' }}>
        <Link to="/" style={{ marginRight: '1rem', fontWeight: 600 }}>首页</Link>
        <Link to="/apply" style={{ marginRight: '1rem' }}>申请 API Key</Link>
        <Link to="/admin" style={{ marginRight: '1rem' }}>管理后台</Link>
        <Link to="/test">测试调用</Link>
      </nav>
      <Routes>
        <Route path="/" element={<Demo />} />
        <Route path="/apply" element={<Apply />} />
        <Route path="/admin" element={<Admin />} />
        <Route path="/test" element={<TestCall />} />
        <Route path="/about" element={<Home />} />
      </Routes>
    </div>
  )
}

export default App
