import os
import numpy as np
import faiss
from openai import OpenAI
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

api_key = os.getenv('OPENAI_API_KEY')


# Initialize OpenAI client
client = OpenAI(api_key=api_key)


# Function to get embeddings (supports batch requests if possible)
def get_embedding(texts, model="text-embedding-3-small"):
    try:
        # Handle multiple texts at once (if OpenAI API allows)
        texts = [text.replace("\n", " ") for text in texts]
        return [res.embedding for res in client.embeddings.create(input=texts, model=model).data]
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return [None] * len(texts)


# Function to split text into chunks of specified size with overlap
def split_into_chunks(text, chunk_size=1000, overlap=300):
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

# Load all .txt files and split text into chunks of 1000 characters with 300 overlap
def load_data_files(directory):
    documents = []
    try:
        for filename in os.listdir(directory):
            if filename.endswith('.txt'):
                file_path = os.path.join(directory, filename)
                try:
                    # Use 'utf-8-sig' encoding to remove BOM if present
                    with open(file_path, 'r', encoding='utf-8-sig') as file:
                        content = file.read()
                        # Split content into chunks of 1000 characters with 300 overlap
                        chunks = split_into_chunks(content, chunk_size=1000, overlap=300)
                        for chunk in chunks:
                            documents.append({'page_content': chunk, 'metadata': {'source': filename}})
                except OSError as e:
                    print(f"Error reading file {file_path}: {e}")
        return documents
    except Exception as e:
        print(f"Error loading files from directory {directory}: {e}")
        return []



# Parallelize embedding generation using ThreadPoolExecutor
def generate_embeddings_parallel(documents, max_workers=5):
    texts = [doc['page_content'] for doc in documents]
    embeddings = []

    # Process in batches for efficiency
    batch_size = 10
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(get_embedding, texts[i:i + batch_size]) for i in range(0, len(texts), batch_size)]

        for future in as_completed(futures):
            result = future.result()
            embeddings.extend(result)

    # Filter out None results if any embedding failed
    embeddings = [emb for emb in embeddings if emb is not None]
    return np.array(embeddings).astype('float32')


# Create FAISS index
def create_faiss_index(documents):
    try:
        # Generate embeddings in parallel
        embeddings = generate_embeddings_parallel(documents)

        # Initialize FAISS index
        index = faiss.IndexFlatIP(embeddings.shape[1])  # Use cosine similarity
        index.add(embeddings)  # Add embeddings to the index

        # Check if the directories exist, if not, create them
        faiss_output_dir = "embedded_data"
        json_output_dir = "chunks"
        if not os.path.exists(faiss_output_dir):
            os.makedirs(faiss_output_dir)
        if not os.path.exists(json_output_dir):
            os.makedirs(json_output_dir)

        # Define the saving paths
        faiss_saving_path = os.path.join(faiss_output_dir, "embedded_data.index")
        json_saving_path = os.path.join(json_output_dir, "chunks.json")

        # Save FAISS index to disk
        faiss.write_index(index, faiss_saving_path)
        print(f"FAISS index saved successfully in {faiss_saving_path}!")

        # Save corresponding texts to a JSON file
        texts = [doc['page_content'] for doc in documents]
        with open(json_saving_path, 'w', encoding='utf-8') as f:
            json.dump(texts, f)
        print(f"Corresponding chunks saved successfully in {json_saving_path}!")

    except Exception as e:
        print(f"Error creating FAISS index or saving data: {e}")


# Run ..........
if __name__ == "__main__":
    data_folder = "data"  # Folder where .md files are located
    try:
        documents = load_data_files(data_folder)
        if documents:
            create_faiss_index(documents)
        else:
            print("No documents to process.")
    except Exception as e:
        print(f"Unexpected error: {e}")
