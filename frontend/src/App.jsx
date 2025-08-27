/**
 * Main App Component
 * Handles routing and provides authentication context to the entire app
 */

import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import CreateNote from './pages/CreateNote'
import EditNote from './pages/EditNote'
import Header from './components/Header'
import Loading from './components/Loading'

/**
 * Protected Route wrapper component
 * Redirects to login if user is not authenticated
 */
function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()

  if (loading) {
    return <Loading />
  }

  return user ? children : <Navigate to="/login" />
}

/**
 * Public Route wrapper component
 * Redirects to dashboard if user is already authenticated
 */
function PublicRoute({ children }) {
  const { user, loading } = useAuth()

  if (loading) {
    return <Loading />
  }

  return user ? <Navigate to="/dashboard" /> : children
}

/**
 * App layout component
 * Includes header and main content area
 */
function AppLayout({ children }) {
  const { user } = useAuth()

  return (
    <div className="min-h-screen bg-gray-50">
      {user && <Header />}
      <main className={user ? 'pt-16' : ''}>
        {children}
      </main>
    </div>
  )
}

/**
 * Main App component
 * Sets up routing and authentication context
 */
function App() {
  return (
    <AuthProvider>
      <AppLayout>
        <Routes>
          {/* Public routes */}
          <Route 
            path="/login" 
            element={
              <PublicRoute>
                <Login />
              </PublicRoute>
            } 
          />
          <Route 
            path="/register" 
            element={
              <PublicRoute>
                <Register />
              </PublicRoute>
            } 
          />

          {/* Protected routes */}
          <Route 
            path="/dashboard" 
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/notes/new" 
            element={
              <ProtectedRoute>
                <CreateNote />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/notes/:id/edit" 
            element={
              <ProtectedRoute>
                <EditNote />
              </ProtectedRoute>
            } 
          />

          {/* Default redirect */}
          <Route path="/" element={<Navigate to="/dashboard" />} />
          
          {/* 404 page */}
          <Route 
            path="*" 
            element={
              <div className="min-h-screen flex items-center justify-center">
                <div className="text-center">
                  <h1 className="text-4xl font-bold text-gray-900 mb-4">404</h1>
                  <p className="text-gray-600">Page not found</p>
                </div>
              </div>
            } 
          />
        </Routes>
      </AppLayout>
    </AuthProvider>
  )
}

export default App
