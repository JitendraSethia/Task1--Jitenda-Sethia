import { configureStore } from "@reduxjs/toolkit";
import interactionReducer from "./slices/interactionSlice";
import chatReducer from "./slices/chatSlice";
import activityReducer from "./slices/activitySlice";

export const store = configureStore({
  reducer: {
    interaction: interactionReducer,
    chat: chatReducer,
    activity: activityReducer,
  },
});
