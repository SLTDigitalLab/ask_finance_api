import React from 'react'
import {
    Text, Container, Heading, Image, Box,
} from "@chakra-ui/react";
import Footer from '../../components/Footer';

function HistoryGuide() {
  return (
    <Box>
        <Container maxW="container.xl">
            <Heading size='lg' mb={5}>History</Heading>
            <Text fontSize="lg">To review and visit past history sessions a user can visit history page. The page will reflect past history interactions.</Text>
            <Box m={10} alignContent='center' maxW="100%">
              <Image src="historyGuide1.png" alt="History-Navbar" maxW="75%" height="auto" />
            </Box>
            <Text fontSize="lg">User can select the History from the NavBar and navigate to the history page.</Text>
            <Box m={10} alignContent='center' maxW="100%">
              <Image src="historyGuide2.png" alt="History-Navbar" maxW="75%" height="auto" />
            </Box>
        </Container>
        <Footer />
    </Box>
  )
}

export default HistoryGuide
