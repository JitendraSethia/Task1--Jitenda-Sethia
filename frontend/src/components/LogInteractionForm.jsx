import { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  loadHcps,
  setField,
  addToList,
  removeFromList,
  saveInteraction,
  resetForm,
  summarizeFromNote,
  fetchSuggestions,
  clearStatus,
} from "../store/slices/interactionSlice";
import TagInput from "./TagInput";

const INTERACTION_TYPES = [
  "Meeting",
  "Call",
  "Email",
  "Virtual Call",
  "Conference",
  "Sample Drop",
];
const SENTIMENTS = [
  { value: "Positive", emoji: "🙂" },
  { value: "Neutral", emoji: "😐" },
  { value: "Negative", emoji: "🙁" },
];

export default function LogInteractionForm() {
  const dispatch = useDispatch();
  const { form, hcps, saving, summarizing, suggesting, status } = useSelector(
    (s) => s.interaction
  );

  const [voiceOpen, setVoiceOpen] = useState(false);
  const [consent, setConsent] = useState(false);
  const [transcript, setTranscript] = useState("");

  useEffect(() => {
    dispatch(loadHcps(""));
  }, [dispatch]);

  useEffect(() => {
    if (status) {
      const t = setTimeout(() => dispatch(clearStatus()), 5000);
      return () => clearTimeout(t);
    }
  }, [status, dispatch]);

  const update = (field, value) => dispatch(setField({ field, value }));

  const handleSummarize = async () => {
    if (!consent || !transcript.trim()) return;
    await dispatch(summarizeFromNote(transcript));
    setVoiceOpen(false);
    setTranscript("");
    setConsent(false);
  };

  return (
    <section className="card form-card">
      <header className="card-header">
        <h2>Interaction Details</h2>
      </header>

      <div className="card-body">
        {/* HCP + Type */}
        <div className="grid-2">
          <div className="field">
            <label>HCP Name</label>
            <input
              list="hcp-options"
              placeholder="Search or select HCP..."
              value={form.hcp_name}
              onChange={(e) => update("hcp_name", e.target.value)}
            />
            <datalist id="hcp-options">
              {hcps.map((h) => (
                <option key={h.id} value={h.name}>
                  {h.specialty ? `${h.specialty} — ${h.institution}` : h.institution}
                </option>
              ))}
            </datalist>
          </div>
          <div className="field">
            <label>Interaction Type</label>
            <select
              value={form.interaction_type}
              onChange={(e) => update("interaction_type", e.target.value)}
            >
              {INTERACTION_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Date + Time */}
        <div className="grid-2">
          <div className="field">
            <label>Date</label>
            <input
              type="date"
              value={form.date}
              onChange={(e) => update("date", e.target.value)}
            />
          </div>
          <div className="field">
            <label>Time</label>
            <input
              type="time"
              value={form.time}
              onChange={(e) => update("time", e.target.value)}
            />
          </div>
        </div>

        {/* Attendees */}
        <div className="field">
          <label>Attendees</label>
          <TagInput
            values={form.attendees}
            placeholder="Enter names or search..."
            buttonLabel="Add"
            emptyLabel="No attendees added"
            onAdd={(v) => dispatch(addToList({ field: "attendees", value: v }))}
            onRemove={(i) => dispatch(removeFromList({ field: "attendees", index: i }))}
          />
        </div>

        {/* Topics Discussed */}
        <div className="field">
          <div className="label-row">
            <label>Topics Discussed</label>
            <button
              type="button"
              className="ai-chip"
              onClick={() => setVoiceOpen((o) => !o)}
              title="Summarize from a voice note / transcript"
            >
              ✨ AI
            </button>
          </div>
          <textarea
            rows={3}
            placeholder="Enter key discussion points..."
            value={form.topics_discussed}
            onChange={(e) => update("topics_discussed", e.target.value)}
          />
          <button
            type="button"
            className="link-btn"
            onClick={() => setVoiceOpen((o) => !o)}
          >
            🎙 Summarize from Voice Note (Requires Consent)
          </button>

          {voiceOpen && (
            <div className="voice-panel">
              <label className="consent">
                <input
                  type="checkbox"
                  checked={consent}
                  onChange={(e) => setConsent(e.target.checked)}
                />
                I confirm the HCP consented to recording / note capture.
              </label>
              <textarea
                rows={3}
                placeholder="Paste the voice-note transcript or dictate your raw notes here. The LLM will summarize and extract topics, sentiment, materials, samples & follow-ups."
                value={transcript}
                onChange={(e) => setTranscript(e.target.value)}
              />
              <div className="voice-actions">
                <button
                  type="button"
                  className="btn-primary"
                  disabled={!consent || !transcript.trim() || summarizing}
                  onClick={handleSummarize}
                >
                  {summarizing ? "Summarizing..." : "Summarize with AI"}
                </button>
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => setVoiceOpen(false)}
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Materials & Samples */}
        <h3 className="section-title">Materials Shared / Samples Distributed</h3>
        <div className="field">
          <label>Materials Shared</label>
          <TagInput
            values={form.materials_shared}
            placeholder="e.g. Product X efficacy brochure"
            buttonLabel="🔍 Search/Add"
            emptyLabel="No materials added"
            onAdd={(v) => dispatch(addToList({ field: "materials_shared", value: v }))}
            onRemove={(i) =>
              dispatch(removeFromList({ field: "materials_shared", index: i }))
            }
          />
        </div>
        <div className="field">
          <label>Samples Distributed</label>
          <TagInput
            values={form.samples_distributed}
            placeholder="e.g. OncoBoost 10mg x2"
            buttonLabel="➕ Add Sample"
            emptyLabel="No samples added"
            onAdd={(v) =>
              dispatch(addToList({ field: "samples_distributed", value: v }))
            }
            onRemove={(i) =>
              dispatch(removeFromList({ field: "samples_distributed", index: i }))
            }
          />
        </div>

        {/* Sentiment */}
        <div className="field">
          <label>Observed / Inferred HCP Sentiment</label>
          <div className="radio-row">
            {SENTIMENTS.map((s) => (
              <label
                key={s.value}
                className={`radio ${form.sentiment === s.value ? "active" : ""}`}
              >
                <input
                  type="radio"
                  name="sentiment"
                  checked={form.sentiment === s.value}
                  onChange={() => update("sentiment", s.value)}
                />
                <span className="sentiment-emoji">{s.emoji}</span>
                <span className={`dot dot-${s.value.toLowerCase()}`} />
                {s.value}
              </label>
            ))}
          </div>
        </div>

        {/* Outcomes */}
        <div className="field">
          <label>Outcomes</label>
          <textarea
            rows={2}
            placeholder="Key outcomes or agreements..."
            value={form.outcomes}
            onChange={(e) => update("outcomes", e.target.value)}
          />
        </div>

        {/* Follow-up Actions */}
        <div className="field">
          <label>Follow-up Actions</label>
          <textarea
            rows={2}
            placeholder="Enter next steps or tasks..."
            value={form.follow_up_actions}
            onChange={(e) => update("follow_up_actions", e.target.value)}
          />
        </div>

        {/* AI Suggested Follow-ups */}
        <div className="ai-suggest">
          <div className="label-row">
            <span className="ai-suggest-title">✨ AI Suggested Follow-ups</span>
            <button
              type="button"
              className="link-btn"
              disabled={suggesting}
              onClick={() => dispatch(fetchSuggestions())}
            >
              {suggesting ? "Thinking..." : "Generate"}
            </button>
          </div>
          {form.ai_suggested_followups.length > 0 && (
            <ul className="suggest-list">
              {form.ai_suggested_followups.map((s, i) => (
                <li key={i}>
                  <button
                    type="button"
                    title="Add to Follow-up Actions"
                    onClick={() =>
                      update(
                        "follow_up_actions",
                        form.follow_up_actions
                          ? `${form.follow_up_actions}\n• ${s}`
                          : `• ${s}`
                      )
                    }
                  >
                    + {s}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      <footer className="form-footer">
        {status && <span className={`status ${status.type}`}>{status.message}</span>}
        <div className="footer-actions">
          <button
            type="button"
            className="btn-secondary"
            onClick={() => dispatch(resetForm())}
          >
            New
          </button>
          <button
            type="button"
            className="btn-primary"
            disabled={saving}
            onClick={() => dispatch(saveInteraction())}
          >
            {saving ? "Saving..." : form.id ? "Update Interaction" : "Log Interaction"}
          </button>
        </div>
      </footer>
    </section>
  );
}
