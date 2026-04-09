import React, { useEffect, useState, useRef } from "react";
import {
  Box,
  Button,
  Drawer,
  Flex,
  Image,
  Input,
  Text,
  useToast,
  VStack,
  HStack,
  useColorModeValue,
  useDisclosure,
  DrawerOverlay,
  DrawerContent,
  DrawerCloseButton,
  DrawerHeader,
  DrawerBody,
  useColorMode,
  Spinner,
} from "@chakra-ui/react";

import ReactMarkdown from "react-markdown";
import FaceIcon from "@mui/icons-material/Face";
import SmartToyIcon from "@mui/icons-material/SmartToy";
import SendIcon from "@mui/icons-material/Send";
import { useParams } from "react-router-dom";
import { DirectLine } from "botframework-directlinejs";


// IMPORTANT:
// This component uses the SAME UI as ChatInterface,
// but sends/receives messages via DirectLine (Copilot),
// using token fetched from Flask: /copilot/get_token (proxied in dev)

function CopilotChatInterface() {
  const { colorMode } = useColorMode();
  const isDarkMode = colorMode === "dark";

  const bgColor = useColorModeValue("gray.50", "gray.800");
  const textColor = useColorModeValue("gray.800", "white");
  const cardBgColor = useColorModeValue("white", "gray.700");
  const inputBgColor = useColorModeValue("white", "gray.600");
  const hoverBgColor = useColorModeValue("gray.100", "gray.600");

  const toast = useToast();
  const { isOpen, onOpen, onClose } = useDisclosure();
  const btnRef = React.useRef();

  //const { domain } = useParams();
  const domainFromPath = (window.location.pathname.split("/")[1] || "").toLowerCase();
  const domain = domainFromPath;


  // const normalized = (domain || "").toLowerCase();

  // const isFinance =
  //   normalized === "ask_finance" ||
  //   normalized === "ask_fiannce" ||
  //   normalized === "ask_fianance";

  // if (!isFinance) return null;
  
  const [isLoading, setIsLoading] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);
  const [question, setQuestion] = useState("");

  // Reference UI (kept to preserve same UI; Copilot won’t use these)
  const [pdf, setPdf] = useState(null);
  const [page, setPage] = useState(0);
  const [refHeader, setRefHeader] = useState("");

  // DirectLine
  const directLineRef = useRef(null);
  const activitySubRef = useRef(null);
  const [copilotReady, setCopilotReady] = useState(false);

  // Fetch token + init DirectLine on mount
  useEffect(() => {

    //if (!isFinance) return;
    let cancelled = false;

    const initCopilot = async () => {
      try {
        // Dev: Vite proxy forwards /copilot -> http://localhost:5003
        // Prod: Nginx should proxy /copilot -> copilot backend
        const tokenUrl =
          import.meta.env.VITE_COPILOT_TOKEN_URL || "/copilot/get_token";

        //const res = await fetch(tokenUrl, { cache: "no-store" });
        const res = await fetch(`${tokenUrl}?domain=${encodeURIComponent(domain)}`, { cache: "no-store" });

        if (!res.ok) {
          throw new Error(`Token fetch failed (${res.status}) from ${tokenUrl}`);
        }

        const data = await res.json();
        if (!data?.token) {
          throw new Error("No token received from /copilot/get_token");
        }

        if (cancelled) return;

        const dl = new DirectLine({ token: data.token });
        directLineRef.current = dl;

        // Subscribe to incoming activities (bot messages)
        activitySubRef.current = dl.activity$.subscribe((activity) => {
          if (activity?.type !== "message") return;
          if (activity?.from?.role !== "bot") return;

          const botText =
            activity.text ||
            (Array.isArray(activity.attachments) && activity.attachments.length
              ? "I sent you a message with attachments."
              : "");

          setChatHistory((prev) => [
            ...prev,
            {
              role: "bot",
              message: botText,
              hasReference: false,
              referenceDocuments: [],
            },
          ]);

          // stop spinner when first bot reply comes back
          setIsLoading(false);
        });

        setCopilotReady(true);

        toast({
          title: "Copilot connected",
          description: "You can start chatting now.",
          status: "success",
          duration: 2000,
          isClosable: true,
        });
      } catch (e) {
        console.error(e);
        setCopilotReady(false);
        toast({
          title: "Copilot setup failed",
          description: e?.message || String(e),
          status: "error",
          duration: 5000,
          isClosable: true,
        });
      }
    };

    initCopilot();

    return () => {
      cancelled = true;
      try {
        if (activitySubRef.current) {
          activitySubRef.current.unsubscribe();
          activitySubRef.current = null;
        }
        if (directLineRef.current) {
          directLineRef.current.end();
          directLineRef.current = null;
        }
      } catch {}
    };
  }, [toast, domain]);


  // Send message to Copilot
  const handleSubmit = async (e) => {
    e.preventDefault();

    const text = (question || "").trim();
    if (!text) return;

    if (!copilotReady || !directLineRef.current) {
      toast({
        title: "Copilot not ready",
        description: "Token/connection not initialized yet.",
        status: "warning",
        duration: 2500,
        isClosable: true,
      });
      return;
    }

    try {
      setIsLoading(true);

      // Add user message immediately
      setChatHistory((prev) => [...prev, { role: "user", message: text }]);

      // Clear input
      setQuestion("");

      // Send to DirectLine
      await directLineRef.current
        .postActivity({
          type: "message",
          text,
          from: { id: "user", role: "user", name: "User" },
          channelData: {
            // optional: include domain for your own tracking if needed
            domain,
          },
        })
        .toPromise();

      // Keep spinner true until bot responds (activity subscription will turn it off)
    } catch (error) {
      console.error("Copilot send error:", error);
      setIsLoading(false);
      toast({
        title: "An error occurred",
        description: error?.message || String(error),
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    }
  };

  // ReferenceButton component (kept for UI compatibility)
  const ReferenceButton = ({ document, onedriveUrl, onClick }) => {
    const displayName =
      document.name.length > 25
        ? `${document.name.substring(0, 22)}...${document.name.split(".").pop()}`
        : document.name;

    const tooltipText = `Click to open: ${document.name}\n${
      onedriveUrl ? `URL: ${onedriveUrl}` : "URL: Will open shared folder"
    }`;

    const handleClick = () => {
      if (onedriveUrl) onClick(document.name, onedriveUrl);
      else onClick(document.name);
    };

    return (
      <Button
        size="xs"
        colorScheme="blue"
        variant="outline"
        onClick={handleClick}
        mt={2}
        mr={2}
        title={tooltipText}
        maxW="200px"
        overflow="hidden"
        textOverflow="ellipsis"
        whiteSpace="nowrap"
        _hover={{
          transform: "translateY(-2px)",
          boxShadow: "md",
          bg: useColorModeValue("blue.50", "blue.900"),
        }}
        transition="all 0.2s"
        leftIcon={<Box as="span" fontSize="sm">📄</Box>}
      >
        {displayName}
      </Button>
    );
  };

  // Kept — but Copilot path won’t call these.
  const handleReferenceClick = async (documentName, onedriveUrl = null) => {
    toast({
      title: "References not available in Copilot mode",
      description:
        "Copilot messages don’t include Ask Finance reference documents.",
      status: "info",
      duration: 3000,
      isClosable: true,
    });
  };

  return (
    <Flex direction="column" h="100%" minH="0">
      {/* Centered main container, same width as before (85%) */}
      <Box
        h="100%"
        w={{ base: "100%", md: "85%" }}
        maxW="1400px"
        pt={0}
        mt={0}
        pb={0}
        display="flex"
        mx="auto"
        position="relative"
        bottom="5px"
      >
        <VStack spacing={2} p={4} pb={0} flexGrow={1}>
          <VStack w="full" h="65vh" alignItems="left" p={3} overflowY="auto">
            {chatHistory.length === 0 ? (
              <VStack
                spacing={1}
                align="center"
                p={5}
                borderRadius="15"
                boxShadow="xl"
                flexGrow={100}
              >
                <Image
                  src="/12.png"
                  alt="Logo"
                  boxSize="300px"
                  mb={-10}
                  opacity="70%"
                />
                <Text fontSize="2xl" fontWeight="bold" color="gray.600">
                  How can I assist you today?
                </Text>
                {/* <Text fontSize="sm" color="gray.500">
                  (Copilot mode)
                </Text> */}
                {!copilotReady && (
                  <HStack pt={3}>
                    <Spinner size="sm" />
                    <Text fontSize="sm" color="gray.500">
                      Connecting to Copilot…
                    </Text>
                  </HStack>
                )}
              </VStack>
            ) : null}

            {chatHistory.map((entry, index) => (
              <VStack
                key={index}
                align={entry.role === "user" ? "end" : "start"}
                spacing={1}
                p={5}
                backgroundColor={
                  entry.role === "user"
                    ? useColorModeValue("#edede9", "gray.700")
                    : useColorModeValue("gray.100", "gray.900")
                }
                borderRadius="15"
                w="full"
              >
                <Text fontWeight="bold">
                  {entry.role === "user" ? <FaceIcon /> : <SmartToyIcon />}
                </Text>

                {entry.message === "Generating response..." ? (
                  <HStack>
                    <Text>Generating response</Text>
                    <Spinner
                      size="sm"
                      thickness="3px"
                      speed="0.5s"
                      color="blue.500"
                    />
                  </HStack>
                ) : (
                  <>
                    <ReactMarkdown>
                      {(entry.message || "").replace(/\[REFERENCE:.*?\]/g, "")}
                    </ReactMarkdown>

                    {/* kept but will never show in Copilot mode */}
                    {entry.hasReference &&
                      entry.referenceDocuments &&
                      entry.referenceDocuments.length > 0 && (
                        <HStack wrap="wrap" mt={2}>
                          <Text
                            fontSize="sm"
                            fontWeight="bold"
                            mr={2}
                            color={useColorModeValue(
                              "blue.700",
                              "blue.300"
                            )}
                          >
                            📚 References:
                          </Text>
                          {entry.referenceDocuments.map((doc, idx) => {
                            if (!doc.name || doc.name.trim() === "") return null;

                            return (
                              <ReferenceButton
                                key={idx}
                                document={doc}
                                onedriveUrl={doc.preview_url || doc.direct_link}
                                onClick={handleReferenceClick}
                              />
                            );
                          })}
                        </HStack>
                      )}
                  </>
                )}

                {Array.isArray(entry.image) &&
                  entry.image.length > 0 &&
                  entry.image.map((img, idx) => (
                    <Image key={idx} rounded="md" src={img} alt="Image" />
                  ))}

                {Array.isArray(entry.file) && entry.file.length > 0 && (
                  <>
                    <Drawer
                      isOpen={isOpen}
                      placement="right"
                      onClose={onClose}
                      finalFocusRef={btnRef}
                      size="xl"
                    >
                      <DrawerOverlay />
                      <DrawerContent>
                        <DrawerCloseButton />
                        <DrawerHeader align="center">{refHeader}</DrawerHeader>
                        <DrawerBody>
                          {/* ReferencePreview exists in your codebase */}
                          <ReferencePreview file={pdf} page={page} />
                        </DrawerBody>
                      </DrawerContent>
                    </Drawer>
                  </>
                )}
              </VStack>
            ))}

            {isLoading && (
              <VStack
                align="start"
                spacing={1}
                p={5}
                backgroundColor={useColorModeValue("gray.200", "gray.600")}
                borderRadius="15"
              >
                <SmartToyIcon />
                <Text fontWeight="bold">Generating response...</Text>
                <Spinner
                  size="sm"
                  thickness="3px"
                  speed="0.5s"
                  color="blue.500"
                />
              </VStack>
            )}
          </VStack>

          {/* Input Row */}
          <Flex
            w={{ base: "80%", md: "80%" }}
            mx="auto"
            align="center"
            gap={3}
            wrap="nowrap"
          >
            <Input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              flex="1"
              minW={0}
              bg={inputBgColor}
              color={textColor}
              placeholder={
                copilotReady ? "Type your message..." : "Connecting to Copilot..."
              }
              isDisabled={!copilotReady}
              onKeyDown={(e) => {
                if (e.key === "Enter" && question.trim() !== "") {
                  e.preventDefault();
                  handleSubmit(e);
                }
              }}
            />

            <Button
              type="submit"
              isLoading={isLoading}
              isDisabled={!copilotReady || question.trim() === ""}
              onClick={handleSubmit}
              flexShrink={0}
            >
              <SendIcon />
            </Button>
          </Flex>
        </VStack>
      </Box>

      {/* --- FOOTER --- */}
      <Box
        as="footer"
        mt="auto"
        pt={2} 
        pb={4}
        bg={useColorModeValue("gray.50", "gray.900")}
      >
        <Flex justify="center" align="center" gap={3}>
          <Text
            fontSize="xs"
            fontWeight="bold"
            color="gray.500"
            textTransform="uppercase"
            letterSpacing="wider"
          >
            Powered By
          </Text>

          <Image
            src="/embryo-removebg.png"
            alt="SLT Digital Lab Logo"
            h="35px"
            objectFit="contain"
            opacity={0.8}
            _hover={{ opacity: 1 }}
            transition="opacity 0.2s"
          />
        </Flex>
      </Box>
    </Flex>
  );
}

export default CopilotChatInterface;
