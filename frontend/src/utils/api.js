/**
 * API Client
 * Provides centralized API communication with automatic token management
 */

import axios from 'axios'

// Create axios instance with base configuration
const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add authentication token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle authentication errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

/**
 * Authentication API endpoints
 */
export const authAPI = {
  /**
   * Login user
   * @param {string} email - User email
   * @param {string} password - User password
   * @returns {Promise} API response with token and user data
   */
  login: async (email, password) => {
    const response = await api.post('/auth/login', { email, password })
    return response.data
  },

  /**
   * Register new user
   * @param {string} email - User email
   * @param {string} password - User password
   * @param {string} fullName - User full name
   * @returns {Promise} API response with token and user data
   */
  register: async (email, password, fullName) => {
    const response = await api.post('/auth/signup', { 
      email, 
      password, 
      full_name: fullName 
    })
    return response.data
  },

  /**
   * Get current user information
   * @returns {Promise} User data
   */
  getCurrentUser: async () => {
    const response = await api.get('/auth/me')
    return response.data
  },
}

/**
 * Notes API endpoints
 */
export const notesAPI = {
  /**
   * Get all notes for current user
   * @param {Object} params - Query parameters (skip, limit, search)
   * @returns {Promise} Notes list response
   */
  getNotes: async (params = {}) => {
    const response = await api.get('/notes/', { params })
    return response.data
  },

  /**
   * Get single note by ID
   * @param {string} noteId - Note ID
   * @returns {Promise} Note data
   */
  getNote: async (noteId) => {
    const response = await api.get(`/notes/${noteId}`)
    return response.data
  },

  /**
   * Create new note
   * @param {Object} noteData - Note data (title, content, tags, is_favorite)
   * @returns {Promise} Created note data
   */
  createNote: async (noteData) => {
    const response = await api.post('/notes/', noteData)
    return response.data
  },

  /**
   * Update existing note
   * @param {string} noteId - Note ID
   * @param {Object} noteData - Updated note data
   * @returns {Promise} Updated note data
   */
  updateNote: async (noteId, noteData) => {
    const response = await api.put(`/notes/${noteId}`, noteData)
    return response.data
  },

  /**
   * Delete note
   * @param {string} noteId - Note ID
   * @returns {Promise} Deletion confirmation
   */
  deleteNote: async (noteId) => {
    const response = await api.delete(`/notes/${noteId}`)
    return response.data
  },

  /**
   * Search notes
   * @param {string} query - Search query
   * @param {Object} params - Additional parameters (skip, limit)
   * @returns {Promise} Search results
   */
  searchNotes: async (query, params = {}) => {
    const response = await api.get('/notes/', { 
      params: { ...params, search: query } 
    })
    return response.data
  },
}

/**
 * Helper function to handle API errors
 * @param {Error} error - Axios error object
 * @returns {string} User-friendly error message
 */
export const getErrorMessage = (error) => {
  if (error.response?.data?.detail) {
    return error.response.data.detail
  }
  if (error.response?.data?.message) {
    return error.response.data.message
  }
  if (error.message) {
    return error.message
  }
  return 'An unexpected error occurred. Please try again.'
}

export default api
