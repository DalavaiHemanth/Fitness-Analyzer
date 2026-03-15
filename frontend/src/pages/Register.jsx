import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { authAPI } from '../api/client'
import toast from 'react-hot-toast'
import { Zap } from 'lucide-react'

const GOALS = ['general', 'weight_loss', 'muscle_gain', 'endurance', 'flexibility']

export default function Register() {
  const [form, setForm] = useState({ email: '', username: '', password: '', full_name: '', fitness_goal: 'general' })
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const set = (k, v) => setForm((p) => ({ ...p, [k]: v }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.email || !form.username || !form.password) { toast.error('Please fill required fields'); return }
    setLoading(true)
    try {
      await authAPI.register(form)
      await login(form.username, form.password)
      toast.success('Account created! Welcome to FitAI 🎉')
      navigate('/')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Registration failed')
    } finally { setLoading(false) }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '2rem' }}>
      <div style={{ width: '100%', maxWidth: 460 }}>
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: 56, height: 56, borderRadius: 18, background: 'linear-gradient(135deg, #10b981, #059669)', boxShadow: '0 0 30px rgba(16,185,129,0.5)', marginBottom: '0.75rem' }}>
            <Zap size={24} color="white" fill="white" />
          </div>
          <h1 style={{ marginBottom: '0.2rem' }}>Join Fit<span style={{ color: '#10b981' }}>AI</span></h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Start your AI-powered fitness journey</p>
        </div>

        <div className="card" style={{ border: '1px solid rgba(16,185,129,0.2)' }}>
          <form onSubmit={handleSubmit}>
            <div className="grid-2" style={{ gap: '0.75rem' }}>
              <div className="form-group">
                <label className="label">Email *</label>
                <input className="input" type="email" placeholder="you@email.com" value={form.email} onChange={(e) => set('email', e.target.value)} />
              </div>
              <div className="form-group">
                <label className="label">Username *</label>
                <input className="input" placeholder="fituser123" value={form.username} onChange={(e) => set('username', e.target.value)} />
              </div>
            </div>
            <div className="form-group">
              <label className="label">Full Name</label>
              <input className="input" placeholder="John Doe" value={form.full_name} onChange={(e) => set('full_name', e.target.value)} />
            </div>
            <div className="form-group">
              <label className="label">Password *</label>
              <input className="input" type="password" placeholder="••••••••" value={form.password} onChange={(e) => set('password', e.target.value)} />
            </div>
            <div className="form-group">
              <label className="label">Fitness Goal</label>
              <select className="input" value={form.fitness_goal} onChange={(e) => set('fitness_goal', e.target.value)}
                style={{ cursor: 'pointer', appearance: 'none' }}>
                {GOALS.map((g) => <option key={g} value={g}>{g.replace('_', ' ').replace(/^\w/, c => c.toUpperCase())}</option>)}
              </select>
            </div>
            <button type="submit" className="btn btn-primary" disabled={loading} style={{ width: '100%', justifyContent: 'center', padding: '0.85rem' }}>
              {loading ? 'Creating account...' : '✨ Create Account'}
            </button>
          </form>
          <div style={{ textAlign: 'center', marginTop: '1.25rem', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            Already have an account? <Link to="/login" style={{ color: 'var(--accent)', fontWeight: 600 }}>Sign In</Link>
          </div>
        </div>
      </div>
    </div>
  )
}
