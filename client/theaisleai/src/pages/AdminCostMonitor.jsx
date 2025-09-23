import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import {
    Box,
    Container,
    Heading,
    Tabs,
    Tab,
    TabList,
    useColorModeValue,
    TabPanels,
    TabPanel,
    Spinner,
    useToast,
} from "@chakra-ui/react";
import Footer from '../components/Footer';
import { BarChart, Bar, XAxis, YAxis, Legend, Tooltip, ResponsiveContainer } from 'recharts';
import { USAGE } from '../urls';

const calculateTierUsageData = (summaryData = []) => {
    if (!Array.isArray(summaryData)) return []; 
    const monthlyData = {};

    summaryData.forEach((item) => {
        if (!item.timestamp) return;

        const date = new Date(item.timestamp);
        const month = `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, "0")}`;

        if (!monthlyData[month]) {
            monthlyData[month] = { tokenCount: 0, cost: 0 };
        }
    
        monthlyData[month].tokenCount += item.token_count;
        monthlyData[month].cost += item.cost;
    });

    return Object.entries(monthlyData).map(([month, data]) => ({
        month,
        tokenCount: data.tokenCount,
        cost: data.cost,
    }));
};

const calculateTotalPerModel = (allData) => {
    return allData.map((modelData, index) => {
        const totalTokens = modelData.reduce((sum, item) => sum + item.token_count, 0);
        return {
            model: modelNames[index + 1], // Skip 'Total' in modelNames
            tokenCount: totalTokens
        };
    });
};

const getCurrentMonthName = () => {
    const date = new Date();
    return date.toLocaleString('default', { month: 'long' });
};

// Model names with Total added
const modelNames = [
    'Total',
    'Sparkly',
    'Oracle',
    'Ethereal',
    'Granite',
    'GPT-3.5',
    'GPT-4',
    'GPT-4o',
    'Claude',
    'Neo',
    'DeepSeek',
];

function AdminCostMonitor() {
    const [selectedModel, setSelectedModel] = useState(0);
    const [monthlyTierData, setMonthlyTierData] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const toast = useToast();

    const handleTabChange = (index) => {
        setSelectedModel(index);
    };

    useEffect(() => {
        const fetchData = async () => {
            setIsLoading(true);
            try {
                const token = localStorage.getItem("authToken");
                
                if (selectedModel === 0) { // Total tab
                    // Fetch data for all models
                    const allResponses = await Promise.all(
                        modelNames.slice(1).map(model => 
                            axios.get(`${USAGE.GET_TIER_COST}/${model}`, {
                                headers: { Authorization: `Bearer ${token}` },
                            })
                        )
                    );
                    const allData = allResponses.map(response => response.data.result);
                    const totalData = calculateTotalPerModel(allData);
                    setMonthlyTierData(totalData);
                } else { // Individual model tabs
                    const response = await axios.get(`${USAGE.GET_TIER_COST}/${modelNames[selectedModel]}`, {
                        headers: { Authorization: `Bearer ${token}` },
                    });
                    const tierData = calculateTierUsageData(response.data.result);
                    setMonthlyTierData(tierData);
                }
                
            } catch (error) {
                toast({
                    title: "Error fetching data",
                    description: "Could not fetch token usage data.",
                    status: "error",
                    duration: 5000,
                    isClosable: true,
                });
                console.error("Error fetching tier data: ", error);
            } finally {
                setIsLoading(false);
            }
        };
        fetchData();
    }, [selectedModel]);

    return (
        <Container maxW="100vw" display="flex" flexDirection="column" minH="80vh">
            <Tabs size="md" variant="unstyled" onChange={handleTabChange}>
                <Box display={{ base: "block", lg: "flex" }} alignItems="flex-start" justifyContent="flex-start">
                    {/* Sidebar */}
                    <Container
                        w={{ base: "100%", lg: "30%" }}
                        display="flex"
                        flexDirection="column"
                        overflowY="auto"
                        minH={{ base: "auto", lg: "80vh" }}
                        bg={useColorModeValue("gray.100", "gray.900")}
                        p={4}
                        m={{ base: 2, lg: 5 }}
                        borderRadius="15px"
                        boxShadow="lg"
                    >
                        <TabList flexDirection="column" py={3}>
                            <Heading mt={1} mb={6} fontSize={20} fontWeight="bold" textAlign="center">
                                Models
                            </Heading>
                            {modelNames.map((model, index) => (
                                <Tab 
                                    key={index} 
                                    p={2} 
                                    _selected={{ bg: "#457b9d", color: "white" }} 
                                    borderRadius="md"
                                >
                                    {model}
                                </Tab>
                            ))}
                        </TabList>
                    </Container>

                    {/* Main Content */}
                    <Box
                        w={{ base: "100%", lg: "70%" }}
                        p={4}
                        overflowY="auto"
                        display="flex"
                        flexDirection="column"
                        justifyContent="flex-start"
                        alignItems="flex-start"
                    >
                        <TabPanels>
                            {modelNames.map((model, index) => (
                                <TabPanel key={index}>
                                    <Box
                                        bg={useColorModeValue("white", "gray.800")}
                                        p={6}
                                        shadow="xl"
                                        borderRadius="lg"
                                        maxW="100%"
                                        w="full"
                                        mb={4}
                                        boxShadow="0px 8px 16px rgba(0, 0, 0, 0.2)"
                                    >
                                        <Heading size="md" mb={5} textAlign="center">
                                            {model === 'Total' ? 
                                                `Total Token Count : ${getCurrentMonthName()}` : 
                                                `Monthly Token Count (${getCurrentMonthName()})`
                                            }
                                        </Heading>
                                        {isLoading ? (
                                            <Box display="flex" justifyContent="center" alignItems="center" height="400px">
                                                <Spinner size="xl" />
                                            </Box>
                                        ) : (
                                            <ResponsiveContainer width="100%" height={400}>
                                                <BarChart 
                                                    width={600} 
                                                    height={400} 
                                                    data={monthlyTierData}
                                                    margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                                                >
                                                    <XAxis 
                                                        dataKey={model === 'Total' ? 'model' : 'month'} 
                                                        angle={model === 'Total' ? -45 : 0}
                                                        textAnchor={model === 'Total' ? 'end' : 'middle'}
                                                        height={model === 'Total' ? 60 : 30}
                                                    />
                                                    <YAxis />
                                                    <Tooltip />
                                                    <Legend />
                                                    <Bar dataKey="tokenCount" fill="#8884d8" />
                                                </BarChart>
                                            </ResponsiveContainer>
                                        )}
                                    </Box>
                                </TabPanel>
                            ))}
                        </TabPanels>
                    </Box>
                </Box>
            </Tabs>
            <Footer />
        </Container>
    );
}

export default AdminCostMonitor;