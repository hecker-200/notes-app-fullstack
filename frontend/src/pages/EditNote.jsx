/**
 * EditNote Page
 * Form for editing an existing note with optimistic concurrency control
 */

import { useState, useEffect } from 'react'
import { useNavigate, useParams, Link } from 'react-router-dom'
import { notesAPI, getErrorMessage } from '../utils/api'
import Loading from '../components/Loading'

export default function EditNote() {
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    tags: '',
    is_favorite: false,
    version: 1
  })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  
  const navigate = useNavigate()
  const { id } = useParams()

  // Load note data on component mount
  useEffect(() => {
    loadNote()
  }, [id])

  /**
   * Load note data from API
   */
  const loadNote = async () => {
    try {
      setLoading(true)
      setError('')
      
      const note = await notesAPI.getNote(id)
      
      setFormData({
        title: note.title,
        content: note.content,
        tags: note.tags ? note.tags.join(', ') : '',
        is_favorite: note.is_favorite,
        version: note.version
      })
    } catch (error) {
      console.error('Failed to load note:', error)
      setError(getErrorMessage(error))
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')

    // Validate required fields
    if (!formData.title.trim()) {
      setError('Title is required')
      setSaving(false)
      return
    }

    if (!formData.content.trim()) {
      setError('Content is required')
      setSaving(false)
      return
    }

    try {
      // Parse tags from comma-separated string
      const tags = formData.tags
        .split(',')
        .map(tag => tag.trim())
        .filter(tag => tag.length > 0)

      const updateData = {
        title: formData.title.trim(),
        content: formData.content.trim(),
        tags: tags,
        is_favorite: formData.is_favorite,
        version: formData.version // Include version for optimistic concurrency
      }

      const updatedNote = await notesAPI.updateNote(id, updateData)
      
      // Update local version number
      setFormData(prev => ({
        ...prev,
        version: updatedNote.version
      }))
      
      // Redirect to dashboard on success
      navigate('/dashboard')
    } catch (error) {
      console.error('Failed to update note:', error)
      const errorMessage = getErrorMessage(error)
      
      // Handle version conflict specifically
      if (error.response?.status === 409) {
        setError('This note was modified by another session. Please refresh the page to get the latest version and try again.')
      } else {
        setError(errorMessage)
      }
    } finally {
      setSaving(false)
    }
  }

  /**
   * Handle refreshing note data (useful when version conflict occurs)
   */
  const handleRefresh = () => {
    loadNote()
  }

  if (loading) {
    return <Loading />
  }

  if (error && !formData.title) {
    return (
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Error Loading Note</h1>
          <p className="text-gray-600 mb-6">{error}</p>
          <Link
            to="/dashboard"
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
          >
            Back to Notes
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Edit Note</h1>
            <p className="mt-2 text-gray-600">
              Make changes to your note. Changes are saved with version control.
            </p>
          </div>
          
          <Link
            to="/dashboard"
            className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Back to Notes
          </Link>
        </div>
      </div>

      {/* Form */}
      <div className="bg-white shadow rounded-lg">
        <form onSubmit={handleSubmit} className="p-6">
          {error && (
            <div className="mb-6 rounded-md bg-red-50 p-4">
              <div className="flex items-center justify-between">
                <div className="text-sm text-red-700">{error}</div>
                {error.includes('version conflict') || error.includes('modified by another') && (
                  <button
                    type="button"
                    onClick={handleRefresh}
                    className="ml-4 text-sm text-red-600 hover:text-red-800 font-medium"
                  >
                    Refresh Note
                  </button>
                )}
              </div>
            </div>
          )}

          <div className="space-y-6">
            {/* Version info */}
            <div className="text-xs text-gray-500">
              Version: {formData.version}
            </div>

            {/* Title */}
            <div>
              <label htmlFor="title" className="block text-sm font-medium text-gray-700">
                Title *
              </label>
              <input
                type="text"
                id="title"
                name="title"
                required
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm px-3 py-2 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="Enter note title"
                value={formData.title}
                onChange={handleChange}
              />
            </div>

            {/* Content */}
            <div>
              <label htmlFor="content" className="block text-sm font-medium text-gray-700">
                Content *
              </label>
              <textarea
                id="content"
                name="content"
                rows={12}
                required
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm px-3 py-2 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="Write your note content here..."
                value={formData.content}
                onChange={handleChange}
              />
            </div>

            {/* Tags */}
            <div>
              <label htmlFor="tags" className="block text-sm font-medium text-gray-700">
                Tags
              </label>
              <input
                type="text"
                id="tags"
                name="tags"
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm px-3 py-2 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="Enter tags separated by commas (e.g., work, important, ideas)"
                value={formData.tags}
                onChange={handleChange}
              />
              <p className="mt-1 text-xs text-gray-500">
                Separate multiple tags with commas. Tags help you organize and find your notes.
              </p>
            </div>

            {/* Favorite */}
            <div className="flex items-center">
              <input
                id="is_favorite"
                name="is_favorite"
                type="checkbox"
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                checked={formData.is_favorite}
                onChange={handleChange}
              />
              <label htmlFor="is_favorite" className="ml-2 block text-sm text-gray-700">
                Mark as favorite
              </label>
            </div>
          </div>

          {/* Actions */}
          <div className="pt-6 border-t border-gray-200 mt-6">
            <div className="flex items-center justify-end space-x-3">
              <Link
                to="/dashboard"
                className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Cancel
              </Link>
              
              <button
                type="submit"
                disabled={saving}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {saving ? (
                  <div className="flex items-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Saving...
                  </div>
                ) : (
                  'Save Changes'
                )}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  )
}
