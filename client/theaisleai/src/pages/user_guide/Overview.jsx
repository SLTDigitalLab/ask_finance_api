import React from 'react';
import {
  Container, Heading, Text, Flex, Box, SimpleGrid, Card, CardBody,
} from "@chakra-ui/react";

function Overview() {
  return (
    <Container maxW="container.xl" centerContent>
      <Flex alignItems="center" justifyContent="center" direction={{ base: 'column', md: 'column' }} textAlign="center" mt={10} mb={10}>
        <Box w={{ base: '100%', md: '80%' }} p={8}>
          <Heading as="h1" size="xl" mb={6}>
            Overview
          </Heading>
          <Text fontSize="xl" mb={6}>
            AisleAI is a generative AI platform designed to serve as an enterprise knowledge hub. We use advanced retrieval-augmentation generation (RAG) techniques to improve knowledge management and decision-making processes. AisleAI can seamlessly integrate with various data sources, enabling businesses to extract, augment, and generate valuable insights from their vast repositories of information.
          </Text>
        </Box>
      </Flex>

      {/* Key Features Section */}
      <Heading as="h2" size="lg" mt={10} textAlign="center">
        Key Features
      </Heading>
      <SimpleGrid columns={{ base: 1, md: 3 }} spacing={6} mt={5} mb={10}>
        <Card _hover={{ bg: '#f5f5f5', boxShadow: '0px 2px 5px rgba(0, 0, 0, 0.1)', transform: 'translateY(-3px)' }}>
          <CardBody>
            <Text fontWeight="bold" fontSize="xl">Advanced RAG Techniques</Text>
            <Text fontSize="xl">
              Utilize cutting-edge retrieval-augmentation generation to enhance data-driven decisions.
            </Text>
          </CardBody>
        </Card>
        <Card _hover={{ bg: '#f5f5f5', boxShadow: '0px 2px 5px rgba(0, 0, 0, 0.1)', transform: 'translateY(-3px)' }}>
          <CardBody>
            <Text fontWeight="bold" fontSize="xl">Seamless Integration</Text>
            <Text fontSize="xl">
              Connect with various data sources effortlessly for unified knowledge management.
            </Text>
          </CardBody>
        </Card>
        <Card _hover={{ bg: '#f5f5f5', boxShadow: '0px 2px 5px rgba(0, 0, 0, 0.1)', transform: 'translateY(-3px)' }}>
          <CardBody>
            <Text fontWeight="bold" fontSize="xl">Real-time Insights</Text>
            <Text fontSize="xl">
              Generate valuable insights instantly from large information repositories.
            </Text>
          </CardBody>
        </Card>
      </SimpleGrid>

      {/* Benefits Section */}
      <Heading as="h2" size="lg" mt={10} textAlign="center">
        Benefits
      </Heading>
      <SimpleGrid columns={{ base: 1, md: 3 }} spacing={6} mt={5} mb={10}>
        <Card _hover={{ bg: '#f5f5f5', boxShadow: '0px 2px 5px rgba(0, 0, 0, 0.1)', transform: 'translateY(-3px)' }}>
          <CardBody>
            <Text fontWeight="bold" fontSize="xl">Improved Efficiency</Text>
            <Text fontSize="xl">
              Streamline decision-making with automated data processing.
            </Text>
          </CardBody>
        </Card>
        <Card _hover={{ bg: '#f5f5f5', boxShadow: '0px 2px 5px rgba(0, 0, 0, 0.1)', transform: 'translateY(-3px)' }}>
          <CardBody>
            <Text fontWeight="bold" fontSize="xl">Cost-Effective</Text>
            <Text fontSize="xl">
              Reduce the time and resources spent on manual data handling.
            </Text>
          </CardBody>
        </Card>
        <Card _hover={{ bg: '#f5f5f5', boxShadow: '0px 2px 5px rgba(0, 0, 0, 0.1)', transform: 'translateY(-3px)' }}>
          <CardBody>
            <Text fontWeight="bold" fontSize="xl">Scalable Solutions</Text>
            <Text fontSize="xl">
              Adapt to your organization's growing needs with scalable AI solutions.
            </Text>
          </CardBody>
        </Card>
      </SimpleGrid>
    </Container>
  );
}

export default Overview;
