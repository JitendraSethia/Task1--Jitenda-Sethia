import axios from "axios";

// Requests go to /api and Vite proxies them to the FastAPI backend (see vite.config.js).
// Longer timeout gives the backend room to wait out & retry transient Groq 429s.
const api = axios.create({ baseURL: "/api", timeout: 120000 });

export const fetchHcps = (q = "") =>
  api.get("/hcps", { params: { q } }).then((r) => r.data);

export const createInteraction = (payload) =>
  api.post("/interactions", payload).then((r) => r.data);

export const updateInteractionApi = (id, payload) =>
  api.put(`/interactions/${id}`, payload).then((r) => r.data);

export const listInteractions = (hcpName = "") =>
  api.get("/interactions", { params: { hcp_name: hcpName } }).then((r) => r.data);

export const listFollowUps = (hcpName = "") =>
  api.get("/follow-ups", { params: { hcp_name: hcpName } }).then((r) => r.data);

export const summarizeText = (text, hcpName = "") =>
  api.post("/ai/summarize", { text, hcp_name: hcpName }).then((r) => r.data);

export const suggestFollowupsApi = (payload) =>
  api.post("/ai/suggest-followups", payload).then((r) => r.data);

export const sendChat = (message, threadId = "default") =>
  api.post("/chat", { message, thread_id: threadId }).then((r) => r.data);

export const getHealth = () => api.get("/health").then((r) => r.data);

export default api;
