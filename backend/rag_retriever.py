# backend/rag_retriever.py

import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
import pandas as pd

# 모델 및 FAISS 인덱스 로딩
model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

with open("index/card_embeddings.pkl", "rb") as f:
    card_embeddings = pickle.load(f)

faiss_index = faiss.read_index("index/faiss_index.bin")

# 카드 설명 유사 검색 함수
def retrieve_similar_card_descriptions(card_name: str, card_df: pd.DataFrame, top_k: int = 3) -> str:
    try:
        query_text = card_df[card_df["Card Name"] == card_name]["Benefits"].values[0]
    except IndexError:
        return "카드 설명을 찾을 수 없습니다."

    query_vec = model.encode([query_text])
    _, indices = faiss_index.search(np.array(query_vec).astype("float32"), top_k)

    similar_descriptions = []
    for idx in indices[0]:
        if idx < len(card_df):
            row = card_df.iloc[idx]
            similar_descriptions.append(f"{row['Card Name']} - {row['Benefits']}")

    return "\n".join(similar_descriptions)
