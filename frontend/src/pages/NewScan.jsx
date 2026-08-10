import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'

function NewScan() {
  const navigate = useNavigate()
  const [target, setTarget] = useState('')
  const [scanType, setScanType] = useState('WEB')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!target.trim()) {
      setError('Please enter a target.')
      return
    }

    try {
      setLoading(true)
      setError('')

      const scan = await api.post('/scans', {
        target: target.trim(),
        scan_type: scanType
      })

      await api.post(`/scans/${scan.data.id}/analyze`)

      navigate(`/scans/${scan.data.id}`)
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        err.response?.data?.error ||
        'Unable to create or analyze scan.'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <section>
      <h1 className="page-title">New Scan</h1>
      <p className="page-copy">
        Start a security assessment for a target.
      </p>

      <form
        onSubmit={handleSubmit}
        className="surface mt-8 max-w-2xl space-y-6 p-6"
      >
        <div>
          <label className="mb-2 block text-sm font-medium text-slate-300">
            Target
          </label>

          <input
            type="text"
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            placeholder="http://example.com"
            className="w-full rounded-lg border border-slate-700 bg-slate-900 px-4 py-3 text-white outline-none focus:border-cyan-400"
          />
        </div>

        <div>
          <label className="mb-2 block text-sm font-medium text-slate-300">
            Scan Type
          </label>

          <select
            value={scanType}
            onChange={(e) => setScanType(e.target.value)}
            className="w-full rounded-lg border border-slate-700 bg-slate-900 px-4 py-3 text-white outline-none focus:border-cyan-400"
          >
            <option value="WEB">WEB</option>
          </select>
        </div>

        {error && (
          <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-300">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="rounded-lg bg-cyan-500 px-5 py-3 font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? 'Analyzing...' : 'Start Scan'}
        </button>
      </form>
    </section>
  )
}

export default NewScan