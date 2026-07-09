import LogInteractionForm from "./components/LogInteractionForm";
import ChatAssistant from "./components/ChatAssistant";
import RecentActivity from "./components/RecentActivity";

export default function App() {
  return (
    <div className="app">
      <header className="app-bar">
        <div className="app-bar-inner">
          <h1>Log HCP Interaction</h1>
          <span className="app-bar-tag">AI-First CRM · HCP Module</span>
        </div>
      </header>

      <main className="layout">
        <div className="col-main">
          <LogInteractionForm />
          <RecentActivity />
        </div>
        <ChatAssistant />
      </main>
    </div>
  );
}
