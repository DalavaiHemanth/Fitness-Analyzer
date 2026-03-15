import { useState, useEffect } from 'react'
import { analyticsAPI } from '../api/client'
import { useAuth } from '../context/AuthContext'
import {
  BarChart, Bar, LineChart, Line, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts'
import { Activity, Flame, Clock, Target, TrendingUp, Zap, Award } from 'lucide-react'
import toast from 'react-hot-toast'

const CHART_TOOLTIP = {
  contentStyle: { background: 'rgba(17,24,39,0.95)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10, color: '#f9fafb' },
  labelStyle: { color: '#10b981', fontWeight: 600 },
}

function StatCard({ icon: Icon, value, label, color = '#10b981', suffix = '' }) {
  return (
    <div className="stat-card fade-up">
      <div className="stat-icon" style={{ background: `${color}20` }}>
        <Icon size={22} color={color} />
      </div>
      <div>
        <div className="stat-value" style={{ color }}>{value}{suffix}</div>
        <div className="stat-label">{label}</div>
      </div>
    </div>
  )
}

function GradeRing({ grade, score }) {
  const colors = { 'A+': '#10b981', A: '#10b981', B: '#3b82f6', C: '#f59e0b', D: '#ef4444', F: '#ef4444' }
  const color = colors[grade] || '#10b981'
  const r = 42, cx = 50, cy = 50, circ = 2 * Math.PI * r
  const dash = (score / 100) * circ

  return (
    <div style={{ textAlign: 'center' }}>
      <svg width={100} height={100} style={{ transform: 'rotate(-90deg)' }}>
        <circle cx={cx} cy={cy} r={r} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth={8} />
        <circle cx={cx} cy={cy} r={r} fill="none" stroke={color} strokeWidth={8}
          strokeDasharray={`${dash} ${circ}`} strokeLinecap="round"
          style={{ transition: 'stroke-dasharray 1s ease', filter: `drop-shadow(0 0 8px ${color}80)` }} />
      </svg>
      <div style={{ marginTop: -10, position: 'relative' }}>
        <div style={{ fontSize: '2rem', fontWeight: 800, color, fontFamily: "'Space Grotesk', sans-serif" }}>{grade}</div>
        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>{score.toFixed(0)}/100</div>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const { user } = useAuth()
  const [progress, setProgress] = useState(null)
  const [score, setScore] = useState(null)
  const [prediction, setPrediction] = useState(null)
  const [calories, setCalories] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      analyticsAPI.getProgress(),
      analyticsAPI.getFitnessScore(7),
      analyticsAPI.getPredict(),
      analyticsAPI.getCalorieTrend(30),
    ]).then(([prog, sc, pred, cal]) => {
      setProgress(prog.data)
      setScore(sc.data)
      setPrediction(pred.data)
      setCalories(cal.data)
    }).catch(() => toast.error('Failed to load dashboard data'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="loading-center" style={{ minHeight: '80vh' }}>
      <div className="spinner" />
      <span style={{ color: 'var(--text-secondary)' }}>Loading your stats...</span>
    </div>
  )

  const trendColor = prediction?.trend === 'improving' ? '#10b981' : prediction?.trend === 'declining' ? '#ef4444' : '#3b82f6'

  return (
    <div className="page">
      {/* Header */}
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ marginBottom: '0.25rem' }}>
          Welcome back, <span style={{ color: 'var(--accent)' }}>{user?.username}</span> 👋
        </h1>
        <p style={{ color: 'var(--text-secondary)' }}>Here's your fitness snapshot today</p>
      </div>

      {/* Stats Row */}
      <div className="grid-4" style={{ marginBottom: '1.5rem' }}>
        <StatCard icon={Activity} value={progress?.total_sessions ?? 0} label="Sessions (30d)" color="#10b981" />
        <StatCard icon={Clock} value={Math.round(progress?.total_duration_minutes ?? 0)} label="Total Minutes" color="#3b82f6" suffix=" min" />
        <StatCard icon={Flame} value={Math.round(progress?.total_calories_burned ?? 0)} label="Calories Burned" color="#f59e0b" suffix=" kcal" />
        <StatCard icon={Target} value={`${(progress?.avg_pose_accuracy ?? 0).toFixed(0)}%`} label="Avg Pose Accuracy" color="#8b5cf6" />
      </div>

      {/* Score + Prediction Row */}
      <div className="grid-2" style={{ marginBottom: '1.5rem' }}>
        {/* Fitness Score Card */}
        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
          {score && <GradeRing grade={score.grade} score={score.score} />}
          <div style={{ flex: 1 }}>
            <h3 style={{ marginBottom: '0.5rem' }}>Fitness Score</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1rem' }}>{score?.message}</p>
            {[
              { label: 'Frequency', val: score?.frequency_score ?? 0, color: '#10b981' },
              { label: 'Accuracy', val: score?.accuracy_score ?? 0, color: '#3b82f6' },
              { label: 'Duration', val: score?.duration_score ?? 0, color: '#8b5cf6' },
            ].map(({ label, val, color }) => (
              <div key={label} style={{ marginBottom: '0.6rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{label}</span>
                  <span style={{ fontSize: '0.8rem', fontWeight: 600, color }}>{val.toFixed(0)}%</span>
                </div>
                <div className="progress-bar">
                  <div className="progress-fill" style={{ width: `${val}%`, background: color }} />
                </div>
              </div>
            ))}
            <div style={{ marginTop: '0.5rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              🔥 {progress?.current_streak ?? 0}-day streak
            </div>
          </div>
        </div>

        {/* Prediction Card */}
        <div className="card">
          <div className="section-title" style={{ marginBottom: '1.25rem' }}>
            <div className="section-icon"><TrendingUp size={16} /></div>
            Next Week Forecast
          </div>
          <div style={{ display: 'flex', gap: '1.5rem', marginBottom: '1.25rem' }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '2.5rem', fontWeight: 800, color: trendColor, fontFamily: "'Space Grotesk', sans-serif" }}>
                {prediction?.next_week_sessions ?? 0}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Sessions</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '2.5rem', fontWeight: 800, color: '#f59e0b', fontFamily: "'Space Grotesk', sans-serif" }}>
                {prediction?.next_week_calories ?? 0}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Calories</div>
            </div>
          </div>
          <div style={{ padding: '0.75rem 1rem', borderRadius: 10, background: `${trendColor}15`, border: `1px solid ${trendColor}30`, marginBottom: '1rem' }}>
            <span style={{ textTransform: 'uppercase', fontWeight: 700, fontSize: '0.75rem', color: trendColor, letterSpacing: '0.05em' }}>
              {prediction?.trend}
            </span>
            <p style={{ margin: '0.25rem 0 0', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{prediction?.message}</p>
          </div>

          {/* Weekly chart mini */}
          {progress?.weekly_sessions?.length > 0 && (
            <ResponsiveContainer width="100%" height={100}>
              <BarChart data={progress.weekly_sessions} barSize={14}>
                <Bar dataKey="sessions" fill="#10b981" radius={[4, 4, 0, 0]} />
                <XAxis dataKey="label" tick={{ fill: '#6b7280', fontSize: 10 }} />
                <Tooltip {...CHART_TOOLTIP} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Calorie Trend Chart */}
      {calories.length > 0 && (
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <div className="section-title" style={{ marginBottom: '1.25rem' }}>
            <div className="section-icon" style={{ background: 'rgba(245,158,11,0.2)' }}><Flame size={16} color="#f59e0b" /></div>
            30-Day Calorie Burn
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={calories}>
              <defs>
                <linearGradient id="calGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="date" tick={{ fill: '#6b7280', fontSize: 11 }} />
              <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} />
              <Tooltip {...CHART_TOOLTIP} />
              <Area type="monotone" dataKey="calories" stroke="#f59e0b" fill="url(#calGrad)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Mood Trend + Top Exercises */}
      <div className="grid-2">
        {progress?.mood_trend?.length > 0 && (
          <div className="card">
            <div className="section-title" style={{ marginBottom: '1.25rem' }}>
              <div className="section-icon" style={{ background: 'rgba(139,92,246,0.2)' }}><Zap size={16} color="#8b5cf6" /></div>
              Mood & Energy Trend
            </div>
            <ResponsiveContainer width="100%" height={180}>
              <LineChart data={progress.mood_trend}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="date" tick={{ fill: '#6b7280', fontSize: 11 }} />
                <YAxis domain={[0, 10]} tick={{ fill: '#6b7280', fontSize: 11 }} />
                <Tooltip {...CHART_TOOLTIP} />
                <Legend wrapperStyle={{ color: '#9ca3af', fontSize: 12 }} />
                <Line type="monotone" dataKey="mood" stroke="#8b5cf6" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="energy" stroke="#10b981" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="stress" stroke="#ef4444" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {progress?.top_exercises?.length > 0 && (
          <div className="card">
            <div className="section-title" style={{ marginBottom: '1.25rem' }}>
              <div className="section-icon" style={{ background: 'rgba(245,158,11,0.2)' }}><Award size={16} color="#f59e0b" /></div>
              Top Exercises
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {progress.top_exercises.map((ex, i) => (
                <div key={ex.exercise} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <div style={{ width: 28, height: 28, borderRadius: 8, background: `hsl(${i * 50}, 70%, 50%)20`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 700, color: `hsl(${i * 50}, 70%, 60%)` }}>
                    #{i + 1}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 600, fontSize: '0.9rem', textTransform: 'capitalize' }}>{ex.exercise}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{ex.count} sessions · {Math.round(ex.total_calories)} kcal</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {(!progress?.mood_trend?.length && !progress?.top_exercises?.length) && (
          <div className="card" style={{ gridColumn: '1/-1' }}>
            <div className="empty-state">
              <Activity size={48} />
              <h3 style={{ marginBottom: '0.5rem' }}>No data yet</h3>
              <p>Start by uploading a pose or logging a workout to see your dashboard come alive!</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
