import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { loadActivity } from "../store/slices/activitySlice";
import { applyInteractionRecord } from "../store/slices/interactionSlice";

const SENTIMENT_EMOJI = { Positive: "🙂", Neutral: "😐", Negative: "🙁" };

function Chips({ items }) {
  if (!items || items.length === 0) return null;
  return (
    <div className="chips act-chips">
      {items.map((it, i) => (
        <span className="chip" key={i}>
          {it}
        </span>
      ))}
    </div>
  );
}

export default function RecentActivity() {
  const dispatch = useDispatch();
  const { interactions, followUps, loading } = useSelector((s) => s.activity);

  useEffect(() => {
    dispatch(loadActivity());
  }, [dispatch]);

  return (
    <section className="card activity-card">
      <header className="card-header activity-header">
        <div>
          <h2>📋 Recent Interactions &amp; Follow-ups</h2>
          <p className="chat-sub">
            Live view of what's logged — updates when you log, edit or schedule.
          </p>
        </div>
        <button
          type="button"
          className="btn-secondary btn-sm"
          onClick={() => dispatch(loadActivity())}
          disabled={loading}
        >
          {loading ? "Refreshing…" : "↻ Refresh"}
        </button>
      </header>

      <div className="card-body activity-body">
        {/* Interactions */}
        <div className="activity-col">
          <div className="activity-col-title">
            Interactions <span className="count">{interactions.length}</span>
          </div>
          {interactions.length === 0 && !loading && (
            <p className="muted-hint">No interactions logged yet.</p>
          )}
          <ul className="activity-list">
            {interactions.map((it) => (
              <li className="activity-item" key={it.id}>
                <div className="activity-item-top">
                  <span className="activity-name">
                    {it.hcp_name || "Unknown HCP"}
                  </span>
                  <span className={`sentiment-tag s-${(it.sentiment || "Neutral").toLowerCase()}`}>
                    {SENTIMENT_EMOJI[it.sentiment] || "😐"} {it.sentiment || "Neutral"}
                  </span>
                </div>
                <div className="activity-meta">
                  <span className="pill-type">{it.interaction_type}</span>
                  {it.date && <span>· {it.date}</span>}
                  <span className="act-id">#{it.id}</span>
                </div>
                {(it.ai_summary || it.topics_discussed) && (
                  <p className="activity-summary">
                    {it.ai_summary || it.topics_discussed}
                  </p>
                )}
                <Chips items={it.materials_shared} />
                <Chips items={it.samples_distributed} />
                <button
                  type="button"
                  className="link-btn"
                  title="Load this interaction into the form to edit"
                  onClick={() => dispatch(applyInteractionRecord(it))}
                >
                  ✏️ Edit in form
                </button>
              </li>
            ))}
          </ul>
        </div>

        {/* Follow-ups */}
        <div className="activity-col">
          <div className="activity-col-title">
            Follow-ups <span className="count">{followUps.length}</span>
          </div>
          {followUps.length === 0 && !loading && (
            <p className="muted-hint">No follow-ups scheduled yet.</p>
          )}
          <ul className="activity-list">
            {followUps.map((f) => (
              <li className="activity-item followup" key={f.id}>
                <div className="activity-item-top">
                  <span className="activity-name">{f.description}</span>
                  <span className={`status-badge st-${f.status}`}>{f.status}</span>
                </div>
                <div className="activity-meta">
                  {f.hcp_name && <span>{f.hcp_name}</span>}
                  {f.due_date && <span>· due {f.due_date}</span>}
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
