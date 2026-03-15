import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import toast from 'react-hot-toast'
import { Zap } from 'lucide-react'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!username || !password) { toast.error('Please fill all fields'); return }
    setLoading(true)
    try {
      await login(username, password)
      toast.success('Welcome back! 💪')
      navigate('/')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Login failed')
    } finally { setLoading(false) }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '2rem' }}>
      <div style={{ width: '100%', maxWidth: 420 }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: 64, height: 64, borderRadius: 20, background: 'linear-gradient(135deg, #10b981, #059669)', boxShadow: '0 0 30px rgba(16,185,129,0.5)', marginBottom: '1rem' }}>
            <Zap size={28} color="white" fill="white" />
          </div>
          <h1 style={{ marginBottom: '0.25rem' }}>Fit<span style={{ color: '#10b981' }}>AI</span></h1>
          <p style={{ color: 'var(--text-secondary)' }}>Multi-Modal Fitness Analyzer</p>
        </div>

        <div className="card" style={{ border: '1px solid rgba(16,185,129,0.2)' }}>
          <h2 style={{ marginBottom: '1.5rem', textAlign: 'center' }}>Sign In</h2>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="label">Username or Email</label>
              <input className="input" placeholder="username or email" value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" />
            </div>
            <div className="form-group">
              <label className="label">Password</label>
              <input className="input" type="password" placeholder="••••••••" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" />
            </div>
            <button type="submit" className="btn btn-primary" disabled={loading} style={{ width: '100%', justifyContent: 'center', padding: '0.85rem', marginTop: '0.5rem' }}>
              {loading ? 'Signing in...' : '🚀 Sign In'}
            </button>
          </form>
          <div style={{ textAlign: 'center', marginTop: '1.25rem', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            Don't have an account? <Link to="/register" style={{ color: 'var(--accent)', fontWeight: 600 }}>Register</Link>
          </div>
        </div>
      </div>
    </div>
  )
}
