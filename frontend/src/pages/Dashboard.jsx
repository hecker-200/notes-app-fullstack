/**
 * Dashboard Page
 * Main page displaying user's notes with search and filtering capabilities
 */

import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { notesAPI, getErrorMessage } from '../utils/api'
import { useAuth } from '../context/AuthContext'
import NoteCard from '../components/NoteCard'
import Loading from '../components/Loading'

export default function Dashboard() {
  const [notes, setNotes] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [error, setError] = useState('')
  const { user } = useAuth()

  // Load notes on component mount
  useEffect(() => {
    loadNotes()
  }, [])

  /**
   * Load notes from API
   */
  const loadNotes = async (search = '') => {
    try {
      setLoading(true)
      setError('')
      
      const params = search ? { search } : {}
      const response = await notesAPI.getNotes(params)
      setNotes(response.notes || [])
    } catch (error) {
      console.error('Failed to load notes:', error)
      setError(getErrorMessage(error))
    } finally {
      setLoading(false)
    }
  }

  /**
   * Handle search input changes with debouncing
   */
  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      if (searchQuery !== '') {
        loadNotes(searchQuery)
      } else {
        loadNotes()
      }
    }, 500) // 500ms debounce

    return () => clearTimeout(debounceTimer)
  }, [searchQuery])

  /**
   * Handle note deletion
   */
  const handleDeleteNote = async (note) => {
    if (!window.confirm('Are you sure you want to delete this note?')) {
      return
    }

    try {
      await notesAPI.deleteNote(note.id)
      // Remove the note from local state
      setNotes(notes.filter(n => n.id !== note.id))
    } catch (error) {
      console.error('Failed to delete note:', error)
      alert(getErrorMessage(error))
    }
  }

  /**
   * Handle toggling note favorite status
   */
  const handleToggleFavorite = async (note) => {
    try {
      const updatedNote = await notesAPI.updateNote(note.id, {
        is_favorite: !note.is_favorite,
        version: note.version
      })
      
      // Update the note in local state
      setNotes(notes.map(n => n.id === note.id ? updatedNote : n))
    } catch (error) {
      console.error('Failed to update note:', error)
      alert(getErrorMessage(error))
    }
  }

  if (loading && notes.length === 0) {
    return <Loading />
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              Welcome back, {user?.full_name || user?.email}! 👋
            </h1>
            <p className="mt-2 text-gray-600">
              {notes.length === 0 
                ? "You don't have any notes yet. Create your first note to get started!"
                : `You have ${notes.length} notes`
              }
            </p>
          </div>
          
          <Link
            to="/notes/new"
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            New Note
          </Link>
        </div>
      </div>

      {/* Search Bar */}
      <div className="mb-6">
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <input
            type="text"
            className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            placeholder="Search notes..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-6 rounded-md bg-red-50 p-4">
          <div className="text-sm text-red-700">{error}</div>
        </div>
      )}

      {/* Loading indicator for search */}
      {loading && notes.length > 0 && (
        <div className="mb-4 flex items-center justify-center">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
          <span className="ml-2 text-gray-600">Searching...</span>
        </div>
      )}

      {/* Notes Grid */}
      {notes.length === 0 && !loading ? (
        <div className="text-center py-12">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">
            {searchQuery ? 'No notes found' : 'No notes yet'}
          </h3>
          <p className="mt-1 text-sm text-gray-500">
            {searchQuery 
              ? `No notes match "${searchQuery}". Try a different search term.`
              : 'Get started by creating a new note.'
            }
          </p>
          {!searchQuery && (
            <div className="mt-6">
              <Link
                to="/notes/new"
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Create your first note
              </Link>
            </div>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {notes.map((note) => (
            <NoteCard
              key={note.id}
              note={note}
              onDelete={handleDeleteNote}
              onToggleFavorite={handleToggleFavorite}
            />
          ))}
        </div>
      )}
    </div>
  )
}
