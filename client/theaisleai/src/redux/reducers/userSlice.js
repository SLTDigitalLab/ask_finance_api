import {createSlice} from "@reduxjs/toolkit";

export const userSlice = createSlice({
    name: "user",
    initialState: {
        userObj: {
            firstName: "",
            lastName: "",
            tel: "",
            email: "",
            role: "",
            isDisabled: false,
            telVerified: false,
            emailVerified: false,
        },
        isLoggedIn: false,
        userTier: "", 
        apiKey: "",
        tokenCost: 0,
        usageCost: 0,
        currency: 1
    },
    reducers: {
        setUser: (state, action) => {
            state.userObj = action.payload;
        },
        setIsLoggedIn: (state, action) => {
            state.isLoggedIn = action.payload;
        },
        setUserTier: (state, action) => {
            state.userTier = action.payload;
        },
        setApiKey: (state,action) => {
            state.apiKey = action.payload;
        },
        setTokenCost: (state,action) => {
            state.tokenCost = action.payload;
        },
        setUsageCost: (state, action) => {
            state.usageCost = action.payload;
        },
        resetUserState: (state) => {
            state.userObj = {
                firstName: "",
                lastName: "",
                tel: "",
                email: "",
                role: "",
                isDisabled: false,
                telVerified: false,
                emailVerified: false,
            };
            state.isLoggedIn = false;
            state.userTier = "";
            state.apiKey = "";
            state.tokenCost = 0;
            state.usageCost = 0;
            state.currency = 1;
        },
        setCurrency: (state) => {
            state.currency = action.payload;
        }
    },
});

// Action creators are generated for each case reducer function
export const {
    setUser, setIsLoggedIn, setApiKey, setTokenCost,
    setUsageCost, setUserTier,resetUserState, setCurrency
} = userSlice.actions;

export default userSlice.reducer;
