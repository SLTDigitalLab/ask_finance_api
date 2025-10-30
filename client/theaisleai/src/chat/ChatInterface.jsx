import React, { useEffect, useState, useRef, useCallback } from "react";
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
  // --- IMPORTS ADDED FOR POPOVER ---
  Popover,
  PopoverTrigger,
  PopoverContent,
  PopoverBody,
  PopoverArrow,
  PopoverCloseButton,
  IconButton,
} from "@chakra-ui/react";
import { ChatIcon } from "@chakra-ui/icons"; // <-- IMPORT ADDED
import axios from "axios";
import { useDispatch, useSelector } from "react-redux";
import { NavLink, useNavigate } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import { v4 as uuidv4 } from "uuid";
import FaceIcon from "@mui/icons-material/Face";
import SmartToyIcon from "@mui/icons-material/SmartToy";
import SendIcon from "@mui/icons-material/Send";
import { CHAT } from "../urls";
import { keyframes } from "@emotion/react";
import Assistant from "./Assistant"; // <-- Assumed import for the Assistant component

const spin = keyframes`
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
`;

const blink = keyframes`
  0% { opacity: 0.2; }
  20% { opacity: 1; }
  100% { opacity: 0.2; }
`;


function ChatInterface() {
  const { colorMode } = useColorMode();
  const isDarkMode = colorMode === "dark";
  const bgColor = useColorModeValue("gray.50", "gray.800");
  const textColor = useColorModeValue("gray.800", "white");
  const cardBgColor = useColorModeValue("white", "gray.700");
  const inputBgColor = useColorModeValue("white", "gray.600");
  const hoverBgColor = useColorModeValue("gray.100", "gray.600");

  const [isLoading, setIsLoading] = useState(false);
  const [chatHeader, setChatHeader] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [msgCount, setMsgCount] = useState(0);
  const [question, setQuestion] = useState("");
  const toast = useToast();
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const navigate = useNavigate();
  const [chatMode, setChatMode] = useState("short");
  const [chatSessionId, setChatSessionId] = useState(null);
  const [isGlobalCache, setIsGlobalCache] = useState(false); // New state for cache mode
  const { userObj } = useSelector((state) => state.user);
  const [apiKey, setApikey] = useState(null);
  const { isOpen, onOpen, onClose } = useDisclosure();
  const [pdf, setPdf] = useState(null);
  const [page, setPage] = useState(0);
  const [refHeader, setRefHeader] = useState("");
  const btnRef = React.useRef();

  const FRONTEND_TOKEN = "lYrCN/UOC8c+e7CveLp1awTcoUJG8wGDYw5IaK5wf+w=";

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      let currentChatId = chatSessionId;
      if (!currentChatId) {
        currentChatId = uuidv4();
        setChatSessionId(currentChatId);
      }
      const response = await axios.post(
        CHAT.MULTI_AGENT_CHAT,
        {
          query: question,
          chat_id: currentChatId,
        },
        {
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${FRONTEND_TOKEN}`,
          },
        }
      );
      const botAnswer = response.data.answer || "No answer from multi-agent backend";
      const mapLinks = response.data.map_links || [];
      if (response.data.chat_id && !chatSessionId) {
        setChatSessionId(response.data.chat_id);
      }
      setChatHistory((prev) => [
        ...prev,
        { role: "user", message: question },
        { role: "bot", message: botAnswer, mapLinks },
      ]);
      setQuestion("");
    } catch (error) {
      console.error("Multi-agent chat error:", error);
      toast({
        title: "An error occurred",
        description: error.response?.data?.detail || error.message,
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <> {/* <-- WRAPPER ADDED */}
      <Flex h="100vh" w="100%" justify="center" align="flex-start">
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
        >
          <VStack spacing={2} p={4} pb={0} flexGrow={1}>
            <VStack w="full" h="70vh" alignItems="left" p={3} overflowY="auto">
              {chatHistory.length === 0 ? (
                <VStack spacing={1} align="center" p={5} borderRadius="15" boxShadow="xl" flexGrow={100}>
                  <Image src="/12.png" alt="Logo" boxSize={{ base: "200px", md: "300px" }} mb={-10} opacity="70%" />
                  <Text fontSize={{ base: "xl", md: "2xl" }} fontWeight="bold" color="gray.600">
                    How can I assist you today?
                  </Text>
                </VStack>
              ) : null}

              {chatHistory.map((entry, index) => (
                <VStack
                  key={index}
                  maxW={{ base: "85%", md: "70%" }}
                  alignSelf={entry.role === "user" ? "flex-end" : "flex-start"}
                  align={entry.role === "user" ? "end" : "start"}
                  spacing={1}
                  p={5}
                  backgroundColor={
                    entry.role === "user"
                      ? useColorModeValue("#edede9", "gray.700")
                      : useColorModeValue("gray.100", "gray.900")
                  }
                  borderRadius="15"
                >
                  <Text fontWeight="bold">{entry.role === "user" ? <FaceIcon /> : <SmartToyIcon />}</Text>

                  {entry.message === "Generating response..." ? (
                    <HStack>
                      <Text>Generating response</Text>
                      <Spinner size="sm" thickness="3px" speed="0.5s" color="blue.500" />
                    </HStack>
                  ) : (
                    <ReactMarkdown>{entry.message.normalize("NFC")}</ReactMarkdown>
                  )}

                  {Array.isArray(entry.image) &&
                    entry.image.length > 0 &&
                    entry.image.map((img, idx) => <Image key={idx} rounded="md" src={img} alt="Image" />)}

                  {Array.isArray(entry.file) && entry.file.length > 0 && (
                    <>
                      <Drawer isOpen={isOpen} placement="right" onClose={onClose} finalFocusRef={btnRef} size="xl">
                        <DrawerOverlay />
                        <DrawerContent>
                          <DrawerCloseButton />
                          <DrawerHeader align="center">{refHeader}</DrawerHeader>
                          <DrawerBody>
                            {/* Ensure ReferencePreview exists in your codebase */}
                            {/* <ReferencePreview file={pdf} page={page} /> */}
                          </DrawerBody>
                        </DrawerContent>
                      </Drawer>
                    </>
                  )}
                </VStack>
              ))}

              {isLoading && (
                <VStack align="start" spacing={1} p={5} maxW={{ md: "20%" }} backgroundColor={useColorModeValue("gray.200", "gray.600")} borderRadius="15">
                  <SmartToyIcon />
                  <Text fontWeight="bold">Generating response...</Text>
                  <HStack spacing={1}>
                        <Box as="span" boxSize="10px" bg="blue.500" borderRadius="full" animation={`${blink} 1.4s infinite both`} animationDelay="0.0s" />
                        <Box as="span" boxSize="10px" bg="blue.500" borderRadius="full" animation={`${blink} 1.4s infinite both`} animationDelay="0.2s" />
                        <Box as="span" boxSize="10px" bg="blue.500" borderRadius="full" animation={`${blink} 1.4s infinite both`} animationDelay="0.4s" />
                      </HStack>
                </VStack>
              )}
            </VStack>

            {/* Input Row */}
            <Flex
              as="form"
              onSubmit={handleSubmit}
              w={{ base: "95%", md: "80%" }}
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
              />
              <Button
                type="submit"
                isLoading={isLoading}
                isDisabled={question.trim() === ""}
                // onClick={handleSubmit}
                flexShrink={0}
              >
                <SendIcon />
              </Button>
            </Flex>
          </VStack>
        </Box>
      </Flex>

      
      <Popover placement="top-end" isLazy>
        <PopoverTrigger>
          <IconButton
            icon={<ChatIcon />}
            isRound={true}
            size="lg"
            colorScheme="blue"
            aria-label="Open Assistant Chat"
            position="fixed"
            bottom="3rem"
            right="2rem"
            boxShadow="lg"
          />
        </PopoverTrigger>
        <PopoverContent w="380px" h="500px" boxShadow="xl" borderRadius="lg" overflow="hidden">
          <PopoverArrow />
          <PopoverCloseButton zIndex="docked" bg="teal.600" color="white" _hover={{ bg: "teal.700" }}/>
          <PopoverBody p={0} h="100%">
            <Assistant />
          </PopoverBody>
        </PopoverContent>
      </Popover>
    </>
  );
}

export default ChatInterface;