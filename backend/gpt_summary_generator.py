from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM

# 한국어 요약 모델 (필요 시 다른 모델로 교체 가능)
MODEL_NAME = "knkarthick/MEETING_SUMMARY"

# 모델 및 토크나이저 로딩
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
summarizer = pipeline("summarization", model=model, tokenizer=tokenizer)

def generate_summary_with_model(card_name: str, benefits_text: str) -> str:
    try:
        full_text = f"카드 이름: {card_name}\n혜택 설명: {benefits_text}"
        summary = summarizer(full_text, max_length=100, min_length=30, do_sample=False)
        return summary[0]["summary_text"]
    except Exception as e:
        return f"{card_name}의 요약 정보를 불러오지 못했습니다. ({e})"
