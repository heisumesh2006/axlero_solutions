import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'

function Scans() {
  const navigate = useNavigate()
  const [scans, setScans] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const loadScans = async () => {
      try {
        const response = await api.get('/scans')
        setScans(response.data)
      } catch (err) {
        setError(
          err.response?.data?.detail ||
          'Unable to load scans.'
        )
      } finally {
        setLoading(false)
      }
    }

    loadScans()
  }, [])

  if (loading) {
    return <p className="page-copy">Loading scans...</p>
  }

  if (error) {
    return (
      <section>
        <h1 className="page-title">Scans</h1>
        <div className="mt-8 rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-red-300">
          {error}
        </div>
      </section>
    )
  }

  return (
    <section>
      <h1 className="page-title">Scans</h1>
      <p className="page-copy">
        Review your security scan history.
      </p>

      {scans.length === 0 ? (
        <div className="surface mt-8 p-8 text-center text-slate-400">
          No scans found.
        </div>
      ) : (
        <div className="mt-8 space-y-4">
          {scans.map((scan) => (
            <button
              key={scan.id}
              onClick={() => navigate(`/scans/${scan.id}`)}
              className="surface w-full p-5 text-left transition hover:border-cyan-400/50"
            >
              <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <div>
                  <p className="font-semibold text-white">
                    {scan.target}
                  </p>
                  <p className="mt-1 text-sm text-slate-400">
                    {scan.scan_type} · Scan #{scan.id}
                  </p>
                </div>

                <div className="flex items-center gap-4">
                  <span className="text-sm text-slate-400">
                    {scan.status}
                  </span>

                  <span className="rounded-full bg-slate-800 px-3 py-1 text-sm font-semibold text-white">
                    Risk: {scan.risk_score}
                  </span>
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
    </section>
  )
}

export default Scans