import pandas as pd
import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer

CARD_DATA_PATH = "./backend/data/card_data.csv"
EMBEDDING_PATH = "./index/card_embeddings.pkl"
FAISS_INDEX_PATH = "./index/faiss_index.bin"

model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
card_df = pd.read_csv(CARD_DATA_PATH)
descriptions = card_df["Benefits"].fillna("").tolist()
card_info = card_df[["Card Name", "Corporate Name", "Benefits", "Image URLs"]].to_dict("records")

embeddings = model.encode(descriptions).astype("float32")
index = faiss.IndexFlatL2(embeddings.shape[1])
index.add(embeddings)

with open(EMBEDDING_PATH, "wb") as f:
    pickle.dump((embeddings, card_info), f)

faiss.write_index(index, FAISS_INDEX_PATH)
print("✅ FAISS 인덱스 저장 완료")
