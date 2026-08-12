import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { apiErrorMessage, getAnalytics } from "../services/api";

const money = (value) => `$${Number(value || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
const number = (value) => Number(value || 0).toFixed(1);

export default function Analytics({ refreshKey }) {
  const [analytics, setAnalytics] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    getAnalytics()
      .then(({ data }) => {
        if (active) setAnalytics(data);
      })
      .catch((requestError) => active && setError(apiErrorMessage(requestError)));
    return () => {
      active = false;
    };
  }, [refreshKey]);

  const cards = analytics
    ? [
        ["Total Decisions", analytics.total_decisions],
        ["Successful Decisions", analytics.successful_decisions],
        ["Success Rate", `${(analytics.success_rate * 100).toFixed(1)}%`],
        ["Avg Predicted Cost", money(analytics.average_predicted_cost)],
        ["Avg Actual Cost", money(analytics.average_actual_cost)],
        ["Avg Cost Error", money(analytics.average_cost_error)],
        ["Avg Predicted Delay", `${number(analytics.average_predicted_delay)} days`],
        ["Avg Actual Delay", `${number(analytics.average_actual_delay)} days`],
        ["Avg Delay Error", `${number(analytics.average_delay_error)} days`],
      ]
    : [];
  const hasOutcomes = analytics && (
    analytics.average_actual_cost !== 0 ||
    analytics.average_actual_delay !== 0 ||
    analytics.average_cost_error !== 0 ||
    analytics.average_delay_error !== 0
  );
  const chartData = analytics
    ? [{ name: "Average cost", Predicted: analytics.average_predicted_cost, Actual: analytics.average_actual_cost }]
    : [];

  return (
    <section className="section" id="analytics">
      <div className="section-heading">
        <div>
          <span className="eyebrow">Closed-loop performance</span>
          <h2>Analytics</h2>
        </div>
        <span className="live-data">Live database metrics</span>
      </div>
      {error && <div className="alert error">{error}</div>}
      {!analytics ? (
        <div className="empty-state">Loading analytics…</div>
      ) : (
        <>
          <div className="metric-grid">
            {cards.map(([label, value]) => (
              <article className="metric-card" key={label}>
                <span>{label}</span>
                <strong>{value}</strong>
              </article>
            ))}
          </div>
          {hasOutcomes ? (
            <div className="chart-card">
              <h3>Predicted Cost vs Actual Cost</h3>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={chartData} margin={{ top: 16, right: 16, left: 16, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="name" />
                  <YAxis tickFormatter={(value) => `$${value / 1000}k`} />
                  <Tooltip formatter={(value) => money(value)} />
                  <Legend />
                  <Bar dataKey="Predicted" fill="#155eef" radius={[6, 6, 0, 0]} />
                  <Bar dataKey="Actual" fill="#35b9a5" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="empty-state">No decision outcomes available yet.</div>
          )}
        </>
      )}
    </section>
  );
}
