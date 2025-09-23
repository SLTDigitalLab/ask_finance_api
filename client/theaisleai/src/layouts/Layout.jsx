import {Outlet} from "react-router-dom"
import Navbar from "../chat/Navbar"
import {ChakraProvider, Container} from '@chakra-ui/react'

export default function Layout() {

    return (
        <ChakraProvider>
            <div style={{ flexGrow: 1 }}> {/* Key addition */}
            <Navbar/>
                <Outlet/>
            </div>
        </ChakraProvider>
    )
}