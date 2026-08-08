import { Link, useParams } from 'react-router-dom'
function ScanDetails() { const { scanId } = useParams(); return <section><Link to="/scans" className="text-sm font-medium text-cyan-300 hover:text-cyan-200">← Back to scans</Link><h1 className="page-title mt-4">Scan Details</h1><p className="page-copy">Results for scan <span className="font-mono text-slate-300">{scanId}</span> will be displayed here.</p><div className="surface mt-8 grid min-h-80 place-items-center p-6 text-center text-sm text-slate-500">Scan analysis details placeholder</div></section> }
export default ScanDetails
