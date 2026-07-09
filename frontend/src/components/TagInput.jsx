import { useState } from "react";

/**
 * Chip-style multi-value input used for Attendees, Materials Shared and
 * Samples Distributed. Add on Enter or via the action button.
 */
export default function TagInput({
  values = [],
  placeholder,
  buttonLabel,
  emptyLabel,
  onAdd,
  onRemove,
}) {
  const [text, setText] = useState("");

  const commit = () => {
    const v = text.trim();
    if (v) {
      onAdd(v);
      setText("");
    }
  };

  return (
    <div className="tag-input">
      <div className="tag-input-row">
        <input
          type="text"
          value={text}
          placeholder={placeholder}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              commit();
            }
          }}
        />
        {buttonLabel && (
          <button type="button" className="btn-secondary" onClick={commit}>
            {buttonLabel}
          </button>
        )}
      </div>
      {values.length === 0 ? (
        <p className="muted-hint">{emptyLabel}</p>
      ) : (
        <div className="chips">
          {values.map((v, i) => (
            <span className="chip" key={`${v}-${i}`}>
              {v}
              <button
                type="button"
                aria-label={`Remove ${v}`}
                onClick={() => onRemove(i)}
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
