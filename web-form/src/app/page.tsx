"use client";

import SupportForm from "./components/SupportForm";

export default function Home() {
  return (
    <div className="page-wrapper">
      {/* Header */}
      <div className="header">
        <div className="header-logo">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 2L2 7l10 5 10-5-10-5z" />
            <path d="M2 17l10 5 10-5" />
            <path d="M2 12l10 5 10-5" />
          </svg>
        </div>
        <h1>TechCorp Support Center</h1>
        <p>
          Get instant help with TechFlow. Our AI assistant is available 24/7
          across all channels.
        </p>

        {/* Channel badges */}
        <div className="channels">
          <span className="channel-badge">
            <span className="dot dot-green"></span>
            Email Support
          </span>
          <span className="channel-badge">
            <span className="dot dot-blue"></span>
            WhatsApp
          </span>
          <span className="channel-badge">
            <span className="dot dot-yellow"></span>
            Web Form
          </span>
        </div>
      </div>

      {/* Form Card */}
      <SupportForm />

      {/* Feature strip */}
      <div className="features">
        <div className="feature">
          <div className="feature-icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
          </div>
          Avg. response &lt; 30s
        </div>
        <div className="feature">
          <div className="feature-icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><path d="M22 4L12 14.01l-3-3"/></svg>
          </div>
          AI-Powered Resolution
        </div>
        <div className="feature">
          <div className="feature-icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg>
          </div>
          Human Escalation Available
        </div>
      </div>

      {/* Footer */}
      <div className="footer">
        Powered by TechCorp Digital FTE &bull; AI Customer Success Agent
      </div>
    </div>
  );
}
