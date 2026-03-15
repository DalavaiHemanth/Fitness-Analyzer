import { useState, useEffect } from 'react'
import { workoutAPI } from '../api/client'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import toast from 'react-hot-toast'
import { Smile, Zap, AlertTriangle } from 'lucide-react'

const CHART_TOOLTIP = {
  contentStyle: { background: 'rgba(17,24,39,0.95)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10, color: '#f9fafb' },
  labelStyle: { color: '#10b981', fontWeight: 600 },
}

function EmojiSlider({ value, onChange, label, icon, low, high, color }) {
  return (
    <div style={{ marginBottom: '1.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          {icon}
          <span className="label" style={{ margin: 0 }}>{label}</span>
        </div>
        <div style={{ fontSize: '1.75rem', fontWeight: 800, color, fontFamily: "'Space Grotesk', sans-serif" }}>{value}</div>
      </div>
      <input type="range" min={1} max={10} value={value} onChange={(e) => onChange(Number(e.target.value))}
        style={{ '--thumb-color': color }} />
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
        <span>{low}</span><span>{high}</span>
      </div>
    </div>
  )
}

const MOOD_EMOJIS = ['😢', '😞', '😐', '🙂', '😊', '😄', '😁', '🌟', '⭐', '🏆']
const ENERGY_EMOJIS = ['🪫', '😴', '🥱', '😑', '🙂', '💪', '⚡', '🔥', '💥', '🚀']

export default function MoodTracker() {
  const [mood, setMood] = useState(5)
  const [energy, setEnergy] = useState(5)
  const [stress, setStress] = useState(5)
  const [sleep, setSleep] = useState(7)
  const [notes, setNotes] = useState('')
  const [loading, setLoading] = useState(false)
  const [history, setHistory] = useState([])
  const [chartData, setChartData] = useState([])

  useEffect(() => { loadHistory() }, [])

  const loadHistory = async () => {
    try {
      const res = await workoutAPI.getMoodHistory(14)
      setHistory(res.data)
      // Build chart data (daily averages, last 14 entries in reverse)
      const reversed = [...res.data].reverse()
      setChartData(reversed.map((m) => ({
        date: new Date(m.created_at).toLocaleDateString('en', { month: 'short', day: 'numeric' }),
        mood: m.mood_level,
        energy: m.energy_level,
        stress: m.stress_level,
        sleep: m.sleep_hours,
      })))
    } catch { /* ignore */ }
  }

  const handleLog = async () => {
    setLoading(true)
    try {
      await workoutAPI.logMood({ mood_level: mood, energy_level: energy, stress_level: stress, sleep_hours: sleep, notes })
      toast.success('Mood logged! 😊')
      setNotes('')
      loadHistory()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to log mood')
    } finally { setLoading(false) }
  }

  const avgMood = history.length ? (history.reduce((s, h) => s + h.mood_level, 0) / history.length).toFixed(1) : '-'
  const avgEnergy = history.length ? (history.reduce((s, h) => s + h.energy_level, 0) / history.length).toFixed(1) : '-'
  const avgStress = history.length ? (history.reduce((s, h) => s + h.stress_level, 0) / history.length).toFixed(1) : '-'

  return (
    <div className="page">
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ marginBottom: '0.25rem' }}>
          <Smile size={28} style={{ verticalAlign: 'middle', color: 'var(--accent)', marginRight: 8 }} />
          Mood Tracker
        </h1>
        <p style={{ color: 'var(--text-secondary)' }}>Track your mental state to correlate with workout performance</p>
      </div>

      {/* Summary cards */}
      <div className="grid-3" style={{ marginBottom: '1.5rem' }}>
        <div className="stat-card">
          <div className="stat-icon" style={{ background: 'rgba(139,92,246,0.2)' }}><Smile size={22} color="#8b5cf6" /></div>
          <div>
            <div className="stat-value" style={{ color: '#8b5cf6' }}>{MOOD_EMOJIS[Math.round(avgMood) - 1] || '—'} {avgMood}</div>
            <div className="stat-label">Avg Mood (14d)</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon" style={{ background: 'rgba(16,185,129,0.2)' }}><Zap size={22} color="#10b981" /></div>
          <div>
            <div className="stat-value" style={{ color: '#10b981' }}>{ENERGY_EMOJIS[Math.round(avgEnergy) - 1] || '—'} {avgEnergy}</div>
            <div className="stat-label">Avg Energy (14d)</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon" style={{ background: 'rgba(239,68,68,0.2)' }}><AlertTriangle size={22} color="#ef4444" /></div>
          <div>
            <div className="stat-value" style={{ color: '#ef4444' }}>{avgStress}</div>
            <div className="stat-label">Avg Stress (14d)</div>
          </div>
        </div>
      </div>

      <div className="grid-2">
        {/* Logger */}
        <div className="card">
          <h3 style={{ marginBottom: '1.5rem' }}>Log Today's State</h3>

          {/* Mood emoji visual */}
          <div style={{ textAlign: 'center', marginBottom: '0.5rem', fontSize: '3.5rem' }}>
            {MOOD_EMOJIS[mood - 1]}
          </div>

          <EmojiSlider value={mood} onChange={setMood} label="Mood" icon="😊"
            low="Very Low" high="Excellent" color="#8b5cf6" />
          <EmojiSlider value={energy} onChange={setEnergy} label="Energy" icon="⚡"
            low="Drained" high="Energized" color="#10b981" />
          <EmojiSlider value={stress} onChange={setStress} label="Stress" icon="😤"
            low="Relaxed" high="Overwhelmed" color="#ef4444" />

          <div className="form-group">
            <label className="label">Sleep Hours</label>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <input type="range" min={0} max={12} step={0.5} value={sleep} onChange={(e) => setSleep(Number(e.target.value))} />
              <span style={{ fontWeight: 700, color: 'var(--accent)', minWidth: '3.5rem' }}>😴 {sleep}h</span>
            </div>
          </div>

          <div className="form-group">
            <label className="label">Notes (optional)</label>
            <textarea className="input" placeholder="How are you feeling? Any observations..." value={notes} onChange={(e) => setNotes(e.target.value)} rows={2} />
          </div>

          <button className="btn btn-primary" onClick={handleLog} disabled={loading} style={{ width: '100%', justifyContent: 'center', padding: '0.8rem' }}>
            {loading ? 'Saving...' : '📝 Log Mood'}
          </button>
        </div>

        {/* Chart */}
        <div>
          {chartData.length > 0 ? (
            <div className="card">
              <h3 style={{ marginBottom: '1.25rem' }}>14-Day Trend</h3>
              <ResponsiveContainer width="100%" height={280}>
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="moodGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="energyGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="stressGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="date" tick={{ fill: '#6b7280', fontSize: 11 }} />
                  <YAxis domain={[0, 10]} tick={{ fill: '#6b7280', fontSize: 11 }} />
                  <Tooltip {...CHART_TOOLTIP} />
                  <Legend wrapperStyle={{ color: '#9ca3af', fontSize: 12 }} />
                  <Area type="monotone" dataKey="mood" stroke="#8b5cf6" fill="url(#moodGrad)" strokeWidth={2} />
                  <Area type="monotone" dataKey="energy" stroke="#10b981" fill="url(#energyGrad)" strokeWidth={2} />
                  <Area type="monotone" dataKey="stress" stroke="#ef4444" fill="url(#stressGrad)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
              <div style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem', maxHeight: 200, overflowY: 'auto' }}>
                {history.slice(0, 5).map((h) => (
                  <div key={h.id} style={{ display: 'flex', gap: '0.75rem', fontSize: '0.8rem', color: 'var(--text-secondary)', padding: '0.5rem 0', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                    <span>{new Date(h.created_at).toLocaleDateString()}</span>
                    <span>😊 {h.mood_level}</span>
                    <span>⚡ {h.energy_level}</span>
                    <span>😤 {h.stress_level}</span>
                    <span>😴 {h.sleep_hours}h</span>
                    {h.notes && <span style={{ color: 'var(--text-muted)' }}>· {h.notes}</span>}
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="card" style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 300 }}>
              <div className="empty-state">
                <Smile size={40} />
                <h3>No mood data yet</h3>
                <p>Log your first mood entry to start tracking!</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
