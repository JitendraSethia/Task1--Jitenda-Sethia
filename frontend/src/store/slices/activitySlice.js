import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { listInteractions, listFollowUps } from "../../api/client";

const initialState = {
  interactions: [],
  followUps: [],
  loading: false,
  error: null,
};

// Load recent interactions + follow-ups together so the panel refreshes in one go.
export const loadActivity = createAsyncThunk("activity/load", async () => {
  const [interactions, followUps] = await Promise.all([
    listInteractions(),
    listFollowUps(),
  ]);
  return { interactions, followUps };
});

const activitySlice = createSlice({
  name: "activity",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(loadActivity.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(loadActivity.fulfilled, (state, { payload }) => {
        state.loading = false;
        state.interactions = payload.interactions || [];
        state.followUps = payload.followUps || [];
      })
      .addCase(loadActivity.rejected, (state, { error }) => {
        state.loading = false;
        state.error = error.message || "Failed to load activity";
      });
  },
});

export default activitySlice.reducer;
