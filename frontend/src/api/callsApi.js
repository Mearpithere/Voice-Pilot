import api from './axios'

export const getCalls = (params) => api.get('/api/calls/', { params })
export const getCall = (id) => api.get(`/api/calls/${id}/`)
export const getCallRecording = (id) => api.get(`/api/calls/${id}/recording/`)
export const getCallStats = (period = 'today') => api.get('/api/calls/stats/', { params: { period } })
export const getCallQueue = () => api.get('/api/calls/queue/')
