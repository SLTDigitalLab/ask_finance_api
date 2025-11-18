import logging
from typing import Optional, Dict, Any, List
import spacy
from datetime import datetime
import re

logger = logging.getLogger(__name__)

# Load spaCy for entity extraction
try:
    nlp = spacy.load("en_core_web_sm")
except:
    logger.warning("spaCy model not found, install with: python -m spacy download en_core_web_sm")
    nlp = None

PRONOUNS = {"there", "here", "this", "that", "it", "they", "them", "we", "us", "you", "your"}
VAGUE_PATTERNS = [
    r'\bit\b', r'\bthat\b', r'\bthis\b', r'\bthose\b', r'\bthey\b', 
    r'\bthem\b', r'\babout it\b', r'\bexplain it\b', r'\btell me about\b'
]


class EnhancedContextManager:
    """
    Multi-agent conversation context manager with improved entity tracking
    and follow-up question handling.
    """

    def __init__(self):
        # Agent-specific contexts per chat
        self.agent_contexts: Dict[str, Dict[str, Dict[str, Any]]] = {}
        # Global agent contexts
        self.global_contexts: Dict[str, Dict[str, Any]] = {}
        # Entity memory per chat
        self.entity_memory: Dict[str, Dict[str, Any]] = {}
        # Last answer tracking for follow-ups
        self.last_answers: Dict[str, str] = {}

    def _init_agent(self, agent_name: str):
        """Initialize agent context storage."""
        if agent_name not in self.agent_contexts:
            self.agent_contexts[agent_name] = {}
        if agent_name not in self.global_contexts:
            self.global_contexts[agent_name] = {}

    def extract_key_phrases(self, text: str) -> List[str]:
        """
        Extract key phrases including document codes, names, and important terms.
        This catches things spaCy might miss like "CFOO LPC 001".
        """
        key_phrases = []
        
        # Pattern for document codes (e.g., CFOO LPC 001, HR-2024-001)
        doc_code_pattern = r'\b[A-Z]{2,}\s*[A-Z]{2,}\s*\d+\b|\b[A-Z]+-\d{4}-\d+\b'
        doc_codes = re.findall(doc_code_pattern, text)
        key_phrases.extend(doc_codes)
        
        # Pattern for capitalized phrases (likely proper nouns)
        cap_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        cap_phrases = re.findall(cap_pattern, text)
        # Filter out common words
        common_words = {'The', 'This', 'That', 'These', 'Those', 'A', 'An'}
        key_phrases.extend([p for p in cap_phrases if p not in common_words])
        
        return key_phrases

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract named entities from text using spaCy + custom patterns."""
        entities = {}
        
        # First, get custom key phrases
        key_phrases = self.extract_key_phrases(text)
        if key_phrases:
            entities["CUSTOM"] = key_phrases
        
        # Then use spaCy if available
        if not nlp:
            return entities
        
        doc = nlp(text)
        for ent in doc.ents:
            label = ent.label_
            if label not in entities:
                entities[label] = []
            entities[label].append(ent.text)
        
        return entities

    def update_entity_memory(self, chat_id: str, text: str, role: str = "user"):
        """
        Extract and store entities from conversation turns.
        Maintains recency by timestamping entities.
        """
        if chat_id not in self.entity_memory:
            self.entity_memory[chat_id] = {
                "recent_entities": {},
                "all_topics": [],
                "last_domain": None,
                "conversation_flow": []
            }
        
       
        self.entity_memory[chat_id]["conversation_flow"].append({
            "role": role,
            "text": text[:200],  
            "timestamp": datetime.now()
        })
        
        if len(self.entity_memory[chat_id]["conversation_flow"]) > 10:
            self.entity_memory[chat_id]["conversation_flow"] = \
                self.entity_memory[chat_id]["conversation_flow"][-10:]
        
        entities = self.extract_entities(text)
        
        # Update with timestamp for recency tracking
        for entity_type, entity_list in entities.items():
            if entity_type not in self.entity_memory[chat_id]["recent_entities"]:
                self.entity_memory[chat_id]["recent_entities"][entity_type] = []
            
            for entity in entity_list:
                if entity.lower() not in PRONOUNS:
                    self.entity_memory[chat_id]["recent_entities"][entity_type].append({
                        "value": entity,
                        "timestamp": datetime.now(),
                        "role": role
                    })
        
        # Store last answer for follow-ups
        if role == "assistant":
            self.last_answers[chat_id] = text
        
        logger.info(f"ENTITY_MEMORY[{chat_id}]: Extracted {sum(len(v) for v in entities.values())} entities")

    def get_recent_entities(self, chat_id: str, limit: int = 5) -> List[str]:
        """
        Get the most recent entities across all types.
        Returns a list of entity values sorted by recency.
        """
        if chat_id not in self.entity_memory:
            return []
        
        recent_entities = self.entity_memory[chat_id]["recent_entities"]
        
        # Flatten all entities with timestamps
        all_entities = []
        for entity_type, entities in recent_entities.items():
            all_entities.extend(entities)
        
        if not all_entities:
            return []
        
        # Sort by timestamp (most recent first)
        all_entities.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # Return unique values
        seen = set()
        result = []
        for entity in all_entities:
            value = entity["value"]
            if value not in seen:
                seen.add(value)
                result.append(value)
                if len(result) >= limit:
                    break
        
        return result

    def is_followup_question(self, query: str) -> bool:
        """
        Detect if a query is a follow-up question referring to previous context.
        """
        lower_query = query.lower()
        
        # Check for vague patterns
        for pattern in VAGUE_PATTERNS:
            if re.search(pattern, lower_query):
                return True
        
        # Check for short questions without clear subject
        if len(query.split()) < 5 and any(word in lower_query for word in ['it', 'that', 'this']):
            return True
        
        return False

    def enrich_query_with_context(self, chat_id: str, query: str) -> str:
        """
        Automatically enrich queries that reference previous context.
        Enhanced to handle follow-up questions better.
        """
        if not self.is_followup_question(query):
            logger.info(f"[ENRICH] Not a follow-up question: {query}")
            return query
        
        # Get recent entities
        recent_entities = self.get_recent_entities(chat_id, limit=3)
        
        if not recent_entities:
            logger.info(f"[ENRICH] No recent entities found for chat {chat_id}")
            return query
        
        # Build enriched query with context
        context_str = ", ".join(recent_entities[:3])
        enriched = f"{query} [Context: referring to {context_str}]"
        
        logger.info(f"[ENRICH] '{query}' -> '{enriched}'")
        return enriched

    def get_last_answer_snippet(self, chat_id: str, max_length: int = 200) -> Optional[str]:
        """Get a snippet of the last assistant answer."""
        if chat_id not in self.last_answers:
            return None
        
        answer = self.last_answers[chat_id]
        if len(answer) <= max_length:
            return answer
        
        return answer[:max_length] + "..."

    def update_context(self, agent_name: str, key: str, value: Any, chat_id: Optional[str] = None):
        """Store contextual data for an agent."""
        if not value or str(value).lower() in PRONOUNS:
            logger.debug(f"CONTEXT: Ignoring pronoun/empty value '{value}'")
            return

        self._init_agent(agent_name)

        if chat_id:
            if chat_id not in self.agent_contexts[agent_name]:
                self.agent_contexts[agent_name][chat_id] = {}
            self.agent_contexts[agent_name][chat_id][key] = value
            logger.info(f"CONTEXT[{agent_name}][{chat_id}]: Stored '{key}'='{value}'")
        else:
            self.global_contexts[agent_name][key] = value
            logger.info(f"CONTEXT[{agent_name}]: Stored global '{key}'='{value}'")

    def get_context(self, agent_name: str, key: str, chat_id: Optional[str] = None) -> Optional[Any]:
        """Retrieve contextual data for an agent."""
        self._init_agent(agent_name)

        # Check chat-specific first
        if chat_id and chat_id in self.agent_contexts[agent_name]:
            if key in self.agent_contexts[agent_name][chat_id]:
                value = self.agent_contexts[agent_name][chat_id][key]
                logger.info(f"CONTEXT[{agent_name}][{chat_id}]: Retrieved '{key}'='{value}'")
                return value

        # Fall back to global
        if key in self.global_contexts[agent_name]:
            value = self.global_contexts[agent_name][key]
            logger.info(f"CONTEXT[{agent_name}]: Retrieved global '{key}'='{value}'")
            return value

        return None

    def get_conversation_summary(self, chat_id: str) -> Dict[str, Any]:
        """
        Generate a summary of conversation context.
        """
        summary = {
            "entities": {},
            "recent_topics": [],
            "last_domain": None,
            "last_answer_snippet": None
        }
        
        if chat_id in self.entity_memory:
            memory = self.entity_memory[chat_id]
            
            # Get recent entities
            for entity_type, entities in memory["recent_entities"].items():
                if entities:
                    recent = [e["value"] for e in entities[-5:]]
                    summary["entities"][entity_type] = recent
            
            summary["recent_topics"] = memory.get("all_topics", [])[-5:]
            summary["last_domain"] = memory.get("last_domain")
        
        # Add last answer snippet
        summary["last_answer_snippet"] = self.get_last_answer_snippet(chat_id)
        
        return summary

    def clear_context(self, agent_name: str, key: Optional[str] = None, chat_id: Optional[str] = None):
        """Clear context data."""
        self._init_agent(agent_name)

        if chat_id and chat_id in self.agent_contexts[agent_name]:
            if key:
                self.agent_contexts[agent_name][chat_id].pop(key, None)
            else:
                del self.agent_contexts[agent_name][chat_id]

        elif not chat_id:
            if key:
                self.global_contexts[agent_name].pop(key, None)
            else:
                self.global_contexts[agent_name] = {}


# Global singleton instance
context_manager = EnhancedContextManager()