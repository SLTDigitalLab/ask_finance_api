import React from "react";
import EmbryoLogo from "../assets/embryo-removebg.png";

const COPILOT_URL =
  "https://copilotstudio.microsoft.com/environments/Default-534253fc-dfb6-462f-b5ca-cbe81939f5ee/bots/crad5_agent2/webchat?__version__=2&enableFileAttachment=true";

export default function AskEnterpriseChat() {
  return (
    <>
      {/* ✅ Embedded CSS */}
      <style>{`
        .enterprise-page {
          min-height: 100vh;
          display: flex;
          flex-direction: column;
          color: white;
          background:
            radial-gradient(ellipse at top left, rgba(59,130,246,0.25) 0%, transparent 50%),
            radial-gradient(ellipse at top right, rgba(37,99,235,0.35) 0%, transparent 50%),
            radial-gradient(ellipse at bottom left, rgba(14,165,233,0.22) 0%, transparent 50%),
            radial-gradient(ellipse at bottom right, rgba(30,64,175,0.45) 0%, transparent 50%),
            linear-gradient(
              135deg,
              #0b1b3a 0%,
              #0a2a66 15%,
              #0b3aa5 35%,
              #06224d 60%,
              #031227 100%
            );
        }

        .enterprise-container {
          flex: 1;
          max-width: 1200px;
          width: 100%;
          margin: 0 auto;
          padding: 28px 16px;
          text-align: center;
        }

        /* ===== Pure white title ===== */
        .enterprise-title {
          margin: 0;
          font-size: 52px;
          font-weight: 900;
          letter-spacing: 0.04em;
          color: #ffffff;
          text-shadow:
            0 3px 14px rgba(0,0,0,0.35),
            0 1px 2px rgba(0,0,0,0.4);
        }

        .enterprise-subtitle {
          margin-top: 6px;
          font-size: 14px;
          font-weight: 500;
          letter-spacing: 0.25em;
          text-transform: uppercase;
          color: rgba(255,255,255,0.75);
        }

        .enterprise-card {
          margin-top: 22px;
          background: rgba(255,255,255,0.95);
          border-radius: 20px;
          height: 520px;
          overflow: hidden;
          box-shadow:
            0 32px 90px rgba(0,0,0,0.45),
            0 0 0 1px rgba(255,255,255,0.35) inset;
        }

        .enterprise-iframe {
          width: 100%;
          height: 100%;
          border: none;
        }

        /* ===== Footer ~20% bigger ===== */
        .enterprise-footer {
          padding: 14px 0; /* was 12px */
          background: rgba(0,0,0,0.25);
          border-top: 1px solid rgba(255,255,255,0.12);
          display: flex;
          justify-content: center;
          align-items: center;
          gap: 12px; /* was 10px */
          opacity: 0.9;
        }

        .enterprise-footer-text {
          font-size: 14px; /* was 12px */
          letter-spacing: 1px;
          text-transform: uppercase;
        }

        .enterprise-footer-logo {
          height: 38px; /* was 32px */
          width: auto;
          opacity: 0.95;
        }
      `}</style>

      {/* ✅ Page */}
      <div className="enterprise-page">
        <div className="enterprise-container">
          <h1 className="enterprise-title">AIye</h1>
          <div className="enterprise-subtitle">by SLTM Enterprise</div>

          <div className="enterprise-card">
            <iframe
              title="AIye Copilot"
              src={COPILOT_URL}
              className="enterprise-iframe"
              allow="microphone; camera"
            />
          </div>
        </div>

        {/* Footer */}
        <div className="enterprise-footer">
          <span className="enterprise-footer-text">Powered By</span>
          <img
            src={EmbryoLogo}
            alt="THEEMBRYO"
            className="enterprise-footer-logo"
          />
        </div>
      </div>
    </>
  );
}