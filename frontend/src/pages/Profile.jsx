import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { authAPI } from '../api/client'
import toast from 'react-hot-toast'
import { User, Save, Target, Scale, Ruler } from 'lucide-react'

const GOALS = [
  { value: 'weight_loss', label: '🔥 Weight Loss', desc: 'Burn fat, get lean' },
  { value: 'muscle_gain', label: '💪 Muscle Gain', desc: 'Build strength & size' },
  { value: 'endurance', label: '🏃 Endurance', desc: 'Improve stamina & cardio' },
  { value: 'flexibility', label: '🧘 Flexibility', desc: 'Mobility & flexibility' },
  { value: 'general', label: '⭐ General Fitness', desc: 'All-round healthy lifestyle' },
]

export default function Profile() {
  const { user, refreshUser } = useAuth()
  const [form, setForm] = useState({
    full_name: user?.full_name || '',
    age: user?.age || '',
    weight_kg: user?.weight_kg || '',
    height_cm: user?.height_cm || '',
    fitness_goal: user?.fitness_goal || 'general',
  })
  const [saving, setSaving] = useState(false)

  const set = (k, v) => setForm((prev) => ({ ...prev, [k]: v }))

  const handleSave = async () => {
    setSaving(true)
    try {
      await authAPI.updateMe({
        full_name: form.full_name,
        age: Number(form.age) || 0,
        weight_kg: Number(form.weight_kg) || 0,
        height_cm: Number(form.height_cm) || 0,
        fitness_goal: form.fitness_goal,
      })
      await refreshUser()
      toast.success('Profile updated! ✅')
    } catch { toast.error('Failed to save profile') }
    finally { setSaving(false) }
  }

  const bmi = form.weight_kg && form.height_cm
    ? (form.weight_kg / ((form.height_cm / 100) ** 2)).toFixed(1) : null

  const bmiCategory = bmi
    ? bmi < 18.5 ? { label: 'Underweight', color: '#3b82f6' }
      : bmi < 25 ? { label: 'Normal', color: '#10b981' }
        : bmi < 30 ? { label: 'Overweight', color: '#f59e0b' }
          : { label: 'Obese', color: '#ef4444' }
    : null

  return (
    <div className="page">
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ marginBottom: '0.25rem' }}>
          <User size={28} style={{ verticalAlign: 'middle', color: 'var(--accent)', marginRight: 8 }} />
          Profile & Goals
        </h1>
        <p style={{ color: 'var(--text-secondary)' }}>Manage your personal info and fitness goals</p>
      </div>

      <div className="grid-2">
        {/* Profile Form */}
        <div className="card">
          {/* Avatar */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem', marginBottom: '2rem' }}>
            <div style={{
              width: 72, height: 72, borderRadius: '50%',
              background: 'linear-gradient(135deg, #10b981, #059669)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '1.75rem', fontWeight: 700, color: 'white',
              fontFamily: "'Space Grotesk', sans-serif",
              boxShadow: '0 0 20px rgba(16,185,129,0.4)',
            }}>
              {(user?.username || 'U')[0].toUpperCase()}
            </div>
            <div>
              <div style={{ fontWeight: 700, fontSize: '1.25rem' }}>{user?.username}</div>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>{user?.email}</div>
              <div style={{ marginTop: '0.25rem' }}>
                <span className="badge badge-green">{user?.fitness_goal || 'general'}</span>
              </div>
            </div>
          </div>

          <div className="divider" />

          <div className="form-group">
            <label className="label">Full Name</label>
            <input className="input" value={form.full_name} onChange={(e) => set('full_name', e.target.value)} placeholder="Your full name" />
          </div>

          <div className="grid-2" style={{ gap: '0.75rem' }}>
            <div className="form-group">
              <label className="label">Age</label>
              <input className="input" type="number" value={form.age} onChange={(e) => set('age', e.target.value)} placeholder="25" />
            </div>
            <div className="form-group">
              <label className="label"><Scale size={12} style={{ verticalAlign: 'middle', marginRight: 4 }} />Weight (kg)</label>
              <input className="input" type="number" step="0.1" value={form.weight_kg} onChange={(e) => set('weight_kg', e.target.value)} placeholder="70" />
            </div>
          </div>

          <div className="form-group">
            <label className="label"><Ruler size={12} style={{ verticalAlign: 'middle', marginRight: 4 }} />Height (cm)</label>
            <input className="input" type="number" value={form.height_cm} onChange={(e) => set('height_cm', e.target.value)} placeholder="175" />
          </div>

          {bmi && (
            <div style={{ padding: '0.75rem 1rem', background: `${bmiCategory.color}15`, border: `1px solid ${bmiCategory.color}30`, borderRadius: 10, marginBottom: '1.25rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>BMI</span>
              <span style={{ fontWeight: 700, color: bmiCategory.color }}>{bmi} — {bmiCategory.label}</span>
            </div>
          )}

          <button className="btn btn-primary" onClick={handleSave} disabled={saving} style={{ width: '100%', justifyContent: 'center', padding: '0.8rem' }}>
            {saving ? 'Saving...' : <><Save size={16} /> Save Profile</>}
          </button>
        </div>

        {/* Goals Card */}
        <div className="card">
          <div className="section-title" style={{ marginBottom: '1.5rem' }}>
            <div className="section-icon"><Target size={16} /></div>
            Fitness Goal
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {GOALS.map((g) => {
              const active = form.fitness_goal === g.value
              return (
                <button
                  key={g.value}
                  onClick={() => set('fitness_goal', g.value)}
                  style={{
                    padding: '1rem 1.25rem',
                    borderRadius: 12,
                    border: active ? '2px solid var(--accent)' : '1px solid rgba(255,255,255,0.08)',
                    background: active ? 'rgba(16,185,129,0.12)' : 'rgba(255,255,255,0.03)',
                    textAlign: 'left', cursor: 'pointer',
                    transition: 'all 0.2s',
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 600, marginBottom: '0.15rem', color: active ? 'var(--accent)' : 'var(--text-primary)' }}>
                      {g.label}
                    </div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{g.desc}</div>
                  </div>
                  {active && <div style={{ width: 20, height: 20, borderRadius: '50%', background: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <span style={{ color: 'white', fontSize: '0.75rem' }}>✓</span>
                  </div>}
                </button>
              )
            })}
          </div>

          {/* Account Info */}
          <div className="divider" />
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
            <span>📅 Joined: {user?.created_at ? new Date(user.created_at).toLocaleDateString() : '-'}</span>
            <span>📧 Email: {user?.email}</span>
            <span>👤 Username: {user?.username}</span>
          </div>
        </div>
      </div>
    </div>
  )
}
