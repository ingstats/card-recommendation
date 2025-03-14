import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer

CARD_EMBED_PATH = "./index/card_embeddings.pkl"
FAISS_INDEX_PATH = "./index/faiss_index.bin"
model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

with open(CARD_EMBED_PATH, "rb") as f:
    card_embeddings, card_info_list = pickle.load(f)

index = faiss.read_index(FAISS_INDEX_PATH)

def get_card_rag_explanations(user_text, top_k=3):
    query_vec = model.encode([user_text]).astype("float32")
    _, I = index.search(query_vec, top_k)
    return [card_info_list[i] for i in I[0]]