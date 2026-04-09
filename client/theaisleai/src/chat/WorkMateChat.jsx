import React from "react";
import EmbryoLogo from "../assets/embryo-removebg.png";
import AIBot from "../assets/ai-bot.png";

const COPILOT_URL =
  "https://copilotstudio.microsoft.com/environments/Default-534253fc-dfb6-462f-b5ca-cbe81939f5ee/bots/crad5_agentPsQk6Y/webchat?__version__=2&enableFileAttachment=true";

export default function WorkMateChat() {
  return (
    <>
      <style>{`
        .workmate-page {
          min-height: 100svh;
          display: flex;
          flex-direction: column;
          color: white;
        }

        .workmate-container {
          flex: 1;
          max-width: 1200px;
          width: 100%;
          margin: 0 auto;
          padding: 28px 16px;
          text-align: center;
        }

        .workmate-title {
          margin: 0;
          font-size: 48px;
          font-weight: 900;
          letter-spacing: 0.05em;
          color: #ffffff;
        }

        .workmate-subtitle {
          margin-top: 6px;
          font-size: 14px;
          letter-spacing: 0.25em;
          color: rgba(255,255,255,0.8);
        }

        .workmate-card {
          margin-top: 22px;
          background: rgba(255,255,255,0.95);
          border-radius: 20px;
          height: min(580px, 75vh);
          overflow: hidden;
          box-shadow:
            0 30px 80px rgba(0,0,0,0.4),
            0 0 0 1px rgba(255,255,255,0.3) inset;
        }

        .workmate-iframe {
          width: 100%;
          height: 100%;
          border: none;
        }

        .workmate-header {
          position: relative;
          text-align: center;
        }

        .workmate-bot {
          position: absolute;
          left: calc(50% + 160px);
          top: -10px;
          height: 90px;
          animation: floatBot 4s ease-in-out infinite;
        }

        @keyframes floatBot {
          0% { transform: translateY(0px); }
          50% { transform: translateY(-6px); }
          100% { transform: translateY(0px); }
        }

        .workmate-footer {
          padding: 14px 0;
          background: rgba(0,0,0,0.25);
          display: flex;
          justify-content: center;
          align-items: center;
          gap: 12px;
        }

        .workmate-footer-logo {
          height: 36px;
        }

       body {
        margin: 0;
        min-height: 100vh;

        background:
            radial-gradient(circle at 15% 20%, rgba(34,197,94,0.25), transparent 40%),   /* green */
            radial-gradient(circle at 85% 15%, rgba(59,130,246,0.30), transparent 40%),  /* blue */
            radial-gradient(circle at 20% 85%, rgba(16,185,129,0.25), transparent 40%),  /* teal */
            radial-gradient(circle at 80% 80%, rgba(37,99,235,0.25), transparent 40%),   /* deep blue */
            linear-gradient(135deg, #022c22, #064e3b, #0b3aa5, #06224d, #021e3a);

        background-attachment: fixed;
        }

        @media (max-width: 768px) {
          .workmate-bot {
            position: static;
            margin-top: 10px;
            height: 70px;
          }
        }

        @media (max-width: 768px) {
            .workmate-header {
                display: flex;
                flex-direction: column;
                align-items: center;   
            }

            .workmate-bot {
                position: static;
                margin-top: 12px;
                height: 70px;

                display: block;       
                margin-left: auto;
                margin-right: auto;
            }
        }
      `}</style>

      <div className="workmate-page">
        <div className="workmate-container">

          <div className="workmate-header">
            <div>
              <h1 className="workmate-title">WorkMate AI</h1>
              <div className="workmate-subtitle">
                By SLTMobitel
              </div>
            </div>

            <img src={AIBot} alt="AI Bot" className="workmate-bot" />
          </div>

          <div className="workmate-card">
            <iframe
              title="WorkMate AI"
              src={COPILOT_URL}
              className="workmate-iframe"
              allow="microphone; camera"
            />
          </div>
        </div>

        <div className="workmate-footer">
          <span>Powered By</span>
          <img src={EmbryoLogo} alt="logo" className="workmate-footer-logo" />
        </div>
      </div>
    </>
  );
}