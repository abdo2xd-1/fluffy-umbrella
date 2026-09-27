import os
import random
import requests
from urllib.parse import quote
from moviepy.editor import ImageClip, concatenate_videoclips

BUFFER_TOKEN = os.getenv("BUFFER_ACCESS_TOKEN")
PROFILE_IDS = os.getenv("BUFFER_PROFILE_IDS").split(",")

# قائمة أفكار درامية لتوليد قصص قطط متنوعة كل يوم
STORIES = [
    {
        "title": "A homeless crying kitten finds a warm bakery and a kind friend 💔🥺",
        "scenes": [
            "hyper-realistic close-up crying tiny ginger kitten in heavy rain on dark street, cinematic 8k",
            "poor shivering wet kitten looking through a warm bakery glass window, emotional lighting",
            "kind old baker opening the door and smiling, holding a towel, warm golden lights",
            "happy dry cute kitten sleeping in a warm bread basket, peaceful happy ending"
        ]
    },
    {
        "title": "Tiny warrior kitten fights against storm to protect its sibling 🐾⚡",
        "scenes": [
            "tiny injured cute kitten standing in muddy alley shivering, dramatic dark atmosphere",
            "huge scary storm clouds over broken cardboard box, dramatic cinematic angle",
            "the kitten standing brave glowing eyes protecting a smaller kitten, epic heroic mood",
            "morning sun rays shining, both kittens safe and cuddled together, wholesome happy"
        ]
    },
    {
        "title": "Abandoned kitten learns to trust humans again 🐾❤️",
        "scenes": [
            "tiny sad kitten hiding under a cardboard box in dark dirty street, big tearful eyes",
            "gentle human hands reaching out offering food to the scared kitten, cinematic 8k",
            "kitten slowly taking food, cautious but hopeful expression, warm lighting",
            "kitten being hugged happily by a smiling girl inside a cozy living room"
        ]
    }
]

def generate_video():
    story = random.choice(STORIES)
    print(f"Selected Story: {story['title']}")

    image_paths = []
    # 1. توليد صور القصة عبر Pollinations AI مجاناً بجودة 9:16 (1080x1920)
    for i, scene in enumerate(story["scenes"]):
        prompt = quote(f"{scene}, cinematic photo, 8k resolution, highly detailed, photorealistic")
        seed = random.randint(1000, 999999)
        url = f"https://image.pollinations.ai/prompt/{prompt}?width=720&height=1280&model=flux&seed={seed}&nologo=true"
        
        img_name = f"scene_{i}.jpg"
        print(f"Generating image {i+1}...")
        res = requests.get(url, timeout=60)
        if res.status_code == 200:
            with open(img_name, "wb") as f:
                f.write(res.content)
            image_paths.append(img_name)

    if not image_paths:
        raise Exception("Failed to generate scene images.")

    # 2. تحويل الصور إلى فيديو Shorts متتابع (كل لقطة مدتها 4 ثوانٍ)
    clips = [ImageClip(img).set_duration(4) for img in image_paths]
    final_clip = concatenate_videoclips(clips, method="compose")
    output_video = "shorts_video.mp4"
    final_clip.write_videofile(output_video, fps=24, codec="libx264")
    
    return story["title"], output_video, image_paths[0]

def upload_to_tmp(file_path):
    """رفع الفيديو مؤقتاً للحصول على Direct URL يتطلبه Buffer"""
    with open(file_path, "rb") as f:
        res = requests.post("https://tmpfiles.org/api/v1/upload", files={"file": f})
    data = res.json()
    url = data["data"]["url"]
    # تحويل رابط الصفحة إلى رابط مباشر لتحميل الـ MP4
    direct_url = url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
    return direct_url

def post_to_buffer(caption, video_url, thumb_url):
    endpoint = "https://api.bufferapp.com/1/updates/create.json"
    payload = {
        "access_token": BUFFER_TOKEN,
        "profile_ids[]": PROFILE_IDS,
        "text": f"{caption} #cat #kitten #sadstory #viral #shorts #animation",
        "media[video]": video_url,
        "media[thumbnail]": thumb_url,
        "now": "true"
    }
    res = requests.post(endpoint, data=payload)
    print(f"Buffer Response: {res.status_code}")
    print(res.text)

if __name__ == "__main__":
    title, video_file, thumb_file = generate_video()
    print("Uploading video to get public URL for Buffer...")
    direct_video_url = upload_to_tmp(video_file)
    direct_thumb_url = upload_to_tmp(thumb_file)
    print(f"Direct Video URL: {direct_video_url}")
    
    print("Posting to 3 channels via Buffer...")
    post_to_buffer(title, direct_video_url, direct_thumb_url)
