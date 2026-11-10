import { useEffect, useRef, useState } from "react";
import "./App.css";
import ReactMarkdown from "react-markdown";
type ToolTrace = {
  tool: string;
  arguments: Record<string, unknown>;
};

type AgentResponse = {
  status: string;
  answer?: string;
  conversation_id?: number;
  confirmation_id?: string;
  tool?: string;
  arguments?: Record<string, unknown>;
  tool_trace?: ToolTrace[];
  message?: string;
};

type AgentMetrics = {
  total_requests: number;
  average_latency_seconds: number;
  average_tools_per_request: number;
  completion_rate: number;
};
type Conversation = {
  id: number;
  title: string;
  created_at: string;
};
type ChatMessage = {
  id: number;
  role: "user" | "assistant";
  content: string;
  toolTrace?: ToolTrace[];
  confirmation?: {
    confirmationId: string;
    tool: string;
    arguments?: Record<string, unknown>;
  };
};

function App() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [metrics, setMetrics] = useState<AgentMetrics | null>(null);
  const [metricsOpen, setMetricsOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const [conversationId, setConversationId] =
    useState<number | null>(null);
    useEffect(() => {
      loadMetrics();
      loadConversations();
    }, []);
  const [conversations, setConversations] =
    useState<Conversation[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);
  async function loadConversations() {
  try {
    const response = await fetch(
      "http://127.0.0.1:8000/conversations"
    );

    const data = await response.json();

    setConversations(data);
  } catch (error) {
    console.error(
      "Failed to load conversations:",
      error
    );
  }
}
async function openConversation(
  id: number
) {
  const response = await fetch(
    `http://127.0.0.1:8000/conversations/${id}/messages`
  );

  const data = await response.json();

  setConversationId(id);

  setMessages(
    data.map(
      (message: {
        id: number;
        role: "user" | "assistant";
        content: string;
      }) => ({
        id: message.id,
        role: message.role,
        content: message.content,
      })
    )
  );
}
function newChat() {
  setConversationId(null);
  setMessages([]);
  setMessage("");
}
  async function loadMetrics() {
    try {
      const result = await fetch("http://127.0.0.1:8000/analytics/agent");
      const data = await result.json();
      setMetrics(data);
    } catch (error) {
      console.error("Failed to load metrics:", error);
    }
  }

  async function sendMessage() {
    if (!message.trim() || loading) {
      return;
    }

    const userText = message.trim();

    const userMessage: ChatMessage = {
      id: Date.now(),
      role: "user",
      content: userText,
    };

    setMessages((prev) => [...prev, userMessage]);
    setMessage("");
    setLoading(true);

    try {
      const result = await fetch("http://127.0.0.1:8000/agent/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: userText,
          conversation_id: conversationId,
        }),
      });

      const data: AgentResponse = await result.json();
      if (
          data.conversation_id &&
          conversationId === null
        ) {
          setConversationId(
            data.conversation_id
          );
          await loadConversations();
        }
      const assistantMessage: ChatMessage = {
        id: Date.now() + 1,
        role: "assistant",
        content:
          data.status === "completed"
            ? data.answer ?? "No answer returned."
            : data.status === "confirmation_required"
            ? `Confirmation required for "${data.tool}".`
            : data.message ?? "Something went wrong.",
        toolTrace: data.tool_trace,
        confirmation:
          data.status === "confirmation_required" &&
          data.confirmation_id &&
          data.tool
            ? {
                confirmationId: data.confirmation_id,
                tool: data.tool,
                arguments: data.arguments,
              }
            : undefined,
      };

      setMessages((prev) => [...prev, assistantMessage]);
      await loadMetrics();
    } catch (error) {
      console.error(error);

      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          role: "assistant",
          content: "Failed to contact the backend.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  async function confirmAction(confirmationId: string) {
    setLoading(true);

    try {
      const result = await fetch("http://127.0.0.1:8000/agent/confirm", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          confirmation_id: confirmationId,
        }),
      });

      const data = await result.json();

      setMessages((prev) => [
        ...prev,
        {
          id: Date.now(),
          role: "assistant",
          content:
            data.status === "completed"
              ? `${data.tool} completed successfully.`
              : data.message ?? "Action failed.",
        },
      ]);

      await loadMetrics();
    } catch (error) {
      console.error(error);

      setMessages((prev) => [
        ...prev,
        {
          id: Date.now(),
          role: "assistant",
          content: "Failed to confirm the action.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

async function rejectAction(
  confirmationId: string,
  toolName: string
) {
  try {
    const response = await fetch(
      "http://127.0.0.1:8000/agent/reject",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          confirmation_id: confirmationId,
        }),
      }
    );

    const data = await response.json();

    setMessages((prev) => [
      ...prev,
      {
        id: Date.now(),
        role: "assistant",
        content:
          data.status === "rejected"
            ? `Okay, I won't proceed with ${toolName}.`
            : data.message ?? "Unable to reject the action.",
      },
    ]);
  } catch (error) {
    console.error(error);
  }
}

  function handleKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  }

 return (
  <div
    className="app-shell"
    onMouseMove={(event) => {
      document.documentElement.style.setProperty(
        "--mouse-x",
        `${event.clientX}px`
      );

      document.documentElement.style.setProperty(
        "--mouse-y",
        `${event.clientY}px`
      );
    }}
  >
    <div className="main-layout">
      <aside
      className={`sidebar ${sidebarOpen ? "open" : "closed"}`}
    >
      <div className="sidebar-top">
        <button
          className="sidebar-toggle"
          onClick={() => setSidebarOpen(!sidebarOpen)}
        >
          {sidebarOpen ? "←" : "→"}
        </button>

        {sidebarOpen && (
          <button
            className="new-chat-btn"
            onClick={newChat}
          >
            + New chat
          </button>
        )}
      </div>

      {sidebarOpen && (
        <div className="conversation-list">
          <div className="sidebar-section-title">
            Conversations
          </div>

          {conversations.map((conversation) => (
            <button
              key={conversation.id}
              className={`conversation-item ${
                conversationId === conversation.id
                  ? "active"
                  : ""
              }`}
              onClick={() =>
                openConversation(conversation.id)
              }
            >
              <span className="conversation-title">
                {conversation.title}
              </span>
            </button>
          ))}
        </div>
      )}
    </aside>

      <div className="main-content">
        <header className="topbar">
          <div>
            <h1>Luna</h1>
            <p className="subtitle">
              Hospitality intelligence and operations
            </p>
          </div>
        </header>

        <main className="chat-area">
          {messages.length === 0 && (
            <div className="empty-state">
              <div className="copilot-orb" />

              <h2>Operations Copilot</h2>

              <p>
                Ask about bookings, availability,
                pricing, policies or operational
                actions.
              </p>

              <div className="prompt-grid">
                <button
                  onClick={() =>
                    setMessage(
                      "Is apartment 1204 available from 2026-12-20 to 2026-12-23?"
                    )
                  }
                >
                  Check availability
                </button>

                <button
                  onClick={() =>
                    setMessage(
                      "How much would apartment 1204 cost for 3 nights?"
                    )
                  }
                >
                  Calculate a quote
                </button>

                <button
                  onClick={() =>
                    setMessage("Are pets allowed?")
                  }
                >
                  Ask about policies
                </button>

                <button
                  onClick={() =>
                    setMessage("Show me booking 2")
                  }
                >
                  Find a booking
                </button>
              </div>
            </div>
          )}

          {messages.map((chatMessage) => (
            <div
              key={chatMessage.id}
              className={`message-row ${
                chatMessage.role === "user"
                  ? "user-row"
                  : "Luna-row"
              }`}
            >
              <div
                className={`message-bubble ${
                  chatMessage.role === "user"
                    ? "user-bubble"
                    : "Luna-bubble"
                }`}
              >
                <div className="message-role">
                  {chatMessage.role === "user" ? "You" : "Luna"}
                </div>

                <div className="message-content">
                  <ReactMarkdown>
                    {chatMessage.content}
                  </ReactMarkdown>
                </div>

                {chatMessage.confirmation && (
                  <div className="confirmation-card">
                    <p>
                      Approval required for{" "}
                      <strong>
                        {
                          chatMessage.confirmation
                            .tool
                        }
                      </strong>
                    </p>

                    {chatMessage.confirmation
                      .arguments && (
                      <pre className="json-block">
                        {JSON.stringify(
                          chatMessage.confirmation
                            .arguments,
                          null,
                          2
                        )}
                      </pre>
                    )}

                    <div className="confirmation-actions">
                      <button
                        className="primary-btn"
                        onClick={() =>
                          confirmAction(
                            chatMessage.confirmation!
                              .confirmationId
                          )
                        }
                      >
                        Confirm
                      </button>

                      <button
                        className="secondary-btn"
                        onClick={() =>
                          rejectAction(
                            chatMessage.confirmation!.confirmationId,
                            chatMessage.confirmation!.tool
                          )
                        }
                      >
                        Reject
                      </button>
                    </div>
                  </div>
                )}

                {chatMessage.toolTrace &&
                  chatMessage.toolTrace.length >
                    0 && (
                    <details className="tool-trace">
                      <summary>
                        Tool trace
                      </summary>

                      <pre className="json-block">
                        {JSON.stringify(
                          chatMessage.toolTrace,
                          null,
                          2
                        )}
                      </pre>
                    </details>
                  )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="message-row assistant-row">
              <div className="assistant-bubble">
                <div className="typing-dots">
                  <span />
                  <span />
                  <span />
                </div>
              </div>
            </div>
          )} 

          <div ref={messagesEndRef} />
        </main>

        <aside
          className={`metrics-rail ${
            metricsOpen ? "open" : ""
          }`}
          onClick={() =>
            setMetricsOpen(!metricsOpen)
          }
        >
          <div className="metrics-label">
            Metrics
          </div>

          {metrics && (
            <div className="metrics-panel">
              <div className="metric-item">
                <span>Requests</span>
                <strong>
                  {metrics.total_requests}
                </strong>
              </div>

              <div className="metric-item">
                <span>Completion</span>
                <strong>
                  {metrics.completion_rate}%
                </strong>
              </div>

              <div className="metric-item">
                <span>Avg latency</span>
                <strong>
                  {
                    metrics.average_latency_seconds
                  }
                  s
                </strong>
              </div>

              <div className="metric-item">
                <span>
                  Tools / request
                </span>
                <strong>
                  {
                    metrics.average_tools_per_request
                  }
                </strong>
              </div>
            </div>
          )}
        </aside>

        <footer>
          <div className="composer">
            <textarea
              value={message}
              onChange={(event) => {
                setMessage(
                  event.target.value
                );

                event.target.style.height =
                  "auto";

                event.target.style.height =
                  `${Math.min(
                    event.target.scrollHeight,
                    180
                  )}px`;
              }}
              onKeyDown={handleKeyDown}
              placeholder="Message AI Operations Copilot..."
              rows={1}
            />

            <button
              onClick={sendMessage}
              disabled={
                loading ||
                !message.trim()
              }
            >
              ↑
            </button>
          </div>
        </footer>
      </div>
    </div>
  </div>
);
}

export default App;