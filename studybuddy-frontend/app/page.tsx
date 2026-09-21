"use client";
import { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";

const API_URL = "http://localhost:5000";

export default function Home() {
  const [threadId, setThreadId] = useState(null);
  const [explanation, setExplanation] = useState("");
  const [checkQuestion, setCheckQuestion] = useState("");
  const [feedback, setFeedback] = useState("");
  const [stage, setStage] = useState("");
  const [understanding, setUnderstanding] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(true);
  const [subtopics, setSubtopics] = useState([]);
  const [subtopicIndex, setSubtopicIndex] = useState(0);
  const [theme, setTheme] = useState("dark");

  const [selection, setSelection] = useState(null); // { text, x, y }
  const [askAnswer, setAskAnswer] = useState("");
  const [askLoading, setAskLoading] = useState(false);
  const contentRef = useRef(null);

  const isDark = theme === "dark";
  const colors = {
    bg: isDark ? "#0f1123" : "#f8fafc",
    headerBg: isDark ? "#12142b" : "#ffffff",
    sidebarBg: isDark ? "#12142b" : "#ffffff",
    border: isDark ? "#23253f" : "#e2e8f0",
    textPrimary: isDark ? "#f8fafc" : "#0f172a",
    textBody: isDark ? "#e2e8f0" : "#1e293b",
    textMuted: isDark ? "#94a3b8" : "#64748b",
    textFaint: isDark ? "#5b5d80" : "#94a3b8",
    accent: "#6366f1",
    accentLight: "#818cf8",
    cardBg: isDark ? "#1a1c38" : "#f1f5f9",
    cardBorder: isDark ? "#2a2c4a" : "#e2e8f0",
    progressTrack: isDark ? "#2a2c4a" : "#e2e8f0",
    navBorder: isDark ? "#3f4166" : "#cbd5e1",
    checkCardBg: "#f8fafc",
    checkCardText: "#0f172a",
  };

  useEffect(() => {
    startSession();
  }, []);

  function applyResult(data) {
    setStage(data.stage);
    setSubtopics(data.subtopics || []);
    setSubtopicIndex(data.subtopic_index ?? 0);
    setUnderstanding(data.understanding || "");

    if (data.stage === "awaiting_answer") {
      setExplanation(data.explanation || "");
      setCheckQuestion(data.check_question || "");
      setFeedback("");
    } else {
      setFeedback(data.response || "");
    }
  }

  async function startSession() {
    setLoading(true);
    const res = await fetch(`${API_URL}/start`, { method: "POST" });
    const data = await res.json();
    setThreadId(data.thread_id);
    applyResult(data);
    setLoading(false);
  }

  async function submitAnswer(value) {
    if (loading) return;
    setLoading(true);
    const res = await fetch(`${API_URL}/respond`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ thread_id: threadId, answer: value }),
    });
    const data = await res.json();
    applyResult(data);
    setAnswer("");
    setLoading(false);
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey && answer.trim()) {
      e.preventDefault();
      submitAnswer(answer);
    }
  }

  function handleTextSelect() {
    const sel = window.getSelection();
    const text = sel?.toString().trim();
    if (!text || !contentRef.current || !contentRef.current.contains(sel.anchorNode)) {
      return;
    }
    const rect = sel.getRangeAt(0).getBoundingClientRect();
    setAskAnswer("");
    setSelection({ text, x: rect.left + rect.width / 2, y: rect.top });
  }

  async function handleAskDoubt() {
    if (!selection) return;
    setAskLoading(true);
    const res = await fetch(`${API_URL}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ selected_text: selection.text, context: explanation }),
    });
    const data = await res.json();
    setAskAnswer(data.answer);
    setAskLoading(false);
  }

  useEffect(() => {
    function handleDocClick(e) {
      if (!e.target.closest("[data-ask-widget]")) {
        setSelection(null);
        setAskAnswer("");
      }
    }
    document.addEventListener("mousedown", handleDocClick);
    return () => document.removeEventListener("mousedown", handleDocClick);
  }, []);

  const verdictColors = { correct: "#22c55e", partial: "#eab308", wrong: "#ef4444" };
  const isDone = stage === "chapter_done";
  const isAwaitingAnswer = stage === "awaiting_answer";
  const isReadyForNext = stage === "ready_for_next";
  const total = subtopics.length || 1;
  const doneCount = subtopicIndex;

  const markdownComponents = {
    strong: (props) => <strong style={{ fontWeight: 700, color: colors.textPrimary }} {...props} />,
    p: (props) => <p style={{ margin: "0 0 16px 0" }} {...props} />,
    ul: (props) => <ul style={{ margin: "0 0 16px 0", paddingLeft: 22 }} {...props} />,
    ol: (props) => <ol style={{ margin: "0 0 16px 0", paddingLeft: 22 }} {...props} />,
    li: (props) => <li style={{ marginBottom: 6 }} {...props} />,
  };

  return (
    <div style={{ height: "100vh", overflow: "hidden", display: "flex", flexDirection: "column", background: colors.bg, fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" }}>
      <style jsx global>{`
        html, body { height: 100%; margin: 0; overflow: hidden; }
        ::-webkit-scrollbar { width: 8px; height: 8px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: ${colors.navBorder}; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: ${colors.accentLight}; }
        * { scrollbar-width: thin; scrollbar-color: ${colors.navBorder} transparent; }
      `}</style>
      {/* Top header */}
      <header
        style={{
          display: "flex", alignItems: "center", justifyContent: "space-between",
          padding: "16px 32px", background: colors.headerBg, borderBottom: `1px solid ${colors.border}`,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ width: 32, height: 32, borderRadius: 8, background: colors.accent, display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 700, color: "#fff", fontSize: 15 }}>
            S
          </div>
          <span style={{ color: colors.textPrimary, fontWeight: 700, fontSize: 16 }}>StudyBuddy</span>
          <span style={{ color: colors.accentLight, fontSize: 13, fontWeight: 600, marginLeft: 6 }}>CBSE Class 10 History</span>
        </div>
        <button
          onClick={() => setTheme(isDark ? "light" : "dark")}
          style={{
            width: 36, height: 36, borderRadius: "50%", border: `1px solid ${colors.border}`,
            background: "transparent", cursor: "pointer", fontSize: 16,
            display: "flex", alignItems: "center", justifyContent: "center",
          }}
        >
          {isDark ? "☀️" : "🌙"}
        </button>
      </header>

      <div style={{ display: "flex", flex: 1, minHeight: 0 }}>
        {/* Sidebar */}
        <aside
          style={{
            width: 300, flexShrink: 0, background: colors.sidebarBg, borderRight: `1px solid ${colors.border}`,
            padding: "28px 24px", overflowY: "auto",
          }}
        >
          <div style={{ color: colors.textMuted, fontSize: 12, marginBottom: 4 }}>Chapter 1</div>
          <div style={{ color: colors.textPrimary, fontSize: 19, fontWeight: 700, marginBottom: 16, lineHeight: 1.3 }}>
            The Rise of Nationalism in Europe
          </div>

          <div style={{ display: "flex", gap: 4, marginBottom: 8 }}>
            {subtopics.map((_, i) => (
              <div key={i} style={{ flex: 1, height: 4, borderRadius: 2, background: i < doneCount ? colors.accentLight : colors.progressTrack }} />
            ))}
          </div>
          <div style={{ color: colors.textFaint, fontSize: 12, marginBottom: 24 }}>
            {doneCount} of {total} sections done
          </div>

          <div>
            {subtopics.map((topic, i) => {
              const active = i === subtopicIndex;
              const done = i < subtopicIndex;
              return (
                <div key={i} style={{ display: "flex", gap: 12 }}>
                  <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                    <div
                      style={{
                        width: 24, height: 24, borderRadius: "50%", flexShrink: 0,
                        display: "flex", alignItems: "center", justifyContent: "center",
                        fontSize: 11, fontWeight: 700,
                        background: active ? colors.accent : done ? colors.accentLight : "transparent",
                        border: active || done ? "none" : `1px solid ${colors.navBorder}`,
                        color: active || done ? "#fff" : colors.textFaint,
                      }}
                    >
                      {done ? "✓" : i + 1}
                    </div>
                    {i < subtopics.length - 1 && <div style={{ width: 1, flex: 1, minHeight: 20, background: colors.border }} />}
                  </div>
                  <div style={{ paddingBottom: 20, fontSize: 13.5, lineHeight: 1.4, color: active ? colors.textPrimary : done ? colors.textMuted : colors.textFaint, fontWeight: active ? 600 : 400 }}>
                    {topic}
                  </div>
                </div>
              );
            })}
          </div>
        </aside>

        {/* Main content — centered, only this area scrolls */}
        <main style={{ flex: 1, display: "flex", justifyContent: "center", padding: "48px 56px", overflowY: "auto" }}>
          <div style={{ width: "100%", maxWidth: 900 }}>
            {isDone ? (
              <div style={{ color: colors.textPrimary }}>
                <h1 style={{ fontSize: 32, fontWeight: 700, marginBottom: 16 }}>Chapter complete 🎉</h1>
                <p style={{ color: colors.textMuted, fontSize: 16 }}>{feedback}</p>
              </div>
            ) : (
              <>
                <h1 style={{ color: colors.textPrimary, fontSize: 32, fontWeight: 700, lineHeight: 1.25, marginBottom: 28 }}>
                  {subtopics[subtopicIndex] || "Loading..."}
                </h1>

                <div
                  ref={contentRef}
                  onMouseUp={handleTextSelect}
                  style={{ color: colors.textBody, fontSize: 18, lineHeight: 1.8, userSelect: "text" }}
                >
                  {explanation ? <ReactMarkdown components={markdownComponents}>{explanation}</ReactMarkdown> : "Loading your lesson..."}
                </div>

                {selection && (
                  <div
                    data-ask-widget
                    style={{
                      position: "fixed",
                      left: selection.x,
                      top: selection.y - 44,
                      transform: "translateX(-50%)",
                      zIndex: 50,
                    }}
                  >
                    {!askAnswer && !askLoading && (
                      <button
                        onClick={handleAskDoubt}
                        style={{
                          background: colors.accent, color: "#fff", border: "none", borderRadius: 8,
                          padding: "8px 14px", fontSize: 13, fontWeight: 600, cursor: "pointer",
                          boxShadow: "0 8px 20px rgba(0,0,0,0.35)", whiteSpace: "nowrap",
                        }}
                      >
                        ? Ask about this
                      </button>
                    )}

                    {(askLoading || askAnswer) && (
                      <div
                        style={{
                          width: 320, background: colors.checkCardBg, color: colors.checkCardText,
                          borderRadius: 12, padding: "16px 18px", boxShadow: "0 16px 40px rgba(0,0,0,0.4)",
                          fontSize: 14, lineHeight: 1.6,
                        }}
                      >
                        <div style={{ color: colors.accent, fontWeight: 700, fontSize: 11.5, textTransform: "uppercase", letterSpacing: 0.5, marginBottom: 8 }}>
                          "{selection.text.length > 60 ? selection.text.slice(0, 60) + "…" : selection.text}"
                        </div>
                        {askLoading ? "Thinking..." : askAnswer}
                      </div>
                    )}
                  </div>
                )}

                {isReadyForNext && (
                  <div style={{ marginTop: 8, background: colors.cardBg, border: `1px solid ${colors.cardBorder}`, borderRadius: 14, padding: "20px 24px", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16 }}>
                    <div style={{ color: colors.textBody, fontSize: 15 }}>{feedback}</div>
                    <button
                      onClick={() => submitAnswer("continue")}
                      disabled={loading}
                      style={{ padding: "10px 22px", borderRadius: 10, border: "none", background: colors.accent, color: "#fff", fontWeight: 600, fontSize: 14, cursor: "pointer", flexShrink: 0 }}
                    >
                      {loading ? "..." : "Continue →"}
                    </button>
                  </div>
                )}

                {isAwaitingAnswer && (
                  <div style={{ marginTop: 8, background: colors.checkCardBg, borderRadius: 16, padding: "24px 28px", boxShadow: "0 20px 40px rgba(0,0,0,0.35)" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 6, color: colors.accent, fontSize: 12.5, fontWeight: 700, textTransform: "uppercase", letterSpacing: 0.5, marginBottom: 10 }}>
                      ? Comprehension check
                    </div>
                    <div style={{ color: colors.checkCardText, fontSize: 20, fontWeight: 700, lineHeight: 1.4, marginBottom: 18 }}>
                      {checkQuestion}
                    </div>
                    <div style={{ display: "flex", gap: 10, marginBottom: 10 }}>
                      <input
                        type="text"
                        value={answer}
                        onChange={(e) => setAnswer(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Type your answer..."
                        disabled={loading}
                        style={{ flex: 1, padding: "12px 16px", borderRadius: 10, border: "1px solid #cbd5e1", fontSize: 15, outline: "none", color: "#0f172a", background: "#fff", colorScheme: "light" }}
                      />
                      <button
                        onClick={() => submitAnswer(answer)}
                        disabled={loading || !answer.trim()}
                        style={{
                          padding: "12px 24px", borderRadius: 10, border: "none",
                          background: loading || !answer.trim() ? "#c7d2fe" : "#4f46e5",
                          color: "#fff", fontWeight: 600, fontSize: 15,
                          cursor: loading ? "default" : "pointer",
                        }}
                      >
                        {loading ? "..." : "Check answer"}
                      </button>
                    </div>
                    {understanding && (
                      <span style={{ background: verdictColors[understanding] || "#64748b", color: "#fff", padding: "3px 12px", borderRadius: 999, fontWeight: 600, fontSize: 12.5, textTransform: "capitalize" }}>
                        {understanding}
                      </span>
                    )}
                  </div>
                )}
              </>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
