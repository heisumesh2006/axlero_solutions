import { useCallback, useEffect, useMemo, useState } from "react";
import Analytics from "./components/Analytics";
import ContinuousLearning from "./components/ContinuousLearning";
import {
  apiErrorMessage,
  checkHealth,
  createDecision,
  createOutcome,
  createShipment,
  evaluateDecision,
  getDecisions,
  prescribeShipment,
} from "./services/api";

const initialForm = {
  country: "Nigeria",
  managed_by: "PMO - US",
  fulfill_via: "Direct Drop",
  vendor_inco_term: "EXW",
  shipment_mode: "Air",
  product_group: "ARV",
  sub_classification: "Pediatric",
  vendor: "Aurobindo Pharma Limited",
  brand: "Generic",
  dosage_form: "Oral solution",
  manufacturing_site: "Aurobindo Unit III, India",
  first_line_designation: "Yes",
  line_item_quantity: 416,
  line_item_value: 2225.6,
  weight: 504,
  freight_cost: 5920.42,
  scheduled_delivery_date: "2006-09-01",
  available_budget: 20000,
  minimum_inventory: 0,
};

const demoShipment = {
  country: "South Africa",
  managed_by: "PMO - US",
  fulfill_via: "Direct Drop",
  vendor_inco_term: "DDP",
  shipment_mode: "Air",
  product_group: "ARV",
  sub_classification: "Pediatric",
  vendor: "Aurobindo Pharma Limited",
  brand: "Generic",
  dosage_form: "Oral solution",
  manufacturing_site: "Aurobindo Unit III, India",
  first_line_designation: "Yes",
  line_item_quantity: 11628,
  line_item_value: 34884,
  weight: 4382,
  freight_cost: 2154.52,
  scheduled_delivery_date: "2010-08-24",
  available_budget: 20000,
  minimum_inventory: 14,
};

const fieldLabels = {
  country: "Country",
  managed_by: "Managed By",
  fulfill_via: "Fulfill Via",
  vendor_inco_term: "Vendor INCO Term",
  shipment_mode: "Shipment Mode",
  product_group: "Product Group",
  sub_classification: "Sub Classification",
  vendor: "Vendor",
  brand: "Brand",
  dosage_form: "Dosage Form",
  manufacturing_site: "Manufacturing Site",
  first_line_designation: "First Line Designation",
  line_item_quantity: "Line Item Quantity",
  line_item_value: "Line Item Value (USD)",
  weight: "Weight (kg)",
  freight_cost: "Freight Cost (USD)",
  scheduled_delivery_date: "Scheduled Delivery Date",
  available_budget: "Available Budget (USD)",
  minimum_inventory: "Inventory Buffer (days)",
};
const numericFields = new Set([
  "line_item_quantity", "line_item_value", "weight", "freight_cost", "available_budget", "minimum_inventory",
]);
const workflow = ["Analyze", "Predict", "Recommend", "Execute", "Write Back", "Record Outcome", "Evaluate", "Analytics"];
const currency = (value) => `$${Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 })}`;

