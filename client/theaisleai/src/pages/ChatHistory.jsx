import React, { useEffect, useState } from "react";
import axios from "axios";
import ReactMarkdown from "react-markdown";
import {
  Box,
  Divider,
  Drawer,
  Container,
  Heading,
  Text,
  VStack,
  Button,
  useColorModeValue,
  Flex,
  List,
  ListItem,
  useDisclosure,
  DrawerOverlay,
  DrawerContent,
  DrawerCloseButton,
  DrawerHeader,
  DrawerBody,
  Image
} from "@chakra-ui/react";
import FaceIcon from "@mui/icons-material/Face";
import SmartToyIcon from "@mui/icons-material/SmartToy";
import Footer from "../components/Footer";
import { CHAT } from "../urls";
import { format, isToday, isYesterday, parseISO } from 'date-fns';
import ReferencePreview from "../components/ReferencePreview";

function ChatHistory() {
  const [chatHistory, setChatHistory] = useState([]);
  const [selectedChatId, setSelectedChatId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [uniqueChats, setUniqueChats] = useState([]);
  const [visibleItemCount, setVisibleItemCount] = useState(10);
  const { isOpen, onOpen, onClose } = useDisclosure()
  const [pdf, setPdf] = useState(null)
  const [page, setPage] = useState(0)
  const [refHeader, setRefHeader] = useState("")
  const btnRef = React.useRef()


  // Dynamic colors for light and dark modes
  const sidebarBgColor = useColorModeValue("gray.100", "gray.900");
  const mainBgColor = useColorModeValue("gray.50", "gray.800");
  const textColor = useColorModeValue("gray.800", "white");
  const hoverBgColor = useColorModeValue("gray.200", "gray.700");
  const selectedBgColor = "#457b9d";
  const selectedTextColor = "white";
  const userMessageBgColor = useColorModeValue("#edede9", "gray.700"); // Light mode: #edede9, Dark mode: gray.700
  const botMessageBgColor = useColorModeValue("gray.100", "gray.900"); // Light mode: gray.100, Dark mode: gray.900

  useEffect(() => {
    const fetchChatHistory = async () => {
      setIsLoading(true);
      try {
        const token = localStorage.getItem("authToken");
        const response = await axios.get(CHAT.GET_CHAT_HISTORY, {
          headers: { Authorization: `Bearer ${token}` },
        });

        setChatHistory(response.data.result);
        const uniqueChatIds = new Set(response.data.result.map((chat) => chat.chat_id));
        setUniqueChats(Array.from(uniqueChatIds));
      } catch (error) {
        console.error("Error fetching chat history:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchChatHistory();
  }, []);

  const categorizeChatsByDate = (chatHistory) => {
    const categorizedChats = {
      Today: [],
      Yesterday: [],
      Older: [],
    };

    chatHistory.forEach((chat) => {
      const chatDate = parseISO(chat.timestamp);

      if (isToday(chatDate)) {
        if (!categorizedChats.Today.includes(chat.chat_id)) {
          categorizedChats.Today.push(chat.chat_id);
        }
      } else if (isYesterday(chatDate)) {
        if (!categorizedChats.Yesterday.includes(chat.chat_id)) {
          categorizedChats.Yesterday.push(chat.chat_id);
        }
      } else {
        if (!categorizedChats.Older.includes(chat.chat_id)) {
          categorizedChats.Older.push(chat.chat_id);
        }
      }
    });

    return categorizedChats;
  };

  const categorizedChatHistory = categorizeChatsByDate(chatHistory);
  console.log(categorizedChatHistory);

  const filteredChatHistory = selectedChatId
    ? chatHistory.filter((entry) => entry.chat_id === selectedChatId)
    : [];


  const uniqueChatMaps = new Map(chatHistory.map((chat) => [chat.chat_id, chat.chat_header]))

  console.log(uniqueChatMaps);

  const loadPdf = async (file, page) => {
    try {
      const token = localStorage.getItem("authToken");
      const response = await axios.get(`${CHAT.GET_PDF}/${file}`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob',
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
      console.error('Error fetching PDF file:', error);
      setPdf(null);
    }
  };

  const handleShowMore = () => {
    if (isLoading || uniqueChats.length < visibleItemCount) return;
    setVisibleItemCount(prevCount => prevCount + 10);
  };

  const remainingAfterToday = Math.max(0, visibleItemCount - categorizedChatHistory.Today.length);
  const remainingAfterYesterday = Math.max(0, remainingAfterToday - categorizedChatHistory.Yesterday.length);

  return (
    <Box>
      <Container maxW="100vw" minH="100vh" p={0} display="flex" flexDirection="column">
        <Flex flex="1" overflow="hidden">
          {/* Sidebar Container for Chat History */}
          <Box
            w="30%"
            bg={sidebarBgColor}
            p={4}
            m={5}
            borderRadius={15}
            height="80vh"
            overflowY="auto" // Enable vertical scrolling when content overflows
          >
            <Heading size="md" mb={4}>
              Chat History
            </Heading>
            <Divider orientation="horizontal" borderColor="#457b9d" mb={3} />
            <Box
              flex="1"
              overflowY="scroll"
              pr={2}
              sx={{
                '::-webkit-scrollbar': {
                  width: '8px',
                  height: '40px',
                },
                '::-webkit-scrollbar-thumb': {
                  background: '#457b9d',
                  borderRadius: '4px',
                },
                '::-webkit-scrollbar-track': {
                  background: useColorModeValue("#f0f0f0", "gray.700"),
                },
              }}
            >
              <List spacing={3}>
                {categorizedChatHistory.Today.length !== 0 ? (
                  <>
                    <Heading size="sm" color={textColor}>Today</Heading>
                    {categorizedChatHistory.Today.reverse().slice(0, visibleItemCount).map((chat_id) => (
                      <ListItem
                        key={chat_id}
                        p={2}
                        bg={selectedChatId === chat_id ? selectedBgColor : "transparent"}
                        color={selectedChatId === chat_id ? selectedTextColor : textColor}
                        borderRadius="md"
                        cursor="pointer"
                        onClick={() => setSelectedChatId(chat_id)}
                        _hover={{
                          bg: selectedChatId === chat_id ? selectedBgColor : hoverBgColor,
                        }}
                      >
                        {uniqueChatMaps.get(chat_id) ? uniqueChatMaps.get(chat_id) : chat_id}
                      </ListItem>
                    ))}
                  </>
                ) : (
                  []
                )}
                {categorizedChatHistory.Yesterday.length !== 0 && remainingAfterToday !== 0 ? (
                  <>
                    <Heading size="sm" color={textColor}>Yesterday</Heading>
                    {categorizedChatHistory.Yesterday.reverse().slice(0, remainingAfterToday).map((chat_id) => (
                      <ListItem
                        key={chat_id}
                        p={2}
                        bg={selectedChatId === chat_id ? selectedBgColor : "transparent"}
                        color={selectedChatId === chat_id ? selectedTextColor : textColor}
                        borderRadius="md"
                        cursor="pointer"
                        onClick={() => setSelectedChatId(chat_id)}
                        _hover={{
                          bg: selectedChatId === chat_id ? selectedBgColor : hoverBgColor,
                        }}
                      >
                        {uniqueChatMaps.get(chat_id) ? uniqueChatMaps.get(chat_id) : chat_id}
                      </ListItem>
                    ))}
                  </>
                ) : (
                  []
                )}
                {categorizedChatHistory.Older.length !== 0 && remainingAfterYesterday !== 0 ? (
                  <>
                    <Heading size="sm" color={textColor}>Previous</Heading>
                    {categorizedChatHistory.Older.reverse().slice(0, remainingAfterYesterday).map((chat_id) => (
                      <ListItem
                        key={chat_id}
                        p={2}
                        bg={selectedChatId === chat_id ? selectedBgColor : "transparent"}
                        color={selectedChatId === chat_id ? selectedTextColor : textColor}
                        borderRadius="md"
                        cursor="pointer"
                        onClick={() => setSelectedChatId(chat_id)}
                        _hover={{
                          bg: selectedChatId === chat_id ? selectedBgColor : hoverBgColor,
                        }}
                      >
                        {uniqueChatMaps.get(chat_id) ? uniqueChatMaps.get(chat_id) : chat_id}
                      </ListItem>
                    ))}
                  </>
                ) : (
                  []
                )}
              </List>
              {uniqueChats.length > visibleItemCount ? (
                <Flex justifyContent="center" mt={4}>
                  <Button
                    bg="#457B9D"
                    textColor={textColor}
                    colorScheme="#ffffff"
                    minWidth="10vw"
                    align="center"
                    borderRadius={10}
                    onClick={handleShowMore}
                    _hover={{ bg: "#2c5a6d" }}
                  >
                    Show More
                  </Button>
                </Flex>
              ) : (
                []
              )}
            </Box>
          </Box>
          {/* Main Chat Display */}
          <Box w="90%" p={4} overflowY="auto">
            {filteredChatHistory.length > 0 ? (
              <VStack
                w="full"
                align="left"
                border="1px"
                borderRadius={5}
                borderColor="gray.200"
                height="80vh"
                p={4}
                spacing={3}
                bg={mainBgColor}
                overflowY="auto"
                sx={{
                  '::-webkit-scrollbar': {
                    width: '8px',
                  },
                  '::-webkit-scrollbar-thumb': {
                    background: '#457b9d',
                    borderRadius: '4px',
                  },
                  '::-webkit-scrollbar-track': {
                    background: useColorModeValue("#f0f0f0", "gray.700"),
                  },
                }}
              >
                {filteredChatHistory.map((entry, index) => {
                  const referenced_file = entry.file.split(',').map(file => file.trim()).filter(Boolean);
                  const referenced_page = entry.page.split(',').map(page => page.trim()).filter(Boolean);
                  const pageNumbers = referenced_page.map(Number);
                  const images = entry.image.split(',').map(image => image.trim()).filter(Boolean);
                  return (
                    <VStack
                      backgroundColor={
                        entry.role === "user"
                          ? userMessageBgColor // Dynamic background color for user messages
                          : botMessageBgColor // Dynamic background color for bot messages
                      }
                      borderRadius="15"
                      p={5}
                      key={index}
                      align="start"
                    >
                      <Text fontWeight="bold" align="left">
                        {entry.role === "user" ? <FaceIcon /> : <SmartToyIcon />}
                      </Text>

                      <ReactMarkdown>{entry.message.normalize('NFC')}</ReactMarkdown>
                      {Array.isArray(images) && images.length > 0 ? (
                        <>
                          {images.map((img, index) => (
                            <Image key={index} rounded="md" src={img} alt="Image" />
                          ))}
                        </>
                      ) : null}

                      {Array.isArray(referenced_file) && referenced_file.length > 0 ? (
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
                              <DrawerBody><ReferencePreview file={pdf} page={page}/></DrawerBody>
                            </DrawerContent>
                          </Drawer>
                        </>
                      ) : null}
                    </VStack>
                  )
                })}
              </VStack>
            ) : (
              <Text h={'100%'} w={'100%'} textAlign={'center'} alignContent={'center'} color={textColor}>No chat history found for the selected chat.</Text>
            )}
          </Box>
        </Flex>
        <Footer />
      </Container>
    </Box>
  );
}

export default ChatHistory;
