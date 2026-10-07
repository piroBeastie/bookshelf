import React, { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import './styles.css'

const SHELVES = ['WANT', 'READING', 'FINISHED']
const EMPTY = { title: '', author: '', genre: 'General', pages: 0, shelf: 'WANT', rating: 0 }

function api(path, options) {
  return fetch(`/api${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
}

function App() {
  const [books, setBooks] = useState([])
  const [stats, setStats] = useState(null)
  const [form, setForm] = useState(EMPTY)
  const [filter, setFilter] = useState('ALL')
  const [error, setError] = useState('')

  async function load() {
    try {
      const query = filter === 'ALL' ? '' : `?shelf=${filter}`
      const [booksRes, statsRes] = await Promise.all([
        api(`/books${query}`),
        api('/books/stats'),
      ])
      if (!booksRes.ok || !statsRes.ok) throw new Error('backend returned an error')
      setBooks(await booksRes.json())
      setStats(await statsRes.json())
      setError('')
    } catch (err) {
      setError('could not reach the backend')
    }
  }

  useEffect(() => {
    load()
  }, [filter])

  async function addBook(event) {
    event.preventDefault()
    const response = await api('/books', {
      method: 'POST',
      body: JSON.stringify({ ...form, pages: Number(form.pages), rating: Number(form.rating) }),
    })
    if (response.status === 201) {
      setForm(EMPTY)
      load()
    } else {
      setError('the book was rejected - check the title, author and rating')
    }
  }

  async function moveShelf(book, shelf) {
    await api(`/books/${book.id}`, { method: 'PUT', body: JSON.stringify({ shelf }) })
    load()
  }

  async function rate(book, rating) {
    await api(`/books/${book.id}`, { method: 'PUT', body: JSON.stringify({ rating }) })
    load()
  }

  async function remove(book) {
    await api(`/books/${book.id}`, { method: 'DELETE' })
    load()
  }

  return (
    <div className="page">
      <header>
        <h1>BookShelf</h1>
        <p>my reading list - FastAPI + PostgreSQL + React</p>
      </header>

      {error && <div className="error">{error}</div>}

      {stats && (
        <section className="stats">
          <div><span>{stats.total}</span>books</div>
          <div><span>{stats.reading}</span>reading</div>
          <div><span>{stats.finished}</span>finished</div>
          <div><span>{stats.pagesRead}</span>pages read</div>
          <div><span>{stats.averageRating}</span>avg rating</div>
        </section>
      )}

      <form className="add" onSubmit={addBook}>
        <input
          placeholder="Title"
          value={form.title}
          onChange={(e) => setForm({ ...form, title: e.target.value })}
          required
        />
        <input
          placeholder="Author"
          value={form.author}
          onChange={(e) => setForm({ ...form, author: e.target.value })}
          required
        />
        <input
          placeholder="Genre"
          value={form.genre}
          onChange={(e) => setForm({ ...form, genre: e.target.value })}
        />
        <input
          type="number"
          min="0"
          placeholder="Pages"
          value={form.pages}
          onChange={(e) => setForm({ ...form, pages: e.target.value })}
        />
        <select value={form.shelf} onChange={(e) => setForm({ ...form, shelf: e.target.value })}>
          {SHELVES.map((shelf) => (
            <option key={shelf} value={shelf}>{shelf}</option>
          ))}
        </select>
        <button type="submit">Add book</button>
      </form>

      <div className="filters">
        {['ALL', ...SHELVES].map((shelf) => (
          <button
            key={shelf}
            className={filter === shelf ? 'active' : ''}
            onClick={() => setFilter(shelf)}
          >
            {shelf}
          </button>
        ))}
      </div>

      <ul className="books">
        {books.map((book) => (
          <li key={book.id}>
            <div className="meta">
              <strong>{book.title}</strong>
              <span>{book.author} · {book.genre} · {book.pages} pages</span>
            </div>
            <div className="actions">
              <select value={book.shelf} onChange={(e) => moveShelf(book, e.target.value)}>
                {SHELVES.map((shelf) => (
                  <option key={shelf} value={shelf}>{shelf}</option>
                ))}
              </select>
              <select value={book.rating} onChange={(e) => rate(book, Number(e.target.value))}>
                {[0, 1, 2, 3, 4, 5].map((n) => (
                  <option key={n} value={n}>{n === 0 ? 'no rating' : `${n} star`}</option>
                ))}
              </select>
              <button className="delete" onClick={() => remove(book)}>Delete</button>
            </div>
          </li>
        ))}
        {books.length === 0 && <li className="empty">nothing on this shelf yet</li>}
      </ul>
    </div>
  )
}

createRoot(document.getElementById('root')).render(<App />)
