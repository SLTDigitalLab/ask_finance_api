import React, { useEffect, useState, useRef, useCallback } from "react";
import Select from "react-select";
import {
  Box,
  Button,
  Container,
  Card,
  CardBody,
  Drawer,
  Flex,
  Heading,
  Image,
  Input,
  Grid,
  Text,
  useToast,
  VStack,
  HStack,
  useColorModeValue,
  Switch,
  SimpleGrid,
  Popover,
  PopoverTrigger,
  PopoverContent,
  PopoverBody,
  PopoverArrow,
  useDisclosure,
  DrawerOverlay,
  DrawerContent,
  DrawerCloseButton,
  DrawerHeader,
  DrawerBody,
  useColorMode,
  Spinner,
} from "@chakra-ui/react";
import axios from "axios";
import { useDispatch, useSelector } from "react-redux";
import { NavLink, useNavigate } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import { v4 as uuidv4 } from "uuid";
import AddCircleOutlineIcon from "@mui/icons-material/AddCircleOutline";
import FaceIcon from "@mui/icons-material/Face";
import SmartToyIcon from "@mui/icons-material/SmartToy";
import RemoveCircleOutlineIcon from "@mui/icons-material/RemoveCircleOutline";
import SendIcon from "@mui/icons-material/Send";
import { CHAT } from "../urls";
import PublicIcon from "@mui/icons-material/Public";
import PublicOffIcon from "@mui/icons-material/PublicOff";
import DeleteOutlinedIcon from "@mui/icons-material/DeleteOutlined";
// import MicrophoneButton from "../components/MicrophoneButton";
import KeyboardVoiceIcon from "@mui/icons-material/KeyboardVoice";
import MicOffIcon from "@mui/icons-material/MicOff";
import FileUploadIcon from "@mui/icons-material/FileUpload";
import KeyIcon from "@mui/icons-material/Key";
import TextSnippetIcon from "@mui/icons-material/TextSnippet";
import NotesIcon from "@mui/icons-material/Notes";
import LanguageIcon from "@mui/icons-material/Language";
import MemoryIcon from "@mui/icons-material/Memory";
import DeleteIcon from "@mui/icons-material/Delete";
import ChatIcon from "@mui/icons-material/Chat";
import HelpOutlineOutlinedIcon from "@mui/icons-material/HelpOutlineOutlined";
import QuizOutlinedIcon from "@mui/icons-material/QuizOutlined";
import { keyframes } from "@emotion/react";

const spin = keyframes`
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
`;

