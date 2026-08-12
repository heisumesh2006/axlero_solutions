import { useEffect, useState } from "react";
import {
  apiErrorMessage,
  getRetrainingStatus,
  runRetraining,
} from "../services/api";

const money = (value) => `$${Number(value || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}`;

export default function ContinuousLearning({ refreshKey, onRetrained }) {
  const [learning, setLearning] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const checkStatus = async () => {
    setLoading(true);
    setMessage("");
    try {
      const { data } = await getRetrainingStatus();
      setLearning(data);
    } catch (error) {
      setMessage(apiErrorMessage(error, "Learning status could not be loaded."));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkStatus();
    // refreshKey represents new feedback from the operational loop.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshKey]);

  const retrain = async () => {
    setLoading(true);
    setMessage("");
    try {
      const { data } = await runRetraining();
      setMessage(data.status === "completed" ? `Model ${data.model_version} trained successfully.` : data.reason);
      await checkStatus();
      onRetrained();
    } catch (error) {
      setMessage(apiErrorMessage(error, "Retraining failed safely; the current model remains active."));
      setLoading(false);
    }
  };

  return (
    <section className="section learning-section" id="learning">
      <div className="section-heading">
        <div><span className="eyebrow">Feedback-driven improvement</span><h2>Continuous Learning</h2></div>
        {learning && <span className={`learning-status ${learning.retraining_required ? "required" : "current"}`}>{learning.retraining_required ? "Retraining Required" : "Model Current"}</span>}
      </div>
      {!learning ? <div className="empty-state">{loading ? "Checking learning status…" : "Learning status unavailable."}</div> : <>
        <div className="learning-grid">
          <article><span>Model Version</span><strong>{learning.model_version}</strong></article>
          <article><span>Feedback Records</span><strong>{learning.feedback_records}</strong></article>
          <article><span>Average Cost Error</span><strong>{money(learning.mean_cost_error)}</strong></article>
          <article><span>Average Delay Error</span><strong>{Number(learning.mean_delay_error).toFixed(1)} days</strong></article>
        </div>
        <p className="learning-reason">{learning.reason}</p>
        <div className="learning-actions">
          <button className="secondary-button" disabled={loading} onClick={checkStatus}>Check Learning Status</button>
          {learning.retraining_required && <button className="primary-button retrain-button" disabled={loading} onClick={retrain}>{loading ? "Retraining models…" : "Retrain Model"}</button>}
        </div>
      </>}
      {message && <div className="alert success">{message}</div>}
    </section>
  );
}
