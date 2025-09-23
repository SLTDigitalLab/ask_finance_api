import React from 'react'
import {
    Text, Container, Heading, Image, Box,
} from "@chakra-ui/react";
import Footer from '../../components/Footer';

function UsageGuide() {
  return (
    <Box>
        <Container maxW="container.xl">
            <Heading size="lg" mb={5}>Usage Monitoring</Heading>
            <Text fontSize="lg">For inferecnce, the usage of tokens will be calculated and displayed here with some addtional information.</Text>
            <Box m={10} alignContent='center' maxW="100%">
              <Image src="usageGuide1.png" alt="History-Navbar" maxW="75%" height="auto" />
            </Box>
            <Text fontSize="lg">User can select the Usage from the NavBar and navigate to the Usage page.</Text>
            <Box m={10} alignContent='center' maxW="100%">
              <Image src="usageGuide2.png" alt="History-Navbar" maxW="75%" height="auto" />
            </Box>
            <Text fontSize="lg" mb={10}>A detailed view of the token count and cost related to each chat session can be seen. </Text>
        </Container>
        <Footer />
    </Box>
  )
}

export default UsageGuide
