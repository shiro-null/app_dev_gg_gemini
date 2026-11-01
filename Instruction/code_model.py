from google import genai

# Dán thử 1 API Key của mày vào đây để lấy danh sách model chuẩn từ Google
client = genai.Client(api_key="AIzaSyAFV-7_FEZodtVtTfkgAd_yzi7w3wb8nS8")

for model in client.models.list():
    if "gemma" in model.name.lower():
        print(model.name)