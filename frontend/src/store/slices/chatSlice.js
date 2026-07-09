import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { sendChat } from "../../api/client";
import { applyInteractionRecord, loadHcps } from "./interactionSlice";
import { loadActivity } from "./activitySlice";

const initialState = {
  messages: [
    {
      role: "assistant",
      content:
        "Hi! Describe your interaction (e.g. \"Met Dr. Smith, discussed Product X efficacy, positive sentiment, shared brochure\") and I'll log it. You can also ask me to edit, recall history, schedule a follow-up, or suggest the next best action.",
    },
  ],
  sending: false,
  llmEnabled: true,
};

// Tools whose result is a single interaction record we can mirror into the form.
const RECORD_TOOLS = new Set(["log_interaction", "edit_interaction"]);

export const sendMessage = createAsyncThunk(
  "chat/send",
  async (text, { dispatch }) => {
    const data = await sendChat(text);
    // If the agent logged or edited an interaction, reflect it in the form.
    (data.events || []).forEach((ev) => {
      if (RECORD_TOOLS.has(ev.tool) && ev.result && typeof ev.result === "object") {
        dispatch(applyInteractionRecord(ev.result));
      }
    });
    if ((data.events || []).some((ev) => RECORD_TOOLS.has(ev.tool))) {
      dispatch(loadHcps(""));
    }
    // Any tool run may have changed the data (logged/edited/scheduled) — refresh
    // the Recent Activity panel so the UI reflects it, not just the chat.
    if ((data.events || []).length > 0) {
      dispatch(loadActivity());
    }
    return data;
  }
);

const chatSlice = createSlice({
  name: "chat",
  initialState,
  reducers: {
    addUserMessage(state, { payload }) {
      state.messages.push({ role: "user", content: payload });
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(sendMessage.pending, (state) => {
        state.sending = true;
      })
      .addCase(sendMessage.fulfilled, (state, { payload }) => {
        state.sending = false;
        state.llmEnabled = payload.llm_enabled;
        state.messages.push({
          role: "assistant",
          content: payload.reply,
          events: payload.events || [],
        });
      })
      .addCase(sendMessage.rejected, (state, { error }) => {
        state.sending = false;
        state.messages.push({
          role: "assistant",
          content: `Sorry, something went wrong: ${error.message}`,
        });
      });
  },
});

export const { addUserMessage } = chatSlice.actions;
export default chatSlice.reducer;