function App() {
  const [backendOnline, setBackendOnline] = useState(null);
  const [form, setForm] = useState(initialForm);
  const [analysis, setAnalysis] = useState(null);
  const [shipmentId, setShipmentId] = useState("");
  const [shipmentSaved, setShipmentSaved] = useState(false);
  const [executedDecisionId, setExecutedDecisionId] = useState(null);
  const [decisions, setDecisions] = useState([]);
  const [selectedDecision, setSelectedDecision] = useState(null);
  const [actualCost, setActualCost] = useState("");
  const [actualDelay, setActualDelay] = useState("");
  const [evaluation, setEvaluation] = useState(null);
  const [analyticsKey, setAnalyticsKey] = useState(0);
  const [loading, setLoading] = useState(false);
  const [executionLoading, setExecutionLoading] = useState(false);
  const [outcomeLoading, setOutcomeLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [demoMessage, setDemoMessage] = useState("");

  const refreshDecisions = useCallback(async () => {
    try {
      const { data } = await getDecisions();
      setDecisions(data);
    } catch (error) {
      setMessage({ type: "error", text: apiErrorMessage(error, "Decision history could not be loaded.") });
    }
  }, []);

  useEffect(() => {
    checkHealth()
      .then(() => setBackendOnline(true))
      .catch(() => setBackendOnline(false));
    refreshDecisions();
  }, [refreshDecisions]);

  const numericPayload = useMemo(() => {
    const payload = { ...form };
    numericFields.forEach((field) => {
      payload[field] = Number(payload[field]);
    });
    return payload;
  }, [form]);

  const updateField = (event) => {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
    setDemoMessage("");
  };

  const loadDemoShipment = () => {
    setForm(demoShipment);
    setDemoMessage("Demo shipment 48857 loaded");
    setAnalysis(null);
    setMessage(null);
  };

  const analyze = async (event) => {
    event.preventDefault();
    setLoading(true);
    setMessage(null);
    setAnalysis(null);
    setEvaluation(null);
    setExecutedDecisionId(null);
    setShipmentSaved(false);
    setShipmentId(`UI-${Date.now()}`);
    try {
      const { data } = await prescribeShipment(numericPayload);
      setAnalysis(data);
    } catch (error) {
      setMessage({ type: "error", text: apiErrorMessage(error, "Shipment analysis failed.") });
    } finally {
      setLoading(false);
    }
  };

  const executeRecommendation = async (recommendation) => {
    if (!recommendation.feasible || executedDecisionId) return;
    setExecutionLoading(true);
    setMessage(null);
    try {
      if (!shipmentSaved) {
        await createShipment({
          shipment_id: shipmentId,
          country: form.country,
          vendor: form.vendor,
          product_group: form.product_group,
          shipment_mode: form.shipment_mode,
          line_item_quantity: Number(form.line_item_quantity),
          line_item_value: Number(form.line_item_value),
          weight: Number(form.weight),
          freight_cost: Number(form.freight_cost),
          scheduled_delivery_date: form.scheduled_delivery_date,
          available_budget: Number(form.available_budget),
        });
        setShipmentSaved(true);
      }
      const { data: decision } = await createDecision({
        shipment_id: shipmentId,
        selected_option: recommendation.option,
        option_title: recommendation.title,
        predicted_delay_probability: analysis.prediction.delay_probability,
        predicted_delay_days: analysis.prediction.predicted_delay_days,
        predicted_cost: recommendation.cost,
        available_budget: Number(form.available_budget),
      });
      setExecutedDecisionId(decision.id);
      setSelectedDecision(decision);
      setActualCost(decision.predicted_cost);
      setActualDelay(decision.predicted_delay_days);
      setMessage({ type: "success", text: "Decision executed successfully." });
      await refreshDecisions();
      setAnalyticsKey((key) => key + 1);
      document.getElementById("history")?.scrollIntoView({ behavior: "smooth" });
    } catch (error) {
      setMessage({ type: "error", text: apiErrorMessage(error, "Decision write-back failed.") });
    } finally {
      setExecutionLoading(false);
    }
  };

  const chooseDecision = (decision) => {
    setSelectedDecision(decision);
    setActualCost(decision.predicted_cost);
    setActualDelay(decision.predicted_delay_days);
    setEvaluation(null);
    setMessage(null);
  };

  const recordOutcome = async (event) => {
    event.preventDefault();
    if (!selectedDecision) return;
    setOutcomeLoading(true);
    setMessage(null);
    try {
      const { data: outcome } = await createOutcome({
        decision_id: selectedDecision.id,
        actual_cost: Number(actualCost),
        actual_delay_days: Number(actualDelay),
      });
      const { data: evaluationResult } = await evaluateDecision(selectedDecision.id);
      setEvaluation(evaluationResult);
      setMessage({
        type: outcome.success ? "success" : "warning",
        text: outcome.success ? "Outcome recorded: decision was successful." : "Outcome recorded: decision was not successful.",
      });
      setAnalyticsKey((key) => key + 1);
    } catch (error) {
      setMessage({ type: "error", text: apiErrorMessage(error, "Outcome submission failed.") });
    } finally {
      setOutcomeLoading(false);
    }
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-mark">SP</div>
        <div className="brand-copy">
          <h1>SupplyPrescript</h1>
          <p>Closed-Loop Prescriptive Analytics for Supply Chain Operations</p>
        </div>
        <div className={`system-status ${backendOnline ? "online" : backendOnline === false ? "offline" : "checking"}`}>
          <span className="status-dot">●</span>
          <div><small>Backend Connected</small><strong>{backendOnline ? "System Operational" : backendOnline === false ? "Backend Offline" : "Checking System"}</strong></div>
        </div>
      </header>

      <main>
        <section className="hero-panel">
          <div>
            <span className="eyebrow">Operations command center</span>
            <h2>From predicted disruption to measurable action.</h2>
            <p>Analyze shipment risk, select an optimized response, and capture the result in one operational loop.</p>
          </div>
          <div className="hero-stat"><span>Decision engine</span><strong>ML + LP</strong><small>Predictive and prescriptive</small></div>
        </section>

        <nav className="workflow" aria-label="SupplyPrescript workflow">
          {workflow.map((step, index) => (
            <div className="workflow-step" key={step}><span>{index + 1}</span><strong>{step}</strong>{index < workflow.length - 1 && <i>→</i>}</div>
          ))}
        </nav>

        {message && <div className={`alert ${message.type}`}>{message.text}</div>}

        <section className="section" id="analysis">
          <div className="section-heading"><div><span className="eyebrow">Step 01 · Predict</span><h2>Shipment Analysis</h2></div><span className="source-badge">Defaults from SCMS dataset</span></div>
          <form onSubmit={analyze}>
            <div className="form-grid">
              {Object.keys(initialForm).map((field) => (
                <label key={field} className={field === "vendor" || field === "manufacturing_site" ? "wide-field" : ""}>
                  <span>{fieldLabels[field]}</span>
                  <input
                    name={field}
                    type={field === "scheduled_delivery_date" ? "date" : numericFields.has(field) ? "number" : "text"}
                    step={numericFields.has(field) ? "any" : undefined}
                    min={numericFields.has(field) ? "0" : undefined}
                    value={form[field]}
                    onChange={updateField}
                    required
                  />
                </label>
              ))}
            </div>
            <div className="analysis-actions">
              <button className="secondary-button demo-button" type="button" onClick={loadDemoShipment}>
                ⚡ Load Demo Shipment
              </button>
              <button className="primary-button analyze-button" disabled={loading || backendOnline === false} type="submit">
                {loading ? <><span className="spinner" /> Analyzing shipment…</> : "Analyze Shipment"}
              </button>
              {demoMessage && <span className="demo-loaded-message">{demoMessage}</span>}
            </div>
          </form>
        </section>

        {analysis && (
          <>
            <section className="section prediction-section">
              <div className="section-heading"><div><span className="eyebrow">Step 02 · Assess</span><h2>Prediction Result</h2></div><span className={`risk-pill ${analysis.prediction.risk_level.toLowerCase()}`}>{analysis.prediction.risk_level} risk</span></div>
              <div className="prediction-grid">
                <article><span>Delay Probability</span><strong>{(analysis.prediction.delay_probability * 100).toFixed(1)}%</strong><small>Likelihood of late delivery</small></article>
                <article><span>Predicted Delay</span><strong>{analysis.prediction.predicted_delay_days.toFixed(1)}</strong><small>Expected days (+ late / − early)</small></article>
                <article><span>Risk Level</span><strong className={`risk-text ${analysis.prediction.risk_level.toLowerCase()}`}>{analysis.prediction.risk_level}</strong><small>Model-based operational exposure</small></article>
              </div>
            </section>

            <section className="section">
              <div className="section-heading"><div><span className="eyebrow">Step 03 · Prescribe</span><h2>Prescriptive Recommendations</h2></div><span className="source-badge">Ranked by SciPy optimization</span></div>
              <div className="recommendation-grid">
                {analysis.recommendations.map((item) => (
                  <article className={`recommendation-card ${item.rank === 1 ? "recommended" : ""} ${!item.feasible ? "infeasible" : ""}`} key={item.option}>
                    <div className="card-topline"><span className="option-badge">Option {item.option}</span><span className="rank-label">{item.recommendation_label}</span></div>
                    <h3>{item.title}</h3>
                    <div className="recommendation-stats"><div><span>Cost</span><strong>{currency(item.cost)}</strong></div><div><span>Expected delay</span><strong>{item.expected_delay_days.toFixed(1)} days</strong></div></div>
                    <div className="card-meta"><span className={`risk-pill ${item.risk_level.toLowerCase()}`}>{item.risk_level} risk</span><span>Score {item.objective_score.toFixed(4)}</span><span className={item.feasible ? "feasible" : "not-feasible"}>{item.feasible ? "Feasible" : "Over budget"}</span></div>
                    <p>{item.reason}</p><div className="tradeoff"><strong>Tradeoff</strong>{item.tradeoff}</div>
                    <button className="execute-button" disabled={!item.feasible || Boolean(executedDecisionId) || executionLoading} onClick={() => executeRecommendation(item)}>
                      {!item.feasible ? "Unavailable" : executedDecisionId ? "Decision Executed" : executionLoading ? "Writing decision…" : "Execute Decision"}
                    </button>
                  </article>
                ))}
              </div>
            </section>
          </>
        )}

        <section className="section" id="history">
          <div className="section-heading"><div><span className="eyebrow">Step 04 · Write back</span><h2>Decision History</h2></div><button className="secondary-button" onClick={refreshDecisions}>Refresh History</button></div>
          <div className="table-wrap">
            <table><thead><tr><th>Shipment</th><th>Option</th><th>Predicted Cost</th><th>Predicted Delay</th><th>Status</th><th>Executed At</th><th>Outcome</th></tr></thead>
              <tbody>{decisions.length ? decisions.map((decision) => (
                <tr key={decision.id}><td>{decision.shipment_id}</td><td><strong>{decision.selected_option}</strong> · {decision.option_title}</td><td>{currency(decision.predicted_cost)}</td><td>{decision.predicted_delay_days.toFixed(1)} days</td><td><span className="status-chip">{decision.decision_status}</span></td><td>{new Date(decision.executed_at).toLocaleString()}</td><td><button className="text-button" onClick={() => chooseDecision(decision)}>Record outcome</button></td></tr>
              )) : <tr><td colSpan="7" className="empty-cell">No executed decisions yet. Analyze a shipment to begin.</td></tr>}</tbody>
            </table>
          </div>

          {selectedDecision && (
            <div className="outcome-panel">
              <div><span className="eyebrow">Step 05 · Close the loop</span><h3>Record Actual Outcome</h3><p>Decision #{selectedDecision.id} · {selectedDecision.option_title} · {selectedDecision.shipment_id}</p></div>
              <form onSubmit={recordOutcome} className="outcome-form"><label><span>Actual Cost (USD)</span><input type="number" min="0" step="any" value={actualCost} onChange={(event) => setActualCost(event.target.value)} required /></label><label><span>Actual Delay Days</span><input type="number" step="any" value={actualDelay} onChange={(event) => setActualDelay(event.target.value)} required /></label><button className="primary-button" disabled={outcomeLoading}>{outcomeLoading ? "Evaluating…" : "Record Outcome"}</button></form>
              {evaluation && <div className={`evaluation-result ${evaluation.success ? "passed" : "failed"}`}><div className="evaluation-heading"><strong>{evaluation.success ? "Successful Decision" : "Decision Missed Target"}</strong><span>Evaluation saved to model feedback</span></div><div className="evaluation-grid"><div><span>Predicted Cost</span><strong>{currency(evaluation.predicted_cost)}</strong></div><div><span>Actual Cost</span><strong>{currency(evaluation.actual_cost)}</strong></div><div><span>Cost Error</span><strong>{currency(evaluation.cost_error)}</strong></div><div><span>Predicted Delay</span><strong>{evaluation.predicted_delay_days.toFixed(1)} days</strong></div><div><span>Actual Delay</span><strong>{evaluation.actual_delay_days.toFixed(1)} days</strong></div><div><span>Delay Error</span><strong>{evaluation.delay_error.toFixed(1)} days</strong></div></div></div>}
            </div>
          )}
        </section>

        <ContinuousLearning
          refreshKey={analyticsKey}
          onRetrained={() => setAnalyticsKey((key) => key + 1)}
        />
        <Analytics refreshKey={analyticsKey} />
      </main>
      <footer>SupplyPrescript · Academic operational analytics system · Live data from FastAPI and SQLite</footer>
    </div>
  );
}

export default App;
