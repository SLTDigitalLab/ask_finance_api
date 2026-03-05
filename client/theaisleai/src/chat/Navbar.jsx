import React, { useState, useEffect } from "react";
import {
  Button,
  Flex,
  Heading,
  Image,
  Link,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  useColorModeValue,
  IconButton,
  Box,
  useColorMode,
  VStack,
  HStack,
  Text,
  Spinner,
} from "@chakra-ui/react";
import { NavLink, useNavigate, useParams, useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import DarkModeIcon from "@mui/icons-material/DarkMode";
import LightModeIcon from "@mui/icons-material/LightMode";
import AccountCircleIcon from "@mui/icons-material/AccountCircle";
import MenuIcon from "@mui/icons-material/Menu";
import ManageAccountsIcon from "@mui/icons-material/ManageAccounts";
import AddOutlinedIcon from "@mui/icons-material/AddOutlined";
import DeleteOutlinedIcon from "@mui/icons-material/DeleteOutlined";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import { useDispatch, useSelector } from "react-redux";
import axios from "axios";
import { AUTH } from "../urls";
import { setIsLoggedIn, setUser } from "../redux/reducers/userSlice";

const MotionFlex = motion(Flex);
const MotionButton = motion(Button);
const MotionMenuItem = motion(MenuItem);
const MotionIconButton = motion(IconButton);

function NavBar() {
  const location = useLocation();
  const linkColor = useColorModeValue("gray.600", "gray.200");
  const buttonBgColor = useColorModeValue("gray.100", "gray.900");
  const buttonTextColor = useColorModeValue("gray.800", "gray.200");
  const titleColor = useColorModeValue("gray.800", "gray.100");

  const navigate = useNavigate();
  const { isLoggedIn, userObj } = useSelector((state) => state.user);
  const dispatch = useDispatch();
  const { domain } = useParams();

  const { colorMode, toggleColorMode } = useColorMode();

  const [checkingAuth, setCheckingAuth] = useState(false);

  const [activeSubMenu, setActiveSubMenu] = useState(null);

  // Check Authentication Status when DOMAIN changes
  useEffect(() => {
    // If we are on the root /chat (no domain), we don't check auth or allow login
    if (!domain) {
        dispatch(setIsLoggedIn(false));
        setCheckingAuth(false);
        return;
    }

    const checkAuthStatus = async () => {
      setCheckingAuth(true);
      try {
        // Pass the specific domain to check if we are logged in THERE
        const res = await axios.get(`${AUTH.CHECK_AUTH}?domain=${domain}`, { 
            withCredentials: true,
            timeout: 5000
        });
        
        if (res.data.authenticated) {
          dispatch(setIsLoggedIn(true));
          dispatch(setUser({
            ...userObj,
            firstName: res.data.name,
            email: res.data.email,
          }));
        } else {
          dispatch(setIsLoggedIn(false));
        }
      } catch (err) {
        dispatch(setIsLoggedIn(false));
      } finally {
        setCheckingAuth(false);
      }
    };
    
    checkAuthStatus();
  }, [dispatch, domain]); // Re-run when domain changes

  const handleLogin = () => {
    if (domain) {
        const loginUrl = `${AUTH.LOGIN}?domain=${domain}`;
        console.log("Redirecting to:", loginUrl); // <--- Check Console
        window.location.href = loginUrl;
    } else {
        console.error("No domain found, cannot login.");
    }
  };

  const handleLogout = () => {
    if (domain) {
        // Logout specifically from this domain
        window.location.href = `${AUTH.LOGOUT}?domain=${domain}`;
    } else {
        window.location.href = AUTH.LOGOUT;
    }
  };

  const formatDomainName = (domainName) => {
    if (!domainName) return "ASK FINANCE";
    return `${domainName
      .split("_")
      .map((word) => word.toUpperCase())
      .join(" ")}`;
  };

  const displayName = formatDomainName(domain);

  return (
    <MotionFlex
      as="nav"
      w={{ base: "92%", md: "98%" }}
      mx="auto"
      bg={useColorModeValue("gray.100", "gray.900")}
      color={linkColor}
      py={4}
      px={4}
      align="center"
      justify="space-between"
      borderRadius={25}
      m={15}
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 1.5 }}
      position="relative"
      zIndex="2"
    >
      {/* Left: Logo */}
      <Heading as="h1" size="lg">
        <MotionButton
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          bg={buttonBgColor}
        >
          <Link as={NavLink} to="/" exact="true">
            <Image src="/12.png" alt="AisleAI Logo" w="50px" />
          </Link>
        </MotionButton>
      </Heading>

      {/* Center: ASK FINANCE (absolute centered) */}
      {/* Center: ASK FINANCE (stylized, larger) */}
      <Box
        position="absolute"
        left="50%"
        transform="translateX(-50%)"
        textAlign="center"
        pointerEvents="none" // keep behind-clicks working
      >
        <Heading
          as="h2"
          // responsive size: sm → xl, md → 2xl, lg+ → 3xl
          fontSize={{ base: "xl", md: "2xl", lg: "3xl" }}
          fontWeight="extrabold"
          letterSpacing="wider"
          lineHeight="1.1"
          bgGradient={useColorModeValue(
            "linear(to-r, teal.500, blue.500)",
            "linear(to-r, teal.200, blue.300)"
          )}
          bgClip="text"
          // soft glow
          sx={{
            textShadow: useColorModeValue(
              "0 0 10px rgba(56,178,172,0.35), 0 0 18px rgba(66,153,225,0.25)",
              "0 0 10px rgba(129,230,217,0.45), 0 0 18px rgba(144,205,244,0.35)"
            ),
          }}
        >
          {displayName}
        </Heading>

        {/* Accent underline */}
        <Box
          mx="auto"
          mt={1}
          h="3px"
          w={{ base: "60px", md: "80px" }}
          borderRadius="full"
          bgGradient={useColorModeValue(
            "linear(to-r, teal.400, blue.400)",
            "linear(to-r, teal.300, blue.300)"
          )}
          opacity={0.85}
        />
      </Box>

      {/* Desktop actions (Right) */}
      <Flex display={{ base: "none", md: "flex" }} align="center" gap={6}>
        {checkingAuth ? (
          <Spinner size="sm" />
        ) : isLoggedIn && domain ? (
          <HStack spacing={4}>
            <Text fontSize="sm" fontWeight="bold" display={{ base: "none", md: "block" }}>
              Hi, {userObj.firstName}
            </Text>
            <Button size="sm" colorScheme="red" variant="ghost" onClick={handleLogout}>
              Logout
            </Button>
          </HStack>
        ) : domain ? (
            // Only show login button if a domain is present
          <Button size="sm" colorScheme="blue" onClick={handleLogin}>
            Login with Microsoft
          </Button>
        ) : (
            // No button on root /chat
            <Box w="100px" /> 
        )}

        {/* Dark Mode Toggle */}
        <MotionIconButton
          aria-label="Toggle dark mode"
          icon={colorMode === "light" ? <DarkModeIcon /> : <LightModeIcon />}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          onClick={toggleColorMode}
          variant="ghost"
        />
      </Flex>

      {/* ✅ Mobile menu - show only when NOT on iframe route */}
      {!location.pathname.includes("/iframe") && (
        <Box display={{ base: "flex", md: "none" }}>
          <Menu closeOnSelect={false}>
            <MenuButton as={IconButton} icon={<MenuIcon />} variant="outline" />
            <MenuList>
              {isLoggedIn && domain && (
                <VStack align="start" spacing={0}>
                  <MotionMenuItem as={NavLink} to={`/${domain}/chat`}>Chat</MotionMenuItem>
                  <MotionMenuItem as={NavLink} to="/profile">Profile</MotionMenuItem>
                  <MotionMenuItem onClick={handleLogout}>Logout</MotionMenuItem>
                </VStack>
              )}

              {/* Dark mode toggle */}
              <MotionMenuItem onClick={toggleColorMode}>
                {colorMode === "light" ? "Dark Mode" : "Light Mode"}
              </MotionMenuItem>
              
              {!isLoggedIn && domain && (
                 <MotionMenuItem onClick={handleLogin}>Login with Microsoft</MotionMenuItem>
              )}
            </MenuList>
          </Menu>
        </Box>
      )}
    </MotionFlex>
  );
}
export default NavBar;
