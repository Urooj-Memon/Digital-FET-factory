"use client";

import React, { useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

interface FormData {
  name: string;
  email: string;
  subject: string;
  category: string;
  priority: string;
  message: string;
}

interface TicketInfo {
  ticket_id: string;
  status: string;
  messages: Array<{ role: string; content: string; created_at: string }>;
}

const CATEGORIES = [
  { value: "technical", label: "Technical Issue" },
  { value: "billing", label: "Billing & Payments" },
  { value: "account", label: "Account Management" },
  { value: "feedback", label: "Feedback & Suggestions" },
  { value: "general", label: "General Inquiry" },
];

const PRIORITIES = [
  { value: "low", label: "Low - No rush" },
  { value: "medium", label: "Medium - Normal" },
  { value: "high", label: "High - Important" },
  { value: "urgent", label: "Urgent - Critical" },
];

export default function SupportForm() {
  const [formData, setFormData] = useState<FormData>({
    name: "",
    email: "",
    subject: "",
    category: "general",
    priority: "medium",
    message: "",
  });
  const [status, setStatus] = useState<"idle" | "submitting" | "success" | "error">("idle");
  const [errorMessage, setErrorMessage] = useState("");
  const [ticketId, setTicketId] = useState("");
  const [ticketInfo, setTicketInfo] = useState<TicketInfo | null>(null);
  const [checkingTicket, setCheckingTicket] = useState(false);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus("submitting");
    setErrorMessage("");

    try {
      const res = await fetch(`${API_BASE}/api/support/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to submit request");
      }

      const data = await res.json();
      setStatus("success");
      if (data.ticket_id) setTicketId(data.ticket_id);
    } catch (err: any) {
      setStatus("error");
      setErrorMessage(err.message || "Something went wrong. Please try again.");
    }
  };

  const checkTicketStatus = async () => {
    if (!ticketId) return;
    setCheckingTicket(true);
    try {
      const res = await fetch(`${API_BASE}/api/support/ticket/${ticketId}`);
      if (res.ok) {
        const data = await res.json();
        setTicketInfo(data);
      }
    } catch {
      // Ticket may not be ready yet
    }
    setCheckingTicket(false);
  };

  const resetForm = () => {
    setFormData({ name: "", email: "", subject: "", category: "general", priority: "medium", message: "" });
    setStatus("idle");
    setErrorMessage("");
    setTicketId("");
    setTicketInfo(null);
  };

  // --- Success State ---
  if (status === "success") {
    return (
      <div className="card">
        <div className="success-container">
          <div className="success-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M22 11.08V12a10 10 0 11-5.93-9.14" />
              <path d="M22 4L12 14.01l-3-3" />
            </svg>
          </div>
          <h2>Request Submitted!</h2>
          <p className="subtitle">
            Your support request has been received. Our AI assistant is analyzing
            your issue and will respond shortly.
          </p>

          {ticketId && (
            <div>
              <div className="ticket-id-badge">
                Ticket ID: <strong>{ticketId}</strong>
              </div>
              <div style={{ marginTop: 16 }}>
                <button
                  onClick={checkTicketStatus}
                  disabled={checkingTicket}
                  className="btn-outline"
                >
                  {checkingTicket ? (
                    <>
                      <span className="spinner" style={{ borderColor: "rgba(79,70,229,0.3)", borderTopColor: "#4f46e5" }}></span>
                      Checking...
                    </>
                  ) : (
                    <>
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>
                      Check Ticket Status
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

          {ticketInfo && (
            <div className="ticket-info">
              <span className={`status-badge status-${ticketInfo.status}`}>
                {ticketInfo.status.charAt(0).toUpperCase() + ticketInfo.status.slice(1)}
              </span>
              {ticketInfo.messages.map((msg, i) => (
                <div key={i} className="ticket-message">
                  <div className="role">
                    {msg.role === "agent" ? "AI Support" : "You"}
                  </div>
                  {msg.content}
                </div>
              ))}
            </div>
          )}

          <div style={{ marginTop: 24 }}>
            <button onClick={resetForm} className="btn-submit">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 5v14M5 12h14"/></svg>
              Submit Another Request
            </button>
          </div>
        </div>
      </div>
    );
  }

  // --- Form State ---
  return (
    <div className="card">
      <div className="card-header">
        <div className="card-header-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
          </svg>
        </div>
        <div>
          <h2>Submit a Support Request</h2>
          <p>Fill in the details below and we'll get back to you ASAP</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="card-body">
        {status === "error" && (
          <div className="alert-error">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><path d="M15 9l-6 6M9 9l6 6"/></svg>
            {errorMessage}
          </div>
        )}

        {/* Name & Email row */}
        <div className="form-row">
          <div className="form-group">
            <label className="form-label" htmlFor="name">
              Full Name <span className="required">*</span>
            </label>
            <input
              className="form-input"
              id="name"
              name="name"
              type="text"
              required
              value={formData.name}
              onChange={handleChange}
              placeholder="John Doe"
            />
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="email">
              Email Address <span className="required">*</span>
            </label>
            <input
              className="form-input"
              id="email"
              name="email"
              type="email"
              required
              value={formData.email}
              onChange={handleChange}
              placeholder="john@example.com"
            />
          </div>
        </div>

        {/* Subject */}
        <div className="form-group">
          <label className="form-label" htmlFor="subject">
            Subject <span className="required">*</span>
          </label>
          <input
            className="form-input"
            id="subject"
            name="subject"
            type="text"
            required
            value={formData.subject}
            onChange={handleChange}
            placeholder="Brief description of your issue"
          />
        </div>

        {/* Category & Priority row */}
        <div className="form-row">
          <div className="form-group">
            <label className="form-label" htmlFor="category">Category</label>
            <select
              className="form-select"
              id="category"
              name="category"
              value={formData.category}
              onChange={handleChange}
            >
              {CATEGORIES.map((c) => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="priority">Priority</label>
            <select
              className="form-select"
              id="priority"
              name="priority"
              value={formData.priority}
              onChange={handleChange}
            >
              {PRIORITIES.map((p) => (
                <option key={p.value} value={p.value}>{p.label}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Message */}
        <div className="form-group">
          <label className="form-label" htmlFor="message">
            Message <span className="required">*</span>
          </label>
          <textarea
            className="form-textarea"
            id="message"
            name="message"
            required
            minLength={10}
            rows={5}
            value={formData.message}
            onChange={handleChange}
            placeholder="Please describe your issue in detail so we can help you faster..."
          />
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={status === "submitting"}
          className="btn-submit"
        >
          {status === "submitting" ? (
            <>
              <span className="spinner"></span>
              Submitting...
            </>
          ) : (
            <>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/></svg>
              Submit Support Request
            </>
          )}
        </button>
      </form>
    </div>
  );
}
