function Loading({ label = 'Loading...' }) { return <div className="flex items-center gap-3 rounded-lg border border-slate-800 bg-slate-900/60 px-4 py-3 text-sm text-slate-400"><span className="h-4 w-4 rounded-full border-2 border-cyan-400/30 border-t-cyan-400" aria-hidden="true" />{label}</div> }
export default Loading
