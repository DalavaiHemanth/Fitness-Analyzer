import axios from 'axios'

const api = axios.create({
  baseURL: '',  // Vite proxy handles /users, /pose, /workout, /analytics
  headers: { 'Content-Type': 'application/json' },
})

// Inject token on every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Auto-logout on 401
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

// ─── Auth ─────────────────────────────────────────────────────────
export const authAPI = {
  register: (data) => api.post('/users/register', data),
  login: (username, password) => {
    const params = new URLSearchParams()
    params.append('username', username)
    params.append('password', password)
    return api.post('/users/login', params, { 
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' } 
    })
  },
  getMe: () => api.get('/users/me'),
  updateMe: (data) => api.put('/users/me', data),
}

// ─── Pose ─────────────────────────────────────────────────────────
export const poseAPI = {
  classify: (file) => {
    const form = new FormData()
    form.append('file', file)
    return api.post('/pose/classify-pose', form, { headers: { 'Content-Type': 'multipart/form-data' } })
  },
  getHistory: (limit = 20) => api.get(`/pose/history?limit=${limit}`),
  getAccuracyTrend: (days = 30) => api.get(`/pose/accuracy-trend?days=${days}`),
}

// ─── Workout ──────────────────────────────────────────────────────
export const workoutAPI = {
  analyze: (text, save = true) => api.post(`/workout/analyze-workout?save=${save}`, { text }),
  getSessions: (limit = 30, type) =>
    api.get(`/workout/sessions?limit=${limit}${type ? `&workout_type=${type}` : ''}`),
  deleteSession: (id) => api.delete(`/workout/sessions/${id}`),
  logMood: (data) => api.post('/workout/mood', data),
  getMoodHistory: (limit = 30) => api.get(`/workout/mood/history?limit=${limit}`),
}

// ─── Analytics ────────────────────────────────────────────────────
export const analyticsAPI = {
  getProgress: () => api.get('/analytics/progress'),
  getFitnessScore: (days = 7) => api.get(`/analytics/fitness-score?days=${days}`),
  getPredict: () => api.get('/analytics/predict'),
  getMuscleHeatmap: (days = 30) => api.get(`/analytics/muscle-heatmap?days=${days}`),
  getCalorieTrend: (days = 30) => api.get(`/analytics/calorie-trend?days=${days}`),
}

export default api
