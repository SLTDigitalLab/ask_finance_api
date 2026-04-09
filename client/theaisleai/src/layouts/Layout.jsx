// import {Outlet} from "react-router-dom"
// import Navbar from "../chat/Navbar"
// import {ChakraProvider, Container} from '@chakra-ui/react'

// export default function Layout() {

//     return (
//         <ChakraProvider>
//             <div style={{ flexGrow: 1 }}> {/* Key addition */}
//             <Navbar/>
//                 <Outlet/>
//             </div>
//         </ChakraProvider>
//     )
// }

import { Outlet } from "react-router-dom"
import Navbar from "../chat/Navbar"
import { ChakraProvider } from '@chakra-ui/react'

export default function Layout() {
  return (
    <ChakraProvider>
      <div
        style={{
          minHeight: "100vh",
          display: "flex",
          flexDirection: "column"
        }}
      >
        <Navbar />

        <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
          <Outlet />
        </div>

      </div>
    </ChakraProvider>
  )
}