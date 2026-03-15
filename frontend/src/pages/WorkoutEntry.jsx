import { useState, useEffect } from 'react'
import { workoutAPI } from '../api/client'
import toast from 'react-hot-toast'
import { FileText, Send, Trash2, Dumbbell, Clock, Flame, Activity } from 'lucide-react'

const INTENT_COLORS = { strength: '#10b981', cardio: '#3b82f6', flexibility: '#8b5cf6', recovery: '#f59e0b', unknown: '#6b7280' }
const INTENT_ICONS = { strength: '🏋️', cardio: '🏃', flexibility: '🧘', recovery: '😴', unknown: '❓' }
const SAMPLE_TEXTS = [
  'I did 3 sets of 10 pushups and 20 minutes of running',
  'Squatted 80kg for 4 sets of 5 reps today, really felt it in my quads',
  '45 minute jog around the park this morning',
  'Morning yoga session for 30 minutes focusing on hip flexibility',
  'Rest day, just some light walking and foam rolling',
]

export default function WorkoutEntry() {
  const [text, setText] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [sessions, setSessions] = useState([])
  const [sessLoading, setSessLoading] = useState(true)

  useEffect(() => { loadSessions() }, [])

  const loadSessions = async () => {
    setSessLoading(true)
    try {
      const res = await workoutAPI.getSessions(15)
      setSessions(res.data)
    } catch { /* ignore */ }
    finally { setSessLoading(false) }
  }

  const handleAnalyze = async () => {
    if (!text.trim()) { toast.error('Please enter a workout description'); return }
    setLoading(true)
    try {
      const res = await workoutAPI.analyze(text)
      setResult(res.data)
      toast.success('Workout analyzed & saved! 💪')
      loadSessions()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Analysis failed')
    } finally { setLoading(false) }
  }

  const handleDelete = async (id) => {
    try {
      await workoutAPI.deleteSession(id)
      setSessions((prev) => prev.filter((s) => s.id !== id))
      toast.success('Session deleted')
    } catch { toast.error('Delete failed') }
  }

  const color = result ? (INTENT_COLORS[result.intent] || '#10b981') : '#10b981'

  return (
    <div className="page">
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ marginBottom: '0.25rem' }}>
          <FileText size={28} style={{ verticalAlign: 'middle', color: 'var(--accent)', marginRight: 8 }} />
          Workout NLP Analyzer
        </h1>
        <p style={{ color: 'var(--text-secondary)' }}>Describe your workout in plain text — our AI extracts sets, reps, muscles and more</p>
      </div>

      <div className="grid-2">
        {/* Input Panel */}
        <div>
          <div className="card">
            <div className="form-group">
              <label className="label">Describe your workout</label>
              <textarea
                className="input"
                rows={5}
                placeholder="e.g. 'I did 4 sets of 8 bench press at 75kg, then 3 sets of 10 bicep curls'"
                value={text}
                onChange={(e) => setText(e.target.value)}
              />
            </div>

            {/* Sample prompts */}
            <div style={{ marginBottom: '1.25rem' }}>
              <div className="label" style={{ marginBottom: '0.5rem' }}>Try an example:</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                {SAMPLE_TEXTS.map((s, i) => (
                  <button key={i} onClick={() => setText(s)} className="btn btn-secondary" style={{ fontSize: '0.75rem', padding: '0.3rem 0.65rem' }}>
                    {s.slice(0, 30)}...
                  </button>
                ))}
              </div>
            </div>

            <button className="btn btn-primary" onClick={handleAnalyze} disabled={loading} style={{ width: '100%', justifyContent: 'center', padding: '0.8rem' }}>
              {loading ? <><div className="spinner" style={{ width: 18, height: 18, borderWidth: 2 }} /> Analyzing...</>
                : <><Send size={16} /> Analyze Workout</>}
            </button>
          </div>
        </div>

        {/* Result Panel */}
        <div>
          {result ? (
            <div className="card fade-up" style={{ borderColor: `${color}40` }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
                <div style={{ fontSize: '2rem' }}>{INTENT_ICONS[result.intent]}</div>
                <div>
                  <div style={{ fontWeight: 700, fontSize: '1.1rem', color, textTransform: 'capitalize' }}>{result.intent} Training</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Confidence: {Math.round(result.confidence * 100)}%</div>
                </div>
                <div style={{ marginLeft: 'auto' }}>
                  <div className="badge" style={{ background: `${color}15`, color }}>{result.exercise_name.replace('_', ' ')}</div>
                </div>
              </div>

              <div className="grid-2" style={{ marginBottom: '1.25rem', gap: '0.75rem' }}>
                {[
                  { icon: '🔁', label: 'Sets', val: result.sets || '-' },
                  { icon: '💪', label: 'Reps', val: result.reps || '-' },
                  { icon: '⏱', label: 'Duration', val: result.duration_minutes ? `${result.duration_minutes} min` : '-' },
                  { icon: '🔥', label: 'Est. Calories', val: result.calories_estimate ? `${result.calories_estimate} kcal` : '-' },
                ].map(({ icon, label, val }) => (
                  <div key={label} style={{ padding: '0.75rem', background: 'rgba(255,255,255,0.04)', borderRadius: 10, textAlign: 'center' }}>
                    <div style={{ fontSize: '1.25rem', marginBottom: '0.25rem' }}>{icon}</div>
                    <div style={{ fontWeight: 700, marginBottom: '0.15rem' }}>{val}</div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{label}</div>
                  </div>
                ))}
              </div>

              {result.target_muscles.length > 0 && (
                <div>
                  <div className="label" style={{ marginBottom: '0.5rem' }}>Target Muscles</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                    {result.target_muscles.map((m) => (
                      <span key={m} className="badge badge-green" style={{ textTransform: 'capitalize' }}>{m}</span>
                    ))}
                  </div>
                </div>
              )}

              {result.session_id && (
                <div style={{ marginTop: '1rem', padding: '0.6rem 0.85rem', background: 'rgba(16,185,129,0.1)', borderRadius: 8, fontSize: '0.8rem', color: 'var(--accent)' }}>
                  ✅ Saved to workout history (ID #{result.session_id})
                </div>
              )}
            </div>
          ) : (
            <div className="card" style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 280 }}>
              <div className="empty-state">
                <FileText size={40} />
                <h3 style={{ marginBottom: '0.5rem' }}>Analysis results</h3>
                <p>Type your workout and hit Analyze</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Session History */}
      <div style={{ marginTop: '2rem' }}>
        <div className="section-header">
          <div className="section-title">
            <div className="section-icon"><Activity size={16} /></div>
            Workout History
          </div>
        </div>

        {sessLoading ? (
          <div className="loading-center"><div className="spinner" /></div>
        ) : sessions.length === 0 ? (
          <div className="card"><div className="empty-state"><Dumbbell size={36} /><p>No sessions yet. Analyze a workout to get started!</p></div></div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {sessions.map((s) => {
              const c = INTENT_COLORS[s.workout_type] || '#6b7280'
              return (
                <div key={s.id} className="card" style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '0.9rem 1.25rem' }}>
                  <span style={{ fontSize: '1.3rem' }}>{INTENT_ICONS[s.workout_type] || '💪'}</span>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 600, textTransform: 'capitalize', marginBottom: '0.2rem' }}>
                      <span style={{ color: c }}>{s.exercise_name || s.workout_type}</span>
                      {s.sets > 0 && <span style={{ color: 'var(--text-muted)', fontWeight: 400, fontSize: '0.85rem' }}> · {s.sets}×{s.reps}</span>}
                    </div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'flex', gap: '0.75rem' }}>
                      {s.duration_minutes > 0 && <span>⏱ {s.duration_minutes} min</span>}
                      {s.calories_burned > 0 && <span>🔥 {Math.round(s.calories_burned)} kcal</span>}
                      {s.target_muscles && <span>💪 {s.target_muscles.split(',').slice(0, 2).join(', ')}</span>}
                      <span>{new Date(s.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                  <button className="btn btn-danger" style={{ padding: '0.3rem 0.6rem', fontSize: '0.8rem' }} onClick={() => handleDelete(s.id)}>
                    <Trash2 size={13} />
                  </button>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
