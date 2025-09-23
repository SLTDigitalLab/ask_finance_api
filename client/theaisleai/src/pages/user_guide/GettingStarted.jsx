import React from 'react'
import {
    Text, Container, Heading, Image, Box,
} from "@chakra-ui/react";
import Footer from '../../components/Footer';

function GettingStarted() {
  return (
    <Box>
        <Container maxW="container.xl">
            <Heading size='lg' mb={5}>Getting Started</Heading>
            <Text fontSize="lg">To start a session, we must first enable the API Key. This a guide how</Text>
            <Box m={10} alignContent='center' maxW="100%">
              <Image src="GS1 (1).png" alt="History-Navbar" maxW="75%" height="auto" />
            </Box>
            <Text fontSize="lg">User selects the settings button to navigate to API-Key</Text>
            <Box m={10} alignContent='center' maxW="100%">
              <Image src="gs2.png" alt="History-Navbar" maxW="75%" height="auto" />
            </Box>
            <Text fontSize="lg">User then selects API-Key from Navbar</Text>
            <Box m={10} alignContent='center' maxW="100%">
              <Image src="gs3.png" alt="History-Navbar" maxW="75%" height="auto" />
            </Box>
            <Text fontSize="lg">Once the API details are entered and the user submits the API-key. The user has to refresh the page to then view the created API-Key</Text>
            <Box m={10} alignContent='center' maxW="100%">
              <Image src="gs3.png" alt="History-Navbar" maxW="75%" height="auto" />
            </Box>
            <Text fontSize="lg" mb={10}>The user can then select the API key and can start the session.</Text>
        </Container>
        <Footer />
    </Box>
  )
}

export default GettingStarted
