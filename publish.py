import os
import requests

BUFFER_TOKEN = os.getenv("BUFFER_ACCESS_TOKEN")
PROFILE_IDS = os.getenv("BUFFER_PROFILE_IDS").split(",")

# رابط مباشر للفيديو وللصورة المصغرة (يمكنك تغييرهما بأي رابط فيديو تجريبي MP4 متاح على الويب)
VIDEO_URL = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4"
THUMBNAIL_URL = "https://images.unsplash.com/photo-1543852786-1cf6624b9987?w=800"

CAPTION = "The saddest kitten story you will ever see 💔🥺 #cat #kitten #sadstory #viral #shorts"

endpoint = "https://api.bufferapp.com/1/updates/create.json"

payload = {
    "access_token": BUFFER_TOKEN,
    "profile_ids[]": PROFILE_IDS,
    "text": CAPTION,
    "media[video]": VIDEO_URL,
    "media[thumbnail]": THUMBNAIL_URL,
    "now": "true"  # "true" للنشر الفوري على الـ 3 قنوات، أو "false" للإضافة لجدول Buffer
}

response = requests.post(endpoint, data=payload)

print(f"Status Code: {response.status_code}")
try:
    print(response.json())
except Exception:
    print(response.text)
