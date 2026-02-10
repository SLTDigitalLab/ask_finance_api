import React, { useEffect, useRef, useState } from "react";
import { Box, Text, Spinner } from "@chakra-ui/react";

const WEBCHAT_CDN = "https://cdn.botframework.com/botframework-webchat/latest/webchat.js";

export default function CopilotChat() {
  const webchatRef = useRef(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  useEffect(() => {
    let cancelled = false;

    const loadWebChat = () =>
      new Promise((resolve, reject) => {
        if (window.WebChat) return resolve(window.WebChat);

        const s = document.createElement("script");
        s.src = WEBCHAT_CDN;
        s.async = true;
        s.onload = () => resolve(window.WebChat);
        s.onerror = () => reject(new Error("Failed to load BotFramework WebChat script"));
        document.body.appendChild(s);
      });

    (async () => {
      try {
        const WebChat = await loadWebChat();

        // IMPORTANT:
        // Dev: Vite proxy will forward /copilot -> http://localhost:5003
        // Prod: Nginx will proxy /copilot -> copilot backend container
        const tokenUrl = import.meta.env.VITE_COPILOT_TOKEN_URL || "/copilot/get_token";

        const res = await fetch(tokenUrl, {
          method: "GET",
          headers: { "Content-Type": "application/json" },
          cache: "no-store",
        });

        if (!res.ok) throw new Error(`Token fetch failed: ${res.status}`);
        const { token } = await res.json();
        if (!token) throw new Error("No token returned from server");

        if (cancelled) return;

        const directLine = WebChat.createDirectLine({ token });

        WebChat.renderWebChat(
          {
            directLine,
            userID: "user_" + Math.random().toString(36).slice(2),
            locale: "en-US",
          },
          webchatRef.current
        );

        setLoading(false);
      } catch (e) {
        if (cancelled) return;
        setErr(e.message || String(e));
        setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <Box w="100%" h="calc(100vh - 120px)" display="flex" flexDirection="column">
      {loading && (
        <Box p={4} display="flex" alignItems="center" gap={3}>
          <Spinner />
          <Text>Loading Copilot…</Text>
        </Box>
      )}

      {err && (
        <Box p={4}>
          <Text color="red.400">Copilot error: {err}</Text>
        </Box>
      )}

      <Box
        ref={webchatRef}
        flex="1"
        minH="400px"
        borderRadius="12px"
        overflow="hidden"
      />
    </Box>
  );
}
