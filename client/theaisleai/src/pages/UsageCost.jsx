import React, { useEffect, useState, useRef } from "react";
import {
  Box,
  Heading,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Text,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  useColorModeValue,
  Select,
  Container,
  Card,
  CardBody,
  CardHeader,
  Stack,
  RadioGroup,
  Radio,
  useBreakpointValue
} from "@chakra-ui/react";
import axios from "axios";
import DetailsCard from "../components/DetailsCard";
import { USAGE } from "../urls";
import { useDispatch, useSelector } from "react-redux";
import * as d3 from "d3";
import MonetizationOnIcon from '@mui/icons-material/MonetizationOn';
import DataUsageIcon from '@mui/icons-material/DataUsage';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, Legend } from 'recharts';
import Footer from "../components/Footer";

function calculateMonthlyUsageData(summaryData) {
  const monthlyData = {};

  summaryData.forEach((item) => {
    const date = new Date(item.details[0]?.timestamp);
    const month = `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, "0")}`;

    if (!monthlyData[month]) {
      monthlyData[month] = { tokenCount: 0, cost: 0 };
    }

    monthlyData[month].tokenCount += item.tokenCount;
    monthlyData[month].cost += item.cost;
  });

  return Object.entries(monthlyData).map(([month, data]) => ({
    month,
    tokenCount: data.tokenCount,
    cost: data.cost,
  }));
}

function UsageCostPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [usageData, setUsageData] = useState([]);
  const [formattedData, setFormattedData] = useState([]);
  const [summaryData, setSummaryData] = useState([]); // For the summary table
  const [selectedChatId, setSelectedChatId] = useState(null); // Track expanded row
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [currency, setCurrency] = useState(1);
  const [tokenCost, setTokenCost] = useState(0);
  const [usageCost, setUsageCost] = useState(0);
  const [monthlyUsageData, setMonthlyUsageData] = useState([]);
  const breakpointValue = useBreakpointValue({ base: "full", md: "768px" });

  const formatXAxisTick = (unixTime) => {
    const date = new Date(unixTime);

    const year = date.getFullYear();
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const day = date.getDate().toString().padStart(2, '0');
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');

    return `${year}-${month}-${day} ${hours}:${minutes}`;
  };

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      try {
        const token = localStorage.getItem("authToken");
        const response = await axios.get(USAGE.GET_COST, {
          headers: { Authorization: `Bearer ${token}` },
        });
        const formatData = (apiData) => {
          return apiData.map((item) => ({
            timestamp: new Date(item.timestamp),
            cost: item.cost,
            week: getWeekNumber(item.timestamp),
          }));
        };

        const formattedData = formatData(response.data.result);
        setFormattedData(formattedData);
        setUsageData(response.data.result);
        const calculatedSummary = calculateSummaryData(response.data.result);
        setSummaryData(calculatedSummary);

        const token_response = await axios.get(USAGE.GET_TOKEN_COST, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setTokenCost(token_response.data.result.token_cost);

        const cost_response = await axios.get(USAGE.GET_USAGE_COST, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setUsageCost(cost_response.data.result.usage_cost);
      } catch (error) {
        console.error("Error fetching usage data:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  useEffect(() => {
    const monthlyData = calculateMonthlyUsageData(summaryData);
    setMonthlyUsageData(monthlyData);
  }, [summaryData]);

  const getWeekNumber = (timestamp) => {
    const date = new Date(timestamp);
    date.setHours(0, 0, 0, 0);
    date.setDate(date.getDate() + 4 - (date.getDay() || 7));
    const yearStart = new Date(date.getFullYear(), 0, 1);
    return Math.ceil((((date - yearStart) / 86400000) + 1) / 7);
  };

  function calculateSummaryData(usageData) {
    const summary = {};

    usageData.forEach((item) => {
      const chatId = item.chat_id;
      if (!summary[chatId]) {
        summary[chatId] = {
          tokenCount: 0,
          cost: 0,
          latency: 0,
          details: [],
        };
      }

      summary[chatId].tokenCount += item.token_count;
      summary[chatId].cost += item.cost;
      summary[chatId].latency += item.latency;
      summary[chatId].details.push(item);
      summary[chatId].chat_id = item.chat_id;
    });
    return Object.values(summary);
  }

  function combinedFunc(id, boolean) {
    setSelectedChatId(id);
    setShowDetailsModal(boolean);
  }

  const tokenChartData = summaryData.map(row => ({
    chat_id: row.chat_id,
    tokenCount: row.tokenCount,
  }));

  return (
    <Box p={4}>
      <Container maxW={breakpointValue}>
        <Box mb={6} display="flex" flexDirection={{ base: "column", md: "row" }} justifyContent="space-between" gap={4}>
          <Box flex="1" mb={{ base: 4, md: 0 }}>
            <Card borderRadius={15} backgroundColor={useColorModeValue('gray.100', 'gray.900')}>
              <CardHeader>
                <Text fontSize={{ base: "lg", md: "xl" }} fontWeight="bold">Remaining Tokens</Text>
              </CardHeader>
              <CardBody>
                <Box display="flex" alignItems="center" justifyContent="center" flexDirection={{ base: "column", md: "row" }}>
                  <Box mb={{ base: 4, md: 0 }}><DataUsageIcon sx={{ fontSize: '4rem', color: "#457b9d" }} /></Box>
                  <Text fontSize={{ base: "xl", md: "2xl" }} textAlign="center">{tokenCost}</Text>
                </Box>
              </CardBody>
            </Card>
          </Box>
          <Box flex="1">
            <Card borderRadius={15} backgroundColor={useColorModeValue('gray.100', 'gray.900')}>
              <CardHeader>
                <Text fontSize={{ base: "lg", md: "xl" }} fontWeight="bold">Value in Money</Text>
              </CardHeader>
              <CardBody>
                <Box display="flex" alignItems="center" justifyContent="center" flexDirection={{ base: "column", md: "row" }}>
                  <Box mb={{ base: 4, md: 0 }}><MonetizationOnIcon sx={{ fontSize: '4rem', color: "#457b9d" }} /></Box>
                  <Text fontSize={{ base: "xl", md: "2xl" }} textAlign="center">{usageCost}</Text>
                </Box>
              </CardBody>
            </Card>
          </Box>
        </Box>

        <Box mb={6}>
          <Heading as="h2" size="md" mb={4} textAlign="center">Weekly Token Usage</Heading>
          <BarChart width={breakpointValue === "full" ? 300 : 600} height={300} data={tokenChartData}>
            <XAxis dataKey="chat_id" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="tokenCount" fill="#82ca9d" />
          </BarChart>
        </Box>

        <Box mb={6}>
          <Heading as="h2" size="md" mb={4} textAlign="center">Monthly Token Usage</Heading>
          <BarChart width={breakpointValue === "full" ? 300 : 600} height={300} data={monthlyUsageData}>
            <XAxis dataKey="month" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="tokenCount" fill="#8884d8" />
          </BarChart>
        </Box>

        <Box mb={12}>
          <Heading as="h2" size="md" mb={4} textAlign="center">Summary</Heading>
          <Stack direction="row" mb={4} spacing={5} justifyContent="center">
            <RadioGroup onChange={(value) => setCurrency(parseInt(value, 10))} value={currency}>
              <Stack direction='row' spacing={5}>
                <Radio value={1} colorScheme="teal">LKR</Radio>
                <Radio value={2} colorScheme="teal">$</Radio>
              </Stack>
            </RadioGroup>
          </Stack>

          {isLoading ? (
            <Text textAlign="center">Loading data...</Text>
          ) : (
            <Box overflowX="auto">
              <Table variant="simple">
                <Thead>
                  <Tr>
                    <Th>Chat ID</Th>
                    <Th>Total Token Count</Th>
                    <Th>Total Cost</Th>
                    <Th>Total Latency</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {summaryData.map((row) => (
                    <Tr
                      key={row.chat_id}
                      _hover={{ bg: useColorModeValue("gray.50", "gray.600") }}
                      onClick={() => combinedFunc(row.chat_id, true)}
                    >
                      <Td>{row.chat_id}</Td>
                      <Td>{row.tokenCount}</Td>
                      <Td>{currency === 1 ? `LKR ${(row.cost * 300).toFixed(3)}` : `$ ${row.cost.toFixed(3)}`}</Td>
                      <Td>{row.latency} Second/s</Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            </Box>
          )}

          {selectedChatId && (
            <Modal
              isOpen={showDetailsModal}
              onClose={() => setShowDetailsModal(false)}
            >
              <ModalOverlay />
              <ModalContent w={{ base: "90%", md: "800px" }} maxW="1000px">
                <ModalHeader>Chat Details</ModalHeader>
                <ModalCloseButton />
                <ModalBody>
                  <DetailsCard
                    chatId={selectedChatId}
                    details={
                      summaryData.find(row => row.chat_id === selectedChatId)?.details
                    }
                  />
                </ModalBody>
              </ModalContent>
            </Modal>
          )}
        </Box>
      </Container>
      <Footer padding={0} />
    </Box>
  );
}
export default UsageCostPage;