function ErrorMessage({ children = 'Something went wrong. Please try again.' }) { return <div role="alert" className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">{children}</div> }
export default ErrorMessage
