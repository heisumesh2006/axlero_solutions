import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'

function Dashboard() {
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
          'Unable to load dashboard data.'
        )
      } finally {
        setLoading(false)
      }
    }

    loadScans()
  }, [])

  const totalScans = scans.length
  const highRisk = scans.filter((scan) => scan.risk_score >= 70).length
  const mediumRisk = scans.filter(
    (scan) => scan.risk_score >= 40 && scan.risk_score < 70
  ).length
  const lowRisk = scans.filter((scan) => scan.risk_score < 40).length

  const summary = [
    ['Total Scans', totalScans],
    ['High Risk', highRisk],
    ['Medium Risk', mediumRisk],
    ['Low Risk', lowRisk]
  ]

  if (loading) {
    return (
      <section>
        <h1 className="page-title">Security Overview</h1>
        <p className="page-copy">Loading security data...</p>
      </section>
    )
  }

  return (
    <section>
      <h1 className="page-title">Security Overview</h1>

      <p className="page-copy">
        Monitor your scanning activity and security risk posture.
      </p>

      {error && (
        <div className="mt-6 rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-300">
          {error}
        </div>
      )}

      <div className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {summary.map(([label, value]) => (
          <article
            key={label}
            className="surface min-h-32 p-5"
          >
            <h2 className="text-sm font-medium text-slate-400">
              {label}
            </h2>

            <p className="mt-6 text-3xl font-bold text-white">
              {value}
            </p>
          </article>
        ))}
      </div>

      <section className="surface mt-6 p-5 sm:p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-white">
              Recent Scans
            </h2>

            <p className="mt-1 text-sm text-slate-400">
              Latest security assessments
            </p>
          </div>

          <button
            onClick={() => navigate('/scans/new')}
            className="rounded-lg bg-cyan-500 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-400"
          >
            New Scan
          </button>
        </div>

        {scans.length === 0 ? (
          <div className="mt-6 rounded-lg border border-dashed border-slate-700 p-8 text-center text-sm text-slate-500">
            No scans available.
          </div>
        ) : (
          <div className="mt-6 space-y-3">
            {scans
              .slice()
              .reverse()
              .slice(0, 5)
              .map((scan) => (
                <button
                  key={scan.id}
                  onClick={() => navigate(`/scans/${scan.id}`)}
                  className="w-full rounded-lg border border-slate-700 bg-slate-900 p-4 text-left transition hover:border-cyan-400/50"
                >
                  <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                    <div>
                      <p className="font-medium text-white">
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
                        Risk {scan.risk_score}
                      </span>
                    </div>
                  </div>
                </button>
              ))}
          </div>
        )}
      </section>
    </section>
  )
}

export default Dashboard