import api from './axios'

export const getAppointments = (params) => api.get('/api/appointments/', { params })
export const getAppointment = (id) => api.get(`/api/appointments/${id}/`)
export const getTodayAppointments = () => api.get('/api/appointments/today/')
export const updateAppointment = (id, data) => api.patch(`/api/appointments/${id}/`, data)
export const resendWhatsApp = (id) => api.post(`/api/appointments/${id}/resend_whatsapp/`)
