from typing_extensions import TypedDict, Annotated
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph.message import add_messages
from typing import List, Union, Dict, Optional

class AgentState(TypedDict):
    messages: Annotated[List[Union[HumanMessage, AIMessage, SystemMessage]], add_messages]
    query: str
    answer: str
    sources: List[str]
    pages: List[int]
    chat_id: str
    search_results: Optional[str]
    document_context: Optional[str]
    reasoning_chain: List[str]
    needs_map: bool
    map_link: Optional[str]
    booking_details: Optional[Dict]
    booking_options: Optional[Dict]
