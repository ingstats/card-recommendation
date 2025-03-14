import openai
import requests

openai.api_key = "YOUR_OPENAI_API_KEY"

def call_internal_api(user_profile):
    response = requests.post("http://localhost:8000/recommend_card", json={
        "user_profile": user_profile,
        "context": "편의점/커피 중심 소비"
    })
    return response.json()

functions = [
    {
        "name": "get_card_recommendation",
        "description": "카드 추천 요청",
        "parameters": {
            "type": "object",
            "properties": {
                "user_profile": {
                    "type": "object",
                    "properties": {
                        "age": {"type": "number"},
                        "income_level": {"type": "string"},
                        "recent_spending": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["age", "income_level", "recent_spending"]
                }
            }
        }
    }
]

messages = [
    {"role": "system", "content": "너는 카드 추천 도우미야."},
    {"role": "user", "content": "편의점, 커피 중심으로 많이 쓰는데 좋은 카드 뭐 있어?"}
]

response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=messages,
    functions=functions,
    function_call="auto"
)

if "function_call" in response["choices"][0]["message"]:
    args = eval(response["choices"][0]["message"]["function_call"]["arguments"])
    result = call_internal_api(args["user_profile"])
    final_msg = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages + [
            {"role": "assistant", "function_call": response["choices"][0]["message"]["function_call"]},
            {"role": "function", "name": "get_card_recommendation", "content": str(result["summary"])}
        ]
    )
    print("📌 최종 요약 응답:")
    print(final_msg["choices"][0]["message"]["content"])
