import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import api from '../services/api'

function ScanDetails() {
  const { scanId } = useParams()

  const [scan, setScan] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const loadScan = async () => {
      try {
        const response = await api.get(`/scans/${scanId}`)
        setScan(response.data)
      } catch (err) {
        setError(
          err.response?.data?.detail ||
          err.response?.data?.error ||
          'Unable to load scan.'
        )
      } finally {
        setLoading(false)
      }
    }

    loadScan()
  }, [scanId])

  if (loading) {
    return (
      <section>
        <p className="page-copy">Loading scan...</p>
      </section>
    )
  }

  if (error) {
    return (
      <section>
        <Link
          to="/scans"
          className="text-sm font-medium text-cyan-300 hover:text-cyan-200"
        >
          ← Back to scans
        </Link>

        <div className="mt-8 rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-red-300">
          {error}
        </div>
      </section>
    )
  }

  if (!scan) {
    return null
  }

  const riskLevel =
    scan.risk_score >= 70
      ? 'HIGH'
      : scan.risk_score >= 40
        ? 'MEDIUM'
        : 'LOW'

  return (
    <section>
      <Link
        to="/scans"
        className="text-sm font-medium text-cyan-300 hover:text-cyan-200"
      >
        ← Back to scans
      </Link>

      <div className="mt-6">
        <h1 className="page-title">Scan Details</h1>
        <p className="page-copy">
          Security analysis for scan #{scan.id}
        </p>
      </div>

      <div className="mt-8 grid gap-6 md:grid-cols-3">
        <div className="surface p-6">
          <p className="text-sm text-slate-400">Risk Score</p>
          <p className="mt-2 text-4xl font-bold text-white">
            {scan.risk_score}
          </p>
        </div>

        <div className="surface p-6">
          <p className="text-sm text-slate-400">Threat Level</p>
          <p className="mt-2 text-2xl font-bold text-white">
            {riskLevel}
          </p>
        </div>

        <div className="surface p-6">
          <p className="text-sm text-slate-400">Status</p>
          <p className="mt-2 text-2xl font-bold text-white">
            {scan.status}
          </p>
        </div>
      </div>

      <div className="surface mt-6 p-6">
        <h2 className="text-lg font-semibold text-white">
          Target Information
        </h2>

        <div className="mt-4 space-y-3 text-sm">
          <div>
            <span className="text-slate-400">Target: </span>
            <span className="text-white">{scan.target}</span>
          </div>

          <div>
            <span className="text-slate-400">Scan Type: </span>
            <span className="text-white">{scan.scan_type}</span>
          </div>

          <div>
            <span className="text-slate-400">Scan ID: </span>
            <span className="text-white">{scan.id}</span>
          </div>
        </div>
      </div>

      <div className="mt-6 grid gap-6 md:grid-cols-2">
        <div className="surface p-6">
          <h2 className="text-lg font-semibold text-white">
            Findings
          </h2>

          <p className="mt-4 text-sm text-slate-400">
            Findings are available from the scan analysis response.
          </p>
        </div>

        <div className="surface p-6">
          <h2 className="text-lg font-semibold text-white">
            Recommendations
          </h2>

          <p className="mt-4 text-sm text-slate-400">
            Recommendations are available from the scan analysis response.
          </p>
        </div>
      </div>
    </section>
  )
}

export default ScanDetails