// Custom styles for react-select dropdown
const customStyles = (isDarkMode) => ({
  control: (provided) => ({
    ...provided,
    backgroundColor: isDarkMode ? "#2D3748" : "white",
    borderColor: isDarkMode ? "#4A5568" : "#E2E8F0",
    color: isDarkMode ? "white" : "black",
  }),
  option: (provided, state) => ({
    ...provided,
    backgroundColor: state.isFocused
      ? isDarkMode
        ? "#4A5568"
        : "#EDF2F7"
      : isDarkMode
      ? "#2D3748"
      : "white",
    color: isDarkMode ? "white" : "black",
    "&:hover": {
      backgroundColor: isDarkMode ? "#4A5568" : "#EDF2F7",
    },
  }),
  menu: (provided) => ({
    ...provided,
    backgroundColor: isDarkMode ? "#2D3748" : "white",
  }),
  singleValue: (provided) => ({
    ...provided,
    color: isDarkMode ? "white" : "black",
  }),
  input: (provided) => ({
    ...provided,
    color: isDarkMode ? "white" : "black",
  }),
});

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
  const isSubmitAndRecordEnabled = apiKey != null;

  const modeOptions = [
    { value: "short", label: "Short" },
    { value: "long", label: "Long" },
  ];

  const toggleCacheMode = () => {
    setIsGlobalCache((prevMode) => !prevMode);
    // Optionally, inform backend about cache mode here
  };

  // Fetch header for history
  const fetchHeader = async (question, reply) => {
    const msg = [question, reply];
    try {
      const hist_header = await axios.post(
        CHAT.CHAT_HEADER,
        {
          chat_id: chatSessionId,
          collection_id: selectedCollectionIds,
          messages: msg,
        },
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      setChatHeader(hist_header.data.result.response);
      return hist_header.data.result.response;
    } catch (error) {
      console.error("Error fetching chat header:", error);
    }
  };

  const ensureSessionId = () => {
    if (!chatSessionId) {
      const newSessionId = uuidv4();
      setChatSessionId(newSessionId);
      return newSessionId;
    }
    return chatSessionId;
  };

  const FRONTEND_TOKEN = "lYrCN/UOC8c+e7CveLp1awTcoUJG8wGDYw5IaK5wf+w=";

  // Send Chat Question
  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      // Ensure session ID exists
      let currentChatId = chatSessionId;
      if (!currentChatId) {
        currentChatId = uuidv4();
        setChatSessionId(currentChatId);
      }

      // Send query to backend with chat_id
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

      // If backend returns new chat_id on first request, store it
      if (response.data.chat_id && !chatSessionId) {
        setChatSessionId(response.data.chat_id);
      }

      // Update chat history
      setChatHistory((prev) => [
        ...prev,
        { role: "user", message: question },
        { role: "bot", message: botAnswer, mapLinks },
      ]);

      setQuestion(""); // clear input
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

  const handleDeleteCache = () => {
    const token = localStorage.getItem("authToken");
    axios
      .delete(CHAT.DELETE_LOCAL_CACHE, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      .then((response) => {
        if (response.data.msg === "Local cache deleted successfully") {
          toast({
            title: response.data.msg,
            status: "success",
            duration: 3000,
            isClosable: true,
          });
        } else {
          toast({
            title: response.data.msg,
            status: "error",
            duration: 3000,
            isClosable: true,
          });
        }
      })
      .catch((error) => {
        console.error("Error occured during cache clearing - ", error);
        toast({
          title: "Error Deleting Cache",
          status: "error",
          duration: 3000,
          isClosable: true,
        });
      });
  };

  const loadPdf = async (file, page) => {
    try {
      const response = await axios.get(`${CHAT.GET_PDF}/${file}`, {
        responseType: "blob",
      });
      if (response.status === 200) {
        const pdfUrl = URL.createObjectURL(response.data);
        setPdf(pdfUrl);
        setRefHeader(file);
        setPage(page);
      } else {
        console.error("Error fetching PDF:", response.data);
        setPdf(null);
      }
    } catch (error) {
      console.error("Error fetching PDF file:", error);
      setPdf(null);
    }
  };

  return (
    <Flex h="80vh" w="100%" justify="center" align="center">
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
        position="relative" // keeps the help popover absolute positioning working
      >
        <VStack spacing={2} p={4} pb={0} flexGrow={1}>
          <VStack w="full" h="70vh" alignItems="left" p={3} overflowY="auto">
            {chatHistory.length === 0 ? (
              <VStack spacing={1} align="center" p={5} borderRadius="15" boxShadow="xl" flexGrow={100}>
                <Image src="/12.png" alt="Logo" boxSize="300px" mb={-10} opacity="70%" />
                <Text fontSize="2xl" fontWeight="bold" color="gray.600">
                  How can I assist you today?
                </Text>
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
                          <ReferencePreview file={pdf} page={page} />
                        </DrawerBody>
                      </DrawerContent>
                    </Drawer>
                  </>
                )}
              </VStack>
            ))}

            {isLoading && (
              <VStack align="start" spacing={1} p={5} backgroundColor={useColorModeValue("gray.200", "gray.600")} borderRadius="15">
                <SmartToyIcon />
                <Text fontWeight="bold">Generating response...</Text>
                <Spinner size="sm" thickness="3px" speed="0.5s" color="blue.500" />
              </VStack>
            )}
          </VStack>

          {/* Input Row */}
<Flex
  w={{ base: "80%", md: "80%" }}
  mx="auto"
  align="center"
  gap={3}
  wrap="nowrap"         // keep on one line
>
  <Input
    value={question}
    onChange={(e) => setQuestion(e.target.value)}
    flex="1"            // fill remaining space
    minW={0}            // allow shrinking on small screens
    bg={inputBgColor}
    color={textColor}
  />
  <Button
    type="submit"
    isLoading={isLoading}
    isDisabled={question.trim() === ""}
    onClick={handleSubmit}
    flexShrink={0}      // don't let button shrink
  >
    <SendIcon />
  </Button>
</Flex>
        </VStack>
      </Box>
    </Flex>
  );
}

export default ChatInterface;
