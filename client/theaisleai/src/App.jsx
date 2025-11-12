import "./styles/styles.css";
// layouts and pages
import { useDispatch, useSelector } from "react-redux";
import { useEffect, useState } from "react";
import {
  setIsLoggedIn,
  setUser,
  setApiKey,
} from "./redux/reducers/userSlice.js";
import { BrowserRouter, Route, Routes, Navigate } from "react-router-dom";
import axios from "axios";
import ChatPage from "./chat/ChatInterface.jsx";
import ChatIframe from "./chat/ChatIframe.jsx";
import Layout from "./layouts/Layout.jsx";

function App() {
  const { isLoggedIn, userObj } = useSelector((state) => state.user);
  const dispatch = useDispatch();
  const [tierData, setTierData] = useState(null); // Store fetched tier data
  // const [apiKey, setApikey] = useState(null);
  const [isLoadingTier, setIsLoadingTier] = useState(false); // Track loading state

  const fetchTier = async () => {
    setIsLoadingTier(true); // Set loading state to indicate ongoing fetch

    try {
      const token = localStorage.getItem("authToken");
      const tierResponse = await axios.get(TIER.GET_TIER, {
        headers: {
          Authorization: "Bearer " + token,
        },
      });
      // console.log(apiKeyResponse.data.result.api_key)
      // setApikey(apiKeyResponse.data.result.api_key)
      setTierData(tierResponse.data.result.tier.tier); // Update state with fetched data
    } catch (error) {
      console.error("Error fetching tier:", error); // Handle errors gracefully
    } finally {
      setIsLoadingTier(false); // Reset loading state after fetch
    }
  };
  useEffect(() => {
    const token = localStorage.getItem("authToken");
    if (token) {
      dispatch(setIsLoggedIn(true));
    }
    const userRole = localStorage.getItem("role");
    if (userRole) {
      dispatch(setUser({ ...userObj, role: userRole }));
    }
    // localStorage.setItem("apiKey",apiKey)
    // dispatch(setApiKey({apiKey}))
    fetchTier();
  }, []);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/chat" replace />} />
        <Route path=":domain" element={<Layout />}>
          <Route path="chat" element={<ChatPage />} />
          <Route path="iframe" element={<ChatIframe />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
