import React from 'react';
import {
  Text, Container, Heading, Image, Box, OrderedList, ListItem,
} from "@chakra-ui/react";
import Footer from '../../components/Footer';

function ChatGuide() {
  return (
    <Box>
      <Container maxW="container.xl">
        <Heading size='lg' mb={5}>Chat Guide</Heading>
        
        <Text fontSize="lg" mb={5}>
          On successful subscription, users will be redirected to the chat interface where they will:
        </Text>
        
        <Text fontSize="lg" mb={3}>
          - Initially upload a document in the upload page.
        </Text>
        
        <Text fontSize="lg" mb={3}>
          - Choose the uploaded document in the chat interface.
        </Text>
        
        <Text fontSize="lg" mb={3}>
          - Select a chat mode (Short/Long).
        </Text>
        
        <Text fontSize="lg" mb={3}>
          - Start a session.
        </Text>
        
        <Text fontSize="lg" mb={6}>
          - And enter a query.
        </Text>

        <Box m={10} alignContent='center' maxW="100%">
          <Image src="d.png" alt="Chat Interface" maxW="75%" height="auto" />
        </Box>

        <Heading size='md' mb={5}>Component Description</Heading>

        <Box m={10} alignContent='center' maxW="100%">
            <Image src="cg1.png" alt="History-Navbar" maxW="75%" height="auto" />
        </Box>
        
        <OrderedList mb={10}>
            <ListItem fontSize="lg" mb={3}><b>Collection Selector:</b> All the created collections are available here. Users can select one or more collections.</ListItem>
            <ListItem fontSize="lg" mb={3}><b>Chat Mode Selector:</b> Users can get short or long answers according to the selected chat mode. </ListItem>
            <ListItem fontSize="lg" mb={3}><b>All Collections:</b> This will select all collections to start the chat session.</ListItem>
            <ListItem fontSize="lg" mb={3}><b>Web Search:</b> Enables the web search option and retrieves the information from the web. </ListItem>
            <ListItem fontSize="lg" mb={3}><b>Start Session:</b> Users need to start a chat session before submit the question.</ListItem>
            <ListItem fontSize="lg" mb={3}><b>Global Cache:</b> Users can access the global cache which contains all the questions and answers of all users. </ListItem>
            <ListItem fontSize="lg" mb={3}><b>Delete Cache:</b> Deletes the cache memory which contains the user's previous chat messages and answers.</ListItem>
            <ListItem fontSize="lg" mb={3}><b>Submit Button:</b> Submits the user-entered question to the AisleAI bot.</ListItem>
            <ListItem fontSize="lg" mb={3}><b>Voice Message:</b> The voice message option can be enabled here.</ListItem>
        </OrderedList>

      </Container>
      <Footer />
    </Box>
  );
}

export default ChatGuide;
