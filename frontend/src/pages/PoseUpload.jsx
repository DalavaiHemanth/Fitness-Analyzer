import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { poseAPI } from '../api/client'
import { useAuth } from '../context/AuthContext'
import toast from 'react-hot-toast'
import { Camera, Upload, CheckCircle, XCircle, Loader, ChevronRight } from 'lucide-react'

const POSE_COLORS = {
  squat: '#10b981', pushup: '#3b82f6', plank: '#8b5cf6',
  deadlift: '#ef4444', bicep_curl: '#f59e0b', shoulder_press: '#06b6d4',
  lunge: '#84cc16', jumping_jack: '#f97316', warrior_pose: '#ec4899',
  downward_dog: '#a78bfa', unknown: '#6b7280',
}

const POSE_EMOJIS = {
  squat: '🏋️', pushup: '💪', plank: '🧘', deadlift: '⚡', bicep_curl: '💪',
  shoulder_press: '🏋️‍♀️', lunge: '🦵', jumping_jack: '⭐', warrior_pose: '🧘‍♀️',
  downward_dog: '🐕', unknown: '❓',
}

export default function PoseUpload() {
  const { user } = useAuth()
  const [preview, setPreview] = useState(null)
  const [file, setFile] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [history, setHistory] = useState([])
  const [histLoading, setHistLoading] = useState(false)

  const onDrop = useCallback((accepted) => {
    const f = accepted[0]
    if (!f) return
    setFile(f)
    setPreview(URL.createObjectURL(f))
    setResult(null)
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop, accept: { 'image/*': ['.jpg', '.jpeg', '.png', '.webp'] }, maxFiles: 1,
  })

  const handleClassify = async () => {
    if (!file) return
    setLoading(true)
    try {
      const res = await poseAPI.classify(file)
      setResult(res.data)
      toast.success(`Pose detected: ${res.data.pose_label}! 🎯`)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Classification failed')
    } finally {
      setLoading(false)
    }
  }

  const loadHistory = async () => {
    setHistLoading(true)
    try {
      const res = await poseAPI.getHistory(10)
      setHistory(res.data)
    } catch { toast.error('Failed to load history') }
    finally { setHistLoading(false) }
  }

  const color = result ? (POSE_COLORS[result.pose_label] || '#10b981') : '#10b981'
  const conf = result ? Math.round(result.confidence * 100) : 0

  return (
    <div className="page">
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ marginBottom: '0.25rem' }}>
          <Camera size={28} style={{ verticalAlign: 'middle', color: 'var(--accent)', marginRight: 8 }} />
          Pose Detection
        </h1>
        <p style={{ color: 'var(--text-secondary)' }}>Upload a workout photo to classify your exercise pose using AI</p>
      </div>

      <div className="grid-2">
        {/* Upload Panel */}
        <div>
          <div
            {...getRootProps()}
            style={{
              border: `2px dashed ${isDragActive ? 'var(--accent)' : 'rgba(255,255,255,0.15)'}`,
              borderRadius: 16,
              padding: '2.5rem',
              textAlign: 'center',
              cursor: 'pointer',
              background: isDragActive ? 'rgba(16,185,129,0.06)' : 'rgba(255,255,255,0.02)',
              transition: 'all 0.2s',
              marginBottom: '1rem',
            }}
          >
            <input {...getInputProps()} />
            {preview ? (
              <img src={preview} alt="preview" style={{ maxHeight: 280, maxWidth: '100%', borderRadius: 10, objectFit: 'contain' }} />
            ) : (
              <>
                <Upload size={40} color="var(--text-muted)" style={{ marginBottom: '0.75rem' }} />
                <p style={{ fontWeight: 600, marginBottom: '0.25rem' }}>
                  {isDragActive ? 'Drop it here!' : 'Drag & drop or click to upload'}
                </p>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>JPG, PNG, WebP · Max 10MB</p>
              </>
            )}
          </div>

          {file && (
            <button
              className="btn btn-primary"
              onClick={handleClassify}
              disabled={loading}
              style={{ width: '100%', justifyContent: 'center', padding: '0.8rem' }}
            >
              {loading ? <><div className="spinner" style={{ width: 18, height: 18, borderWidth: 2 }} /> Analyzing...</>
                : <><Camera size={16} /> Classify Pose</>}
            </button>
          )}
        </div>

        {/* Result Panel */}
        <div>
          {result ? (
            <div className="card fade-up" style={{ borderColor: `${color}40`, boxShadow: `0 0 30px ${color}20` }}>
              <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
                <div style={{ fontSize: '4rem', marginBottom: '0.5rem' }}>{POSE_EMOJIS[result.pose_label] || '🏋️'}</div>
                <h2 style={{ textTransform: 'capitalize', color, marginBottom: '0.25rem' }}>
                  {result.pose_label.replace('_', ' ')}
                </h2>
                <span className="badge" style={{ background: `${color}20`, color }}>
                  {result.method === 'trained_model' ? '🤖 ML Model' : '📐 Angle Analysis'}
                </span>
              </div>

              {/* Confidence Ring */}
              <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1.5rem' }}>
                <div style={{ position: 'relative', width: 80, height: 80 }}>
                  <svg width={80} height={80} style={{ transform: 'rotate(-90deg)' }}>
                    <circle cx={40} cy={40} r={34} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth={7} />
                    <circle cx={40} cy={40} r={34} fill="none" stroke={color} strokeWidth={7}
                      strokeDasharray={`${conf / 100 * 2 * Math.PI * 34} ${2 * Math.PI * 34}`} strokeLinecap="round"
                      style={{ filter: `drop-shadow(0 0 6px ${color}80)`, transition: 'stroke-dasharray 1s ease' }} />
                  </svg>
                  <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                    <span style={{ fontSize: '1.2rem', fontWeight: 800, color, fontFamily: 'Space Grotesk' }}>{conf}%</span>
                  </div>
                </div>
              </div>
              <div style={{ textAlign: 'center', marginBottom: '1.5rem', color: 'var(--text-muted)', fontSize: '0.8rem' }}>Confidence</div>

              {/* Feedback */}
              <div style={{ padding: '1rem', background: 'rgba(255,255,255,0.04)', borderRadius: 10, border: '1px solid rgba(255,255,255,0.07)' }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                  💡 Coach Feedback
                </div>
                <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>{result.feedback}</p>
              </div>

              {/* Calories */}
              <div style={{ marginTop: '1rem', display: 'flex', justifyContent: 'center' }}>
                <div className="badge badge-orange">🔥 ~{result.estimated_calories_per_min} kcal/min</div>
              </div>
            </div>
          ) : (
            <div className="card" style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <div className="empty-state">
                <Camera size={48} />
                <h3 style={{ marginBottom: '0.5rem' }}>Results will appear here</h3>
                <p>Upload a photo of your workout pose to get AI analysis</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* History */}
      <div style={{ marginTop: '2rem' }}>
        <div className="section-header">
          <div className="section-title">
            <div className="section-icon"><Camera size={16} /></div>
            Recent Detections
          </div>
          <button className="btn btn-secondary" onClick={loadHistory} disabled={histLoading}>
            {histLoading ? 'Loading...' : 'Load History'}
          </button>
        </div>

        {history.length > 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {history.map((h) => {
              const c = POSE_COLORS[h.pose_label] || '#6b7280'
              return (
                <div key={h.id} className="card" style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '1rem 1.25rem' }}>
                  <span style={{ fontSize: '1.5rem' }}>{POSE_EMOJIS[h.pose_label] || '🏋️'}</span>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 600, textTransform: 'capitalize', color: c }}>{h.pose_label.replace('_', ' ')}</div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{new Date(h.created_at).toLocaleDateString()}</div>
                  </div>
                  <div className="badge" style={{ background: `${c}20`, color: c }}>{Math.round(h.confidence * 100)}%</div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
