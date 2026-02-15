import "./styles/styles.css";
import { useDispatch, useSelector } from "react-redux";
import { useEffect, useState } from "react";
import { setIsLoggedIn, setUser, setApiKey } from "./redux/reducers/userSlice.js";
import { BrowserRouter, Route, Routes, Navigate, useParams } from "react-router-dom";
import axios from "axios";

import ChatPage from "./chat/ChatInterface.jsx";
import ChatIframe from "./chat/ChatIframe.jsx";
import Layout from "./layouts/Layout.jsx";
import CopilotChatInterface from "./chat/CopilotChatInterface.jsx";

function DomainChatRouter() {
  const { domain } = useParams();

  // ONLY Ask Finance goes to Copilot
  if (domain === "ask_finance") {
    return <CopilotChatInterface />;
  }

  // Everything else goes to LangGraph backend
  return <ChatPage />;
}

function App() {
  const { isLoggedIn, userObj } = useSelector((state) => state.user);
  const dispatch = useDispatch();
  const [tierData, setTierData] = useState(null);
  const [isLoadingTier, setIsLoadingTier] = useState(false);

  const fetchTier = async () => {
    setIsLoadingTier(true);
    try {
      const token = localStorage.getItem("authToken");
      // NOTE: leaving your tier logic as-is (no need to change here)
    } catch (error) {
      console.error("Error fetching tier:", error);
    } finally {
      setIsLoadingTier(false);
    }
  };

  useEffect(() => {
    const token = localStorage.getItem("authToken");
    if (token) dispatch(setIsLoggedIn(true));

    const userRole = localStorage.getItem("role");
    if (userRole) dispatch(setUser({ ...userObj, role: userRole }));

    fetchTier();
  }, []);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/ask_fiannce/chat" replace />} />
        <Route path=":domain" element={<Layout />}>
          <Route path="chat" element={<DomainChatRouter />} />
          <Route path="iframe" element={<ChatIframe />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
