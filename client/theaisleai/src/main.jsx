import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import store, { persistor } from './redux/store.js';
import { Provider } from 'react-redux';
import { PersistGate } from 'redux-persist/integration/react';
import { ChakraProvider, ColorModeProvider, extendTheme } from '@chakra-ui/react';

// Extend the theme to include custom configurations
const theme = extendTheme({
  config: {
    initialColorMode: 'light', // Set the initial color mode (light or dark)
    useSystemColorMode: false, // Disable using the system color mode
  },
});

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <Provider store={store}>
      <PersistGate loading={null} persistor={persistor}>
        <ChakraProvider theme={theme}>
          <ColorModeProvider options={{ useSystemColorMode: false }}>
            <App />
          </ColorModeProvider>
        </ChakraProvider>
      </PersistGate>
    </Provider>
  </React.StrictMode>
);