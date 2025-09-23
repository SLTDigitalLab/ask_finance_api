import re
import logging
from typing import Optional
import spacy
from langchain import LLMChain, PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langgraph.graph.message import add_messages
from .app_types import AgentState

logger = logging.getLogger(__name__)
nlp = spacy.load("en_core_web_sm")

def detect_intent_with_context(query: str, destination_context: str = None) -> str:
    """
    Enhanced intent detection that considers destination context.
    This is the key fix for bidirectional context usage.
    """
    vague_patterns = [
        "there", "that place", "it", "its", "their", "this place",
        "what about", "tell me about", "places there", "things there",
        "attractions there", "sites there", "visit there"
    ]
    
    enhanced_query = query
    is_vague_query = any(pattern in query.lower() for pattern in vague_patterns)
    
    if is_vague_query and destination_context:
        enhanced_query = f"{query} {destination_context}"
        logger.info(f"Enhanced vague query: '{query}' → '{enhanced_query}' (using destination: {destination_context})")
    
    return detect_intent(enhanced_query)

def detect_intent(query: str) -> str:
    """
    Unified intent detection for queries:
    - DOCUMENT (knowledge/document retrieval intent)
    - NONE (no clear intent)
    """

    try:
        doc = nlp(query)

        has_booking_verbs = any(
            token.lemma_ in ["book", "reserve", "make", "get", "find", "search", "stay"]
            for token in doc if token.pos_ == "VERB"
        )
        has_accommodation_nouns = any(
            token.lemma_ in ["hotel", "room", "accommodation", "stay", "booking", "reservation", "lodge", "inn"]
            for token in doc if token.pos_ == "NOUN"
        )
        has_temporal_references = any(
            token.lemma_ in ["tonight", "tomorrow", "today", "date", "night", "week", "month", "weekend"]
            for token in doc
        )

        has_movement_verbs = any(
            token.lemma_ in ["go", "get", "reach", "travel", "move", "navigate", "drive", "walk", "come", "head", "visit"]
            for token in doc if token.pos_ == "VERB"
        )
        has_location_entities = any(ent.label_ in ["GPE", "LOC", "FAC"] for ent in doc.ents)
        has_directional_words = any(
            token.lemma_ in ["direction", "route", "way", "path", "road", "highway", "map"]
            for token in doc if token.pos_ == "NOUN"
        )
        has_spatial_references = any(
            token.lemma_ in ["there", "here", "place", "from", "to", "near", "around"]
            for token in doc if token.pos_ in ["ADV", "NOUN", "ADP"]
        )
        has_from_to_pattern = bool(re.search(r"from\s+.+\s+to\s+", query, re.IGNORECASE))

        document_keywords = [
            "policy", "procedure", "document", "manual", "guide", "regulation",
            "specification", "requirement", "standard", "report", "analysis",
            "data", "information", "details", "explain", "what is", "how does",
            "definition", "overview", "summary",

            "places", "attractions", "sites", "things to do", "visit",
            "famous", "popular", "best", "top", "interesting", "beautiful",
            "culture", "history", "food", "restaurants", "temples", "museums",
            "shopping", "activities", "events", "festivals", "weather",
            "about", "regarding", "concerning", "tell me", "what are",
            "list", "show me", "recommend", "suggest"
        ]
        query_lower = query.lower()
        has_document_keywords = any(keyword in query_lower for keyword in document_keywords)

        document_question_patterns = [
            r"what\s+(are|is)\s+",
            r"tell\s+me\s+about",
            r"famous\s+\w+\s+in",
            r"places\s+in",
            r"things\s+to\s+do",
            r"attractions\s+in",
            r"sites\s+in",
            r"best\s+\w+\s+in",
            r"popular\s+\w+\s+in",
            r"interesting\s+\w+\s+in",
        ]
        has_document_patterns = any(re.search(pattern, query_lower) for pattern in document_question_patterns)

        prompt = PromptTemplate.from_template(
            """Classify the user's intent into one of these categories:
- BOOKING: if the user wants to book, reserve, or find accommodation (hotel, room, etc.)
- MAPPING: if the user wants directions, navigation, or routes between places
- DOCUMENT: if the user asks for information, details, places to visit, attractions, things to do, or general knowledge
- NONE: if none of the above apply

IMPORTANT: Questions about "places in X", "things to do in X", "attractions in X", "famous X in Y" should be classified as DOCUMENT.

Linguistic analysis:
- Query: "{query}"
- Booking verbs: {has_booking_verbs}
- Accommodation nouns: {has_accommodation_nouns}
- Temporal references: {has_temporal_references}
- Movement verbs: {has_movement_verbs}
- Location entities: {has_location_entities}
- Directional words: {has_directional_words}
- Spatial references: {has_spatial_references}
- From-to pattern: {has_from_to_pattern}
- Document keywords: {has_document_keywords}
- Document patterns: {has_document_patterns}

Examples:
- "famous places in kandy" → DOCUMENT
- "places there" → DOCUMENT  
- "things to do there" → DOCUMENT
- "how to go there" → MAPPING
- "directions to kandy" → MAPPING
- "book hotel there" → BOOKING

Answer with only one label: BOOKING, MAPPING, DOCUMENT, or NONE.
"""
        )

        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0,
            convert_system_message_to_human=True
        )
        chain = LLMChain(llm=llm, prompt=prompt)

        result = chain.run(
            query=query,
            has_booking_verbs=has_booking_verbs,
            has_accommodation_nouns=has_accommodation_nouns,
            has_temporal_references=has_temporal_references,
            has_movement_verbs=has_movement_verbs,
            has_location_entities=has_location_entities,
            has_directional_words=has_directional_words,
            has_spatial_references=has_spatial_references,
            has_from_to_pattern=has_from_to_pattern,
            has_document_keywords=has_document_keywords,
            has_document_patterns=has_document_patterns
        )

        intent = result.strip().upper()
        if intent not in ["BOOKING", "MAPPING", "DOCUMENT", "NONE"]:
            intent = "NONE"

        logger.info(f"Enhanced intent detection for '{query}': {intent}")
        return intent

    except Exception as e:
        logger.error(f"Enhanced intent detection failed: {e}")
        
        query_lower = query.lower()

        document_fallback_patterns = [
            "places", "attractions", "sites", "things to do", "visit",
            "famous", "popular", "best", "top", "interesting",
            "what are", "tell me", "about", "culture", "history",
            "food", "restaurants", "temples", "museums", "weather"
        ]
        
        if any(pattern in query_lower for pattern in document_fallback_patterns):
            logger.info(f"Fallback: Classified '{query}' as DOCUMENT")
            return "DOCUMENT"

        if any(word in query_lower for word in ["book", "reserve", "hotel", "room", "stay", "accommodation"]):
            logger.info(f"Fallback: Classified '{query}' as BOOKING")
            return "BOOKING"

        if re.search(r"from\s+.+\s+to\s+", query_lower) or \
           any(word in query_lower for word in ["direction", "route", "navigate", "map", "how to get", "how to go"]):
            logger.info(f"Fallback: Classified '{query}' as MAPPING")
            return "MAPPING"

        logger.info(f"Fallback: Classified '{query}' as NONE")
        return "NONE"