export const BASE_URL = "http://localhost:8000/"
// export const BASE_URL = "https://askhr.sltdigitallab.lk/"

export const CHAT = {
    CHAT_API_URL: BASE_URL + "api/v1/chat/vector_multi",
    CHAT_HISTORY_API_URL: BASE_URL + "api/v1/chat/history",
    COLLECTIONS_API_URL: BASE_URL + "api/v1/stores/vector/collections",
    GET_CHAT_HISTORY: BASE_URL + "api/v1/chat/history_get",
    DELETE_LOCAL_CACHE: BASE_URL + "api/v1/chat/deletecache",
    CHAT_HEADER: BASE_URL + "api/v1/chat/history/header",
    GET_PDF: BASE_URL + "api/v1/chat/get-pdf",
    MULTI_AGENT_CHAT: BASE_URL + "api/v1/chat"
}

export const END_POINTS = {
    AWS_AUTHENTICATE: BASE_URL + "api/v1/authenticate-aws-users",
    LIST_AWS_CREDENTIALS: BASE_URL + "api/v1/aws-buckets",
    LIST_BUCKET_FILES: BASE_URL + "api/v1/list-bucket-files",
    DOWNLOAD_BUCKET_FILE: BASE_URL + "api/v1/download-bucket-file"
}

export const USAGE = {
    GET_COST: BASE_URL + "api/v1/chat/usage_cost",
    GET_TIER_COST: BASE_URL + "api/v1/chat/tier_cost",
    GET_TOKEN_COST: BASE_URL + "api/v1/users/tokencost",
    GET_USAGE_COST: BASE_URL + "api/v1/users/usagecost"
}
