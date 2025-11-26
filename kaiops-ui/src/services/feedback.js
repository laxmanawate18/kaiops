import axios from 'axios'
import { API_BASE_URL } from '../constants/apiConstants'

class FeedbackService {
  constructor() {
    this.axios = axios.create({
      baseURL: `${API_BASE_URL}/feedback`,
      headers: { 'Content-Type': 'application/json' }
    })

    this.axios.interceptors.request.use(cfg => {
      const token = localStorage.getItem('auth_token')
      if (token) cfg.headers.Authorization = `Bearer ${token}`
      return cfg
    })

    this.axios.interceptors.response.use(
      response => response,
      error => {
        if (error.response?.status === 401) {
          localStorage.removeItem('auth_token')
          localStorage.removeItem('user_data')
          window.location.href = '/login'
        }
        return Promise.reject(error)
      }
    )
  }

  async sendFeedback(data) {
    const resp = await this.axios.post('/', data)
    return resp.data
  }

  async getMyFeedback() {
    const resp = await this.axios.get('/my')
    return resp.data
  }

  async getMyStats() {
    const resp = await this.axios.get('/my/stats')
    return resp.data
  }

  async getPending() {
    const resp = await this.axios.get('/pending')
    return resp.data
  }

  async review(id, review) {
    const resp = await this.axios.post(`/${id}/review`, review)
    return resp.data
  }

  async stats() {
    const resp = await this.axios.get('/stats')
    return resp.data
  }

  async getDatasets(type) {
    const resp = await this.axios.get('/datasets/entries', { 
      params: type ? { dataset_type: type } : {} 
    })
    return resp.data
  }

  async datasetStats() {
    const resp = await this.axios.get('/datasets/stats')
    return resp.data
  }

  async getCategories() {
    const resp = await this.axios.get('/categories')
    return resp.data
  }
}

export const feedbackService = new FeedbackService()
