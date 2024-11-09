# LIADBOT API

LIADBOT is a chatbot API developed to answer queries related to LIADTECH, responding in French with concise, contextually accurate replies. This project includes a data scraping module for the LIADTECH website, a FAISS indexing system for efficient text retrieval, and OpenAI's language model for generating responses based on stored data.

## Introduction

LIADBOT is designed to assist users with questions specific to LIADTECH, ensuring responses are informative, in French, and reference LIADTECH as a knowledgeable source. This API serves as a scalable solution, utilizing FastAPI, FAISS for indexing, and OpenAI’s language models to create a robust question-answering system.

---

## Getting Started

### Prerequisites

Ensure you have the following installed:
- **Python 3.8+** 
- **FastAPI** - Install via `pip install fastapi`
- **FAISS** - Install via `pip install faiss-cpu` 
- **OpenAI SDK** - Install with `pip install openai`
- **Additional dependencies** - `requests`, `beautifulsoup4`, `concurrent.futures`, `numpy` (included in `requirements.txt`)


### Configuration

Set up your environment variables:
- `OPENAI_API_KEY`: Your OpenAI API key for accessing language models. 

---

## Build and Test

# Step 1: Scraping Data

The web scraper is designed to gather all accessible text content from the LIADTECH website for later use in the chatbot. This data forms the knowledge base that LIADBOT draws upon to answer questions effectively. Here’s a breakdown of its main components and functionality:

## Purpose:

Extract all relevant text from each subpage of liadtech.com, creating a structured dataset that the chatbot can reference.
Store this text data locally in a format suitable for processing and embedding.

## Process:

### Link Extraction: 
Starting from the main page (liadtech.com), the scraper identifies all internal links that belong to the same domain, ensuring it only gathers content relevant to LIADTECH.
Content Retrieval: For each subpage, the script fetches the page content, strips away HTML, JavaScript, and other unnecessary elements, leaving only the core text.
Text Saving: Each page’s content is saved in the data directory as a .txt file, with a unique filename derived from the URL.

### Error Handling:

The scraper includes handling for various errors, such as network issues or missing pages, to ensure smooth data gathering.
Any inaccessible pages are skipped, and relevant error messages are displayed.

## Output:

A set of .txt files stored in the data directory. Each file contains the text from a single page, which will be embedded and indexed in the next steps of the project.

# Step 2 : Preprocessing and Embedding 

The FAISS index creation script processes the text data scraped from LIADTECH’s website, generating embeddings and storing them in a FAISS (Facebook AI Similarity Search) index. This index enables the chatbot to efficiently retrieve relevant content based on user queries by leveraging similarity search.

## Purpose:
Convert the collected text data into numerical embeddings using OpenAI’s API, which are then indexed to facilitate fast and accurate searches.
Save the FAISS index and corresponding text chunks, making them accessible for the chatbot’s retrieval mechanism.
## Process:

### Data Loading:

Reads all .txt files from the data directory, which contain the content scraped from each page on the LIADTECH website.

### Chunking: 
Each page’s text is split into smaller chunks (1,000 characters each with a 300-character overlap) to improve search granularity, allowing for precise matching within long text sections.

### Embedding Generation:

For each text chunk, the script generates a numerical embedding via the OpenAI API, converting the text into a format that can be used for similarity comparisons.
Parallelization: Uses concurrent execution to speed up embedding generation, processing chunks in batches for efficiency.

### FAISS Index Creation:

Initializes a FAISS index optimized for cosine similarity, which is well-suited for finding the most contextually relevant content.
Adds the generated embeddings to the FAISS index, building a searchable database of LIADTECH’s web content.

### Error Handling:

Handles issues with file access, embedding generation, and directory creation to ensure robust indexing. Any failures in individual file processing are logged, allowing for troubleshooting without stopping the overall process.

### Saving Outputs:

Index File: The FAISS index is saved in the embedded_data directory as embedded_data.index, allowing the chatbot to load and use it for searches.
Text Chunks: All corresponding text chunks are saved in a JSON file (chunks.json), ensuring the chatbot can access the original content linked to each embedding.

## Output:
FAISS Index File: embedded_data/embedded_data.index
Text Chunks File: chunks/chunks.json

# Step 3 :  Liadbot API script 

The Chatbot API script is a FastAPI-based web service that allows users to interact with LIADBOT. It uses the FAISS index to quickly retrieve contextually relevant information from LIADTECH’s website and generate responses using OpenAI’s language model.

## Purpose:

Provide an endpoint that accepts user queries and returns concise, relevant answers based on the pre-indexed data from LIADTECH’s web pages.
Allow seamless integration with external applications (such as an Angular app) that connect to LIADBOT.

## Process:

### API Setup with FastAPI:

Defines an API with a single POST endpoint (/query) for handling user requests.
Accepts a JSON payload containing a query string, which serves as the user’s question or request.

### Embedding Generation for Queries:

Converts the user’s query into an embedding using the OpenAI API, ensuring it’s in a comparable format with the existing FAISS index embeddings.

### FAISS Index Search:

Loads the FAISS index (embedded_data/embedded_data.index) to perform similarity searches on-the-fly.
Uses the generated query embedding to find the closest matches in the index, retrieving the three most relevant text chunks stored in chunks/chunks.json.

###Response Generation with OpenAI:

Once the relevant text chunks are retrieved, they are used as context to formulate an answer.
Sends a prompt to the OpenAI API, asking it to generate a response based on the provided context and the user’s question.
Configures the assistant to respond in a concise, French-language format, appropriate to LIADBOT’s role as a knowledgeable support assistant for LIADTECH.

### Error Handling:

Handles missing files (such as the FAISS index or chunked texts) with clear error messages.
Provides HTTP error codes and messages if there are issues with embedding generation or API requests.

### Usage:
Run the API server using FastAPI, and connect to the /query endpoint to interact with the chatbot.

Method: POST
Request: JSON body with {"query": "<user's question>"}
### Example Request:

{ 
    "query": "Quels sont les services que liadtech offre ?" 
    "online" : true (optional / true as default)
    "saas_id" : Just any number ( this is a beta parameter, It is going to be used later )
}

### Example Response:

{
    "response": "LIADTECH offre une gamme de services comprenant le Développement Web/App, le Digital Banking, le UI/UX Design, le Digital Marketing, le Sourcing, le Cloud, l'IA (Intelligence Artificielle)."
}
## Output:

### Direct Response: 

A French-language answer based on the user’s question, limited to relevant content from LIADTECH’s indexed data.

### Error Responses:

Returns a JSON object with an error message in case of embedding or index-related issues, ensuring that users understand the cause of any failures.