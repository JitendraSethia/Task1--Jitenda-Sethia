import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import {
  fetchHcps,
  createInteraction,
  updateInteractionApi,
  summarizeText,
  suggestFollowupsApi,
} from "../../api/client";
import { loadActivity } from "./activitySlice";

const today = new Date().toISOString().slice(0, 10);
const now = new Date().toTimeString().slice(0, 5);

const emptyForm = {
  id: null,
  hcp_id: null,
  hcp_name: "",
  interaction_type: "Meeting",
  date: today,
  time: now,
  attendees: [],
  topics_discussed: "",
  materials_shared: [],
  samples_distributed: [],
  sentiment: "Neutral",
  outcomes: "",
  follow_up_actions: "",
  ai_suggested_followups: [],
};

const initialState = {
  form: { ...emptyForm },
  hcps: [],
  saving: false,
  summarizing: false,
  suggesting: false,
  status: null, // { type: 'success'|'error', message }
};

// ------------------------------ Thunks ------------------------------
export const loadHcps = createAsyncThunk("interaction/loadHcps", async (q = "") =>
  fetchHcps(q)
);

export const saveInteraction = createAsyncThunk(
  "interaction/save",
  async (_, { getState, dispatch }) => {
    const { form } = getState().interaction;
    const payload = { ...form };
    delete payload.id;
    delete payload.ai_suggested_followups;
    const saved = form.id
      ? await updateInteractionApi(form.id, payload)
      : await createInteraction(payload);
    // Keep the Recent Activity panel in sync with form saves.
    dispatch(loadActivity());
    return saved;
  }
);

export const summarizeFromNote = createAsyncThunk(
  "interaction/summarize",
  async (text, { getState }) => {
    const { hcp_name } = getState().interaction.form;
    return summarizeText(text, hcp_name);
  }
);

export const fetchSuggestions = createAsyncThunk(
  "interaction/suggest",
  async (_, { getState }) => {
    const { form } = getState().interaction;
    return suggestFollowupsApi({
      hcp_name: form.hcp_name,
      topics_discussed: form.topics_discussed,
      outcomes: form.outcomes,
      sentiment: form.sentiment,
    });
  }
);

// ------------------------------ Slice -------------------------------
const interactionSlice = createSlice({
  name: "interaction",
  initialState,
  reducers: {
    setField(state, { payload: { field, value } }) {
      state.form[field] = value;
    },
    addToList(state, { payload: { field, value } }) {
      const v = (value || "").trim();
      if (v && !state.form[field].includes(v)) state.form[field].push(v);
    },
    removeFromList(state, { payload: { field, index } }) {
      state.form[field].splice(index, 1);
    },
    resetForm(state) {
      state.form = {
        ...emptyForm,
        date: new Date().toISOString().slice(0, 10),
        time: new Date().toTimeString().slice(0, 5),
      };
      state.status = null;
    },
    clearStatus(state) {
      state.status = null;
    },
    // Merge a record returned by the chat agent (log/edit) into the form.
    applyInteractionRecord(state, { payload }) {
      if (!payload) return;
      const merge = (k) =>
        payload[k] !== undefined && payload[k] !== null ? payload[k] : state.form[k];
      state.form = {
        ...state.form,
        id: payload.id ?? state.form.id,
        hcp_name: merge("hcp_name"),
        interaction_type: merge("interaction_type"),
        date: merge("date") || state.form.date,
        time: merge("time") || state.form.time,
        attendees: payload.attendees ?? state.form.attendees,
        topics_discussed: merge("topics_discussed"),
        materials_shared: payload.materials_shared ?? state.form.materials_shared,
        samples_distributed:
          payload.samples_distributed ?? state.form.samples_distributed,
        sentiment: merge("sentiment"),
        outcomes: merge("outcomes"),
        follow_up_actions: merge("follow_up_actions"),
        ai_suggested_followups:
          payload.ai_suggested_followups ?? state.form.ai_suggested_followups,
      };
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(loadHcps.fulfilled, (state, { payload }) => {
        state.hcps = payload;
      })
      // save
      .addCase(saveInteraction.pending, (state) => {
        state.saving = true;
        state.status = null;
      })
      .addCase(saveInteraction.fulfilled, (state, { payload }) => {
        state.saving = false;
        state.form.id = payload.id;
        state.status = {
          type: "success",
          message: `Interaction #${payload.id} saved for ${payload.hcp_name || "HCP"}.`,
        };
      })
      .addCase(saveInteraction.rejected, (state, { error }) => {
        state.saving = false;
        state.status = { type: "error", message: error.message || "Save failed" };
      })
      // summarize
      .addCase(summarizeFromNote.pending, (state) => {
        state.summarizing = true;
      })
      .addCase(summarizeFromNote.fulfilled, (state, { payload }) => {
        state.summarizing = false;
        const f = state.form;
        f.topics_discussed = payload.topics_discussed || f.topics_discussed;
        f.sentiment = payload.sentiment || f.sentiment;
        f.outcomes = payload.outcomes || f.outcomes;
        if (payload.attendees?.length)
          f.attendees = Array.from(new Set([...f.attendees, ...payload.attendees]));
        if (payload.materials_shared?.length)
          f.materials_shared = Array.from(
            new Set([...f.materials_shared, ...payload.materials_shared])
          );
        if (payload.samples_distributed?.length)
          f.samples_distributed = Array.from(
            new Set([...f.samples_distributed, ...payload.samples_distributed])
          );
        if (payload.suggested_followups?.length)
          f.ai_suggested_followups = payload.suggested_followups;
      })
      .addCase(summarizeFromNote.rejected, (state, { error }) => {
        state.summarizing = false;
        state.status = { type: "error", message: error.message || "Summarize failed" };
      })
      // suggestions
      .addCase(fetchSuggestions.pending, (state) => {
        state.suggesting = true;
      })
      .addCase(fetchSuggestions.fulfilled, (state, { payload }) => {
        state.suggesting = false;
        state.form.ai_suggested_followups = payload.suggestions || [];
      })
      .addCase(fetchSuggestions.rejected, (state, { error }) => {
        state.suggesting = false;
        state.status = { type: "error", message: error.message || "Suggest failed" };
      });
  },
});

export const {
  setField,
  addToList,
  removeFromList,
  resetForm,
  clearStatus,
  applyInteractionRecord,
} = interactionSlice.actions;

export default interactionSlice.reducer;
