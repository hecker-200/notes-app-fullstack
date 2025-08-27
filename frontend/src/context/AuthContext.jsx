/**
 * Authentication Context
 * Provides authentication state and methods throughout the app
 */

import { createContext, useContext, useState, useEffect } from 'react'
import { authAPI } from '../utils/api'

const AuthContext = createContext({})

/**
 * Authentication Provider Component
 * Manages user authentication state and provides auth methods
 */
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  /**
   * Initialize auth state on app load
   * Checks for existing token and validates it
   */
  useEffect(() => {
    initializeAuth()
  }, [])

  const initializeAuth = async () => {
    try {
      const token = localStorage.getItem('token')
      if (!token) {
        setLoading(false)
        return
      }

      // Validate token by fetching user data
      const userData = await authAPI.getCurrentUser()
      setUser(userData)
    } catch (error) {
      // Token is invalid, remove it
      localStorage.removeItem('token')
      console.error('Token validation failed:', error)
    } finally {
      setLoading(false)
    }
  }

  /**
   * Login user with email and password
   * @param {string} email - User email
   * @param {string} password - User password
   * @returns {Promise} Login result
   */
  const login = async (email, password) => {
    try {
      const response = await authAPI.login(email, password)
      
      // Store token in localStorage
      localStorage.setItem('token', response.access_token)
      
      // Set user data
      setUser(response.user)
      
      return { success: true }
    } catch (error) {
      console.error('Login failed:', error)
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Login failed. Please try again.' 
      }
    }
  }

  /**
   * Register new user
   * @param {string} email - User email
   * @param {string} password - User password
   * @param {string} fullName - User full name (optional)
   * @returns {Promise} Registration result
   */
  const register = async (email, password, fullName = '') => {
    try {
      const response = await authAPI.register(email, password, fullName)
      
      // Store token in localStorage
      localStorage.setItem('token', response.access_token)
      
      // Set user data
      setUser(response.user)
      
      return { success: true }
    } catch (error) {
      console.error('Registration failed:', error)
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Registration failed. Please try again.' 
      }
    }
  }

  /**
   * Logout user
   * Clears token and user data
   */
  const logout = () => {
    localStorage.removeItem('token')
    setUser(null)
  }

  /**
   * Get current authentication token
   * @returns {string|null} JWT token or null if not authenticated
   */
  const getToken = () => {
    return localStorage.getItem('token')
  }

  /**
   * Check if user is authenticated
   * @returns {boolean} True if user is authenticated
   */
  const isAuthenticated = () => {
    return !!user && !!getToken()
  }

  const value = {
    user,
    loading,
    login,
    register,
    logout,
    getToken,
    isAuthenticated,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

/**
 * Hook to use authentication context
 * @returns {Object} Authentication context value
 */
export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
