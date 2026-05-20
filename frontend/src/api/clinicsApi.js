import api from './axios'

export const getClinic = (id) => api.get(`/api/clinics/${id}/`)
export const updateClinic = (id, data) => api.patch(`/api/clinics/${id}/`, data)
export const getWebCallToken = (clinicId) => api.post(`/api/clinics/${clinicId}/web_call_token/`)
