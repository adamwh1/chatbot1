from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import faiss
import numpy as np
import json
from openai import OpenAI
import os

# Access the OpenAI API key
api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)
app = FastAPI()


# Define a Pydantic model for the request
class QueryRequest(BaseModel):
    query: str
    online: bool = True
    saas_id: str

# Load FAISS index and documents
try:
    faiss_index = faiss.read_index('embedded_data/embedded_data.index')
except FileNotFoundError:
    raise RuntimeError("Erreur : fichier d'index FAISS introuvable.")

try:
    with open('chunks/chunks.json', 'r', encoding='utf-8') as f:
        documents = json.load(f)
except FileNotFoundError:
    raise RuntimeError("Erreur : fichier chunks.json introuvable.")


def get_embedding(text, model="text-embedding-3-small"):
    text = text.replace("\n", " ")
    return client.embeddings.create(input=[text], model=model).data[0].embedding


def generate_response(query):
    query_embedding = get_embedding(query)
    if query_embedding is None:
        raise HTTPException(status_code=500, detail="Erreur lors de la génération de l'embedding pour la requête.")

    query_vector = np.array(query_embedding).astype('float32').reshape(1, -1)
    distances, indices = faiss_index.search(query_vector, k=3)

    # Get the nearest documents
    retrieved_docs = [documents[idx] for idx in indices[0]]
    context = "\n\n".join(retrieved_docs)

    messages = [
            {"role": "system",
             "content": "Vous êtes un assistant utile, votre nom est LIADBOT. Vous parlez uniquement en français et vous utilisez le pronom 'nous' uniquement lorsque vous faites référence à LIADTECH. Vous ne répondez pas aux questions qui sont générales et sans rapport avec LIADTECH, mais vous pouvez saluer les utilisateurs. Votre réponse doit être concise (100 tokens maximum), explicative et contenir toutes les informations souhaitées. Si une information n'est pas disponible dans le contexte, référez-vous à notre numéro +33 633 324 384 ou à notre email contact@liadtech.com."},
            {"role": "user",
             "content": f"En vous basant sur le contexte suivant :\n\nContexte :\n{context}\n\nQuestion : {query}"}
        ]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )
    return response.choices[0].message.content.strip()


@app.post("/query")
async def query_liaddbot(request: QueryRequest):
    try:
        return {"response": generate_response(request.query)}
    except HTTPException as e:
        return {"error": str(e.detail)}
    except Exception as e:
        return {"error": f"Erreur lors de la génération de la réponse : {str(e)}"}