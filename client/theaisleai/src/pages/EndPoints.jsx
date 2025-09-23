
import { useState,useEffect } from 'react';
import {
    FormLabel,
    Input,
    Button,
    Select,
    useToast,
    Container,
    useColorModeValue,// For dynamic colors
    Heading,
    VStack, // For vertical stacking
    Box // For general container layout if needed
    
} from '@chakra-ui/react';
import { END_POINTS } from '../urls'; 


import axios from "axios";


function EndPoints() {
    const toast = useToast();
    const [awsCredentials, setAwsCredentials] = useState([]);
    const [selectedBucket, setSelectedBucket] = useState('');
    const [bucketFiles, setBucketFiles] = useState([]);
    const [fileList, setFileList] = useState([]); // State to hold files
    // Dynamic colors for light and dark modes
    const bgColor = useColorModeValue("gray.100", "gray.700"); // Background color
    const textColor = useColorModeValue("gray.800", "white"); // Text color

    const listBucketFiles = async () => {
      console.log(selectedBucket)
      if (!selectedBucket) return; // Check if a bucket is selected
  
      try {
        const token = localStorage.getItem("authToken");
        const requestBody = { bucket_name: selectedBucket };
        const response = await axios.post(
          END_POINTS.LIST_BUCKET_FILES,
          requestBody, 
          {
            headers: { Authorization: `Bearer ${token}` },
          }
        );
        console.log(response.data)
        setFileList(response.data.result); // Assuming response.data.files exists
      } catch (error) {
        console.error("Error fetching file list:", error);
        toast({
          title: "Error",
          description: "Failed to fetch file list",
          status: "error",
          duration: 3000,
          isClosable: true,
        });
      }
    };

    useEffect(() => {
      listBucketFiles(); // Fetch file list initially if a bucket is selected
    }, [selectedBucket]); // Refetch when selected bucket changes
  

    const [apiDetails, setApiDetails] = useState({
        type: 's3',
        aws_access_key_id: '',
        aws_secret_access_key: '',
        bucket_name: '',
      });

      
      const downloadFileByIndex = async (index, bucketName) => {
        try {
          console.log(index,bucketName)
          const token = localStorage.getItem("authToken");
          const requestBody = { bucket_name: bucketName, file_index: index };
          const response = await axios.post(
            END_POINTS.DOWNLOAD_BUCKET_FILE,
            requestBody, 
            {
              headers: { Authorization: `Bearer ${token}` },
            }
          );
      
          // **Assumption:** Your backend already sets the correct headers 
          // to trigger a file download with the right filename. If not, you'll
          // need to adjust the backend.
      
        } catch (error) {
          console.error("Error downloading file:", error);
          // Handle error
        }
      };

      useEffect(() => {
        const fetchAwsCredentials = async () => {
          try {
            const token = localStorage.getItem("authToken");
            const response = await axios.get(END_POINTS.LIST_AWS_CREDENTIALS, { // Change to your API endpoint
              headers: { Authorization: `Bearer ${token}` },
            });
            console.log(response)
            setAwsCredentials(response.data);
          } catch (error) {
            console.error("Error fetching AWS credentials:", error);
            // Handle error (e.g., display error message)
          }
        };
    
        fetchAwsCredentials();
      }, []); 


      const handleSubmit = async (e) => {
        e.preventDefault();
      
        try {
            const token = localStorage.getItem("authToken");
            console.log(apiDetails)
            const response = await axios.post(
                END_POINTS.AWS_AUTHENTICATE,
                apiDetails,
                {
                  headers: { Authorization: `Bearer ${token}` },
                }
              );
              toast({
                title: "Authenticated",
                status: "success",
                duration: 3000,
                isClosable: true,
              });
            
          } catch (error) {
            console.error("Chat error:", error);
            toast({
              title: "Not Authenticated",
              status: "error",
              duration: 3000,
              isClosable: true,
            });
          } 

        }
          
    return (
      <Container>
        <Box> {/* Use Box for additional layout if needed */}
              <Heading as="h1" size="lg" textAlign="center" mt={8} mb={4}>
          AWS Endpoint
      </Heading>
      <Heading as="h3" backgroundColor={bgColor} borderRadius={15} padding={5} size="sm" textAlign="left" mt={8} mb={4}>
          Authentication
      </Heading>
      <VStack spacing={4} as="form" onSubmit={handleSubmit}>
        <FormLabel htmlFor="type">API Type</FormLabel>
        <Select id="type" onChange={(e) => setApiDetails({ ...apiDetails, type: e.target.value })}>
          <option value="s3">S3</option>
          {/* Add more options as needed */}
        </Select>

        <FormLabel htmlFor="aws_access_key_id">AWS Access Key ID</FormLabel>
        <Input
          id="aws_access_key_id"
          type="text"
          value={apiDetails.aws_access_key_id}
          onChange={(e) => setApiDetails({ ...apiDetails, aws_access_key_id: e.target.value })}
        />

<FormLabel htmlFor="aws_secret_access_key">AWS Seceret Access Key ID</FormLabel>
        <Input
          id="aws_secret_access_key"
          type="text"
          value={apiDetails.aws_secret_access_key}
          onChange={(e) => setApiDetails({ ...apiDetails, aws_secret_access_key: e.target.value })}
        />

<FormLabel htmlFor="bucket_name">AWS Bucket Name</FormLabel>
        <Input
          id="bucket_name"
          type="text"
          value={apiDetails.bucket_name}
          onChange={(e) => setApiDetails({ ...apiDetails, bucket_name: e.target.value })}
        />

        {/* Similar fields for aws_secret_access_key and bucket_name */}

        <Button type="submit" bg='#457B9D' colorScheme="#ffffff" _hover={{ bg: "#2c5a6d" }} textColor={useColorModeValue("white", "white")}>
          Submit
        </Button>
      </VStack>
      <Heading as="h3" backgroundColor={bgColor} borderRadius={15} padding={5} size="sm" textAlign="left" mt={8} mb={4}>
          Choose a Bucket
      </Heading>
      <VStack spacing={4}> {/* Added a VStack around the dropdown */}
  <FormLabel htmlFor="aws_credentials"></FormLabel>
  {awsCredentials && awsCredentials.length > 0 ? (
    <Select id="aws_credentials" onChange={(e) => {
      const selectedIndex = e.target.value;
      console.log(selectedIndex);
      // Check if the "Select Buckets" option was chosen
      if (selectedIndex != "0") { 
        // console.log("asdasd")
          const selectedBucket = awsCredentials[selectedIndex-1].bucket_name;
          setSelectedBucket(selectedBucket);
      }
  }}>
    <option key="select-bucket" value={0}>Select Buckets</option> 
    {awsCredentials.map((entry, index) => (
      entry.bucket_name && entry.type && entry.aws_access_key_id ? ( 
        <option key={index + 1} value={index + 1}> {/* Adjusted indices */}
          {entry.bucket_name} ({entry.type}, {entry.aws_access_key_id}) 
        </option>
      ) : null 
    ))}
  </Select>
  ) : (
    <p>No AWS credentials found.</p> // Placeholder if no data exists
  )} 
</VStack>
        <Heading as="h3" backgroundColor={bgColor} borderRadius={15} padding={5} size="sm" textAlign="left" mt={8} mb={4}>
                  Choose files to be Uploaded
              </Heading>
              <VStack spacing={4}>
        {fileList.length > 0 ? (
          <ul>
            {fileList.map((file,index) => (
              <li key={index}>
                {file} 
                <Button onClick={() => downloadFileByIndex(index, selectedBucket)} bg='#457b9d' colorScheme="#ffffff">Download</Button> 
                </li>
            ))}
          </ul>
        ) : (
           <p>No files found or bucket not selected.</p>
        )}
      </VStack>

            </Box>
    </Container>
    )
}

export default EndPoints;