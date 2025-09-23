# Virtual City AI Chat Assistant API Documentation

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](#) 
[![OpenAPI](https://img.shields.io/badge/OAS-3.1-green.svg)](#)

Endpoints for system monitoring, multilingual chatbot, and document management.

---

## Table of Contents
- [Overview](#overview)
- [Endpoints](#endpoints)
  - [System](#system)
  - [Chat](#chat)
  - [Documents](#documents)
- [Schemas](#schemas)
  - [ChatRequest](#chatrequest)
  - [ChatResponse](#chatresponse)
  - [LinkRequest](#linkrequest)
  - [ValidationError](#validationerror)
  - [HTTPValidationError](#httpvalidationerror)
  - [WelcomeResponse](#welcomeresponse)
- [Tags](#tags)
- [Interactive Docs](#interactive-docs)

---

## Overview

- **OpenAPI Version:** 3.1.0  
- **API Version:** 1.0.0  
- **Title:** Virtual City AI Chat Assistant  
- **Description:** API Documentation  

---

## Endpoints

### System

Endpoints for system-level operations and monitoring.

- **GET `/api`**  
  Welcome endpoint – Returns a welcome message for testing the API connection.  

  - **Response (200 - Successful Response):**
  ```json
  {
    "msg": "string"
  }
  ```

- **GET `/metrics`**  
  Prometheus metrics – Serves system metrics for monitoring.

  - **Response (200 - Successful Response):**
  ```json
  {
    "msg": "string"
  }
  ```

- **GET `/api/stats`**  
  Grafana redirect – Redirects the user to the Grafana monitoring dashboard.

  - **Response (200 - Successful Response):**
  ```json
  {
    "msg": "string"
  }
  ```

---

### Chat
- **POST `/api/v1/chat`**  
  Chat Endpoint – Send a query to the multilingual chatbot.  
 
  - **Request Body** :  
    ```json
    {
      "query": "string (1–500 chars)",
      "chat_id": "string"
    }
    ```
  - **Response (200 - Successful Response) :**
    ```json
    {
      "answer": "string",
      "sources": [],
      "chat_id": "string",
      "reasoning_chain": [],
      "map_links": []
    }
    ```
  - **Response (422 - Validation Error) :**
    ```json
    {
      "detail": [{
        "loc": ["string",0],
        "msg": "string",
        "type": "string"
      }]
    }
    ```

- **GET `/api/v1/chat/chat/{chat_id}/history`**  
  Get Chat History – Retrieve the chat history by `chat_id`.
   
  - **Request Body** :  
    
    `chat_id` (string (chat_id))
    
  - **Response (200 - Successful Response) :**
    ```json
    {
      "string"
    }
    ```
  - **Response (422 - Validation Error) :**
    ```json
    {
      "detail": [{
        "loc": ["string",0],
        "msg": "string",
        "type": "string"
      }]
    }
    ```
 
- **GET `/api/v1/health`**  
  Health check endpoint.

  - **Response (200 - Successful Response) :**
    ```json
    {
      "string"
    }
    ```
---

### Documents
- **POST `/api/v1/add_data`**  
  *Add Data to Collection* – Add a new URL for processing into the collection.  
 
  - **Request Body** :  
    ```json
    {
      "url": "https://example.com/",
      "chunk_size": 1000,
      "chunk_overlap": 200
    }
    ```
  - **Response (200 - Successful Response) :**
    ```json
    {
      "status": "success",
      "message": "completed"
    }
    ```
  - **Response (422 - Validation Error) :**
    ```json
    {
      "detail": [{
        "loc": ["string",0],
        "msg": "string",
        "type": "string"
      }]
    }
    ```

- **GET `/api/v1/collections`**  
  *List Collections* – Retrieve all available collections.  

- **GET `/api/v1/chunks`**  
  *List Chunks* – Retrieve all available chunks in a collection.  

- **DELETE `/api/v1/delete`**  
  *Drop Collection* – Delete all chunks in the collection.  

---

## Schemas

### ChatRequest
```json
{
  "query": "string (1–500 chars)",
  "chat_id": "string "
}
```
### ChatResponse
```json
{
  "answer": "string",
  "sources": ["string"],
  "chat_id": "string",
  "reasoning_chain": ["string"],
  "map_links": ["string"]
}
```

### LinkRequest
```json
{
  "url": "string (URI, required)",
  "chunk_size": 1000,
  "chunk_overlap": 200
}
```

### ValidationError
```json
{
  "loc": ["string | int"],
  "msg": "string",
  "type": "string"
}
```

### HTTPValidationError
```json
{
  "detail": [
    {
      "loc": ["string|int"],
      "msg": "string",
      "type": "string"
    }
  ]
}
```

### WelcomeResponse
```json
{
  "msg": "string"
}
```
---

## Tags

- **System** - Endpoints for system-level operations and monitoring.

- **Chat** - Endpoints for the multilingual chatbot powered by multi-agent architecture.

- **Documents** - Endpoints for managing knowledge base and documents, used by the FAQ agent.

---

## Interactive Docs

- **Swagger UI**: [https://aisleprojects.sltdigitallab.lk/api/docs](https://aisleprojects.sltdigitallab.lk/api/docs)
