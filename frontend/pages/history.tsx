import Head from "next/head";
import { useEffect, useState } from "react";
import axios from "axios";

interface SessionItem {
  id: string;
  session_id?: string;
  created_at?: string;
  last_updated?: string;
  message_count?: number;
  title?: string;
}

interface ConversationMessage {
  role: "user" | "assistant";
  content: string;
  timestamp?: string;
}

export default function HistoryPage() {
  const [sessions, setSessions] = useState<SessionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSession, setSelectedSession] = useState<SessionItem | null>(null);
  const [sessionMessages, setSessionMessages] = useState<ConversationMessage[]>([]);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [historyError, setHistoryError] = useState("");

  const normalizeSessions = (items: any[]): SessionItem[] => {
    return items.map((item) => {
      if (typeof item === "string") {
        return {
          id: item,
          session_id: item,
          title: `Conversation ${item.slice(0, 8)}`
        };
      }

      return {
        id: item?.id || item?.session_id || item?.sessionId || "unknown",
        session_id: item?.session_id || item?.id || item?.sessionId,
        created_at: item?.created_at || item?.createdAt,
        last_updated: item?.last_updated || item?.lastUpdated,
        message_count: item?.message_count ?? item?.messageCount,
        title: item?.title || `Conversation ${(item?.session_id || item?.id || "unknown").slice(0, 8)}`
      };
    });
  };

  useEffect(() => {
    const loadSessions = async () => {
      try {
        const res = await axios.get("http://localhost:8000/sessions");
        const sessionList = Array.isArray(res.data.sessions) ? res.data.sessions : [];
        setSessions(normalizeSessions(sessionList));
      } catch (error) {
        console.error("Failed to load sessions:", error);
        setSessions([]);
      } finally {
        setLoading(false);
      }
    };

    loadSessions();
  }, []);

  const openSession = async (session: SessionItem) => {
    const id = session.session_id || session.id;
    setSelectedSession(session);
    setLoadingMessages(true);
    setHistoryError("");

    try {
      const res = await axios.get(`http://localhost:8000/sessions/${encodeURIComponent(id)}/history`);
      setSessionMessages(Array.isArray(res.data.messages) ? res.data.messages : []);
    } catch (error) {
      console.error("Failed to load conversation:", error);
      setSessionMessages([]);
      setHistoryError("Could not load this conversation. Please check that the backend is running and try again.");
    } finally {
      setLoadingMessages(false);
    }
  };

  return (
    <>
      <Head>
        <title>Conversation History</title>
      </Head>

      <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(59,130,246,0.18),_transparent_20%),linear-gradient(135deg,#f5f7ff_0%,#eef4ff_32%,#fdf2f8_100%)] px-6 py-10 text-slate-800">
        <div className="mx-auto max-w-6xl">
          <div className="mb-8 flex items-center justify-between gap-4">
            <div>
              <p className="text-sm font-bold uppercase tracking-[0.25em] text-blue-600">History</p>
              <h1 className="mt-2 text-3xl font-extrabold bg-gradient-to-r from-blue-600 via-indigo-600 to-violet-600 bg-clip-text text-transparent">
                Conversation History
              </h1>
            </div>
            <a
              href="/"
              className="rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-blue-200 transition-all duration-200 hover:-translate-y-0.5"
            >
              ← Back to chat
            </a>
          </div>

          <div className="rounded-3xl border border-white/60 bg-white/80 p-6 shadow-[0_20px_45px_rgba(59,130,246,0.08)] backdrop-blur-xl">
            {selectedSession && (
              <section className="mb-6 rounded-2xl border border-indigo-100 bg-gradient-to-br from-indigo-50 via-white to-sky-50 p-5">
                <div className="mb-4 flex items-center justify-between gap-3">
                  <div>
                    <p className="text-xs font-bold uppercase tracking-wider text-indigo-500">Selected conversation</p>
                    <h2 className="mt-1 text-lg font-bold text-slate-800">{selectedSession.title}</h2>
                  </div>
                  <button
                    type="button"
                    onClick={() => setSelectedSession(null)}
                    className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-50"
                  >
                    Close
                  </button>
                </div>
                {loadingMessages ? (
                  <p className="text-sm text-slate-500">Loading conversation...</p>
                ) : historyError ? (
                  <p role="alert" className="text-sm font-medium text-rose-600">{historyError}</p>
                ) : sessionMessages.length === 0 ? (
                  <p className="text-sm text-slate-500">This conversation has no messages yet.</p>
                ) : (
                  <div className="max-h-[55vh] space-y-3 overflow-y-auto pr-1">
                    {sessionMessages.map((message, index) => (
                      <div key={`${message.timestamp || index}-${index}`} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
                        <div className={`max-w-[85%] rounded-2xl px-4 py-3 ${message.role === "user" ? "bg-indigo-600 text-white" : "border border-slate-200 bg-white text-slate-700"}`}>
                          <p className="mb-1 text-[10px] font-bold uppercase tracking-wide opacity-70">{message.role === "user" ? "You" : "Assistant"}</p>
                          <p className="whitespace-pre-wrap text-sm leading-relaxed">{message.content}</p>
                          {message.timestamp && <p className="mt-2 text-right text-[10px] opacity-60">{new Date(message.timestamp).toLocaleString()}</p>}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </section>
            )}

            {loading ? (
              <div className="flex items-center gap-3 rounded-2xl bg-slate-50 p-4 text-slate-500 ring-1 ring-slate-200">
                <div className="h-3 w-3 animate-pulse rounded-full bg-blue-500" />
                Loading sessions...
              </div>
            ) : sessions.length === 0 ? (
              <div className="space-y-3 rounded-2xl border border-dashed border-sky-200 bg-sky-50 p-6 text-center">
                <p className="text-xl font-bold text-slate-800">No saved conversations yet.</p>
                <p className="text-slate-500">Start a chat on the main page and it will appear here.</p>
              </div>
            ) : (
              <ul className="space-y-4">
                {sessions.map((session) => (
                  <li key={session.id}>
                    <button
                      type="button"
                      onClick={() => openSession(session)}
                      className="w-full rounded-2xl border border-slate-200 bg-gradient-to-r from-white to-slate-50 p-4 text-left shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-indigo-200 hover:shadow-md focus:outline-none focus:ring-4 focus:ring-indigo-100"
                    >
                      <span className="flex items-center justify-between gap-3 flex-wrap">
                        <span>
                          <span className="block text-lg font-bold text-slate-800">{session.title || "Conversation"}</span>
                          <span className="mt-1 flex items-center gap-3 text-sm text-slate-500">
                            <span>{session.created_at ? new Date(session.created_at).toLocaleString() : "Recent session"}</span>
                            {typeof session.message_count === "number" && (
                              <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-slate-600">
                                {session.message_count} msgs
                              </span>
                            )}
                          </span>
                        </span>
                        <span className="rounded-full bg-gradient-to-r from-violet-100 to-indigo-100 px-3 py-1 text-xs font-bold text-violet-700 ring-1 ring-violet-200">
                          Open · {(session.session_id || session.id || "unknown").slice(0, 8)}
                        </span>
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="mt-6 text-center text-sm font-medium text-slate-500">
            Built by <span className="font-bold text-indigo-600">Saurabh Kumar</span>
          </div>
        </div>
      </main>
    </>
  );
}
