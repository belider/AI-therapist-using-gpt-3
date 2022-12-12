import requests
import os
from googletrans import Translator
translator = Translator()

# getting temporary yandex IAM token
OAuth_token = os.getenv('YANDEX_OAUTH_TOKEN')
url = "https://iam.api.cloud.yandex.net/iam/v1/tokens"
data = {"yandexPassportOauthToken": f"{OAuth_token}"}
response = requests.post(url, json=data).json()
iam_token = response['iamToken']
folder_id = os.getenv('YANDEX_FOLDER_ID')

def yandex_translate(text, target_lang='ru'):
    texts = [text]
    body = {
        "targetLanguageCode": target_lang, 
        "texts": texts,
        "folderId": folder_id,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {iam_token}"
    }
    response = requests.post('https://translate.api.cloud.yandex.net/translate/v2/translate',
        json = body,
        headers = headers
    ).json()
    return response['translations'][0]['text']

def translate_using_available_translator(text, target_lang='ru'):
    try:
        translated_text = yandex_translate(text, target_lang=target_lang)
    except Exception as err: 
        print("Yandex Translate didn't work. Error: ", err)
        translated_text = translator.translate(text, dest=target_lang).text
    return translated_text