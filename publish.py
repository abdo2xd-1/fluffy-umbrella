import os
import time
import random
import urllib.parse
import requests
import numpy as np
import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont

if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.Resampling.LANCZOS

try:
    from moviepy.editor import ImageClip, concatenate_videoclips
except (ImportError, ModuleNotFoundError):
    from moviepy import ImageClip, concatenate_videoclips

BUFFER_TOKEN = os.getenv("BUFFER_ACCESS_TOKEN", "").strip()
PROFILE_IDS = [pid.strip() for pid in os.getenv("BUFFER_PROFILE_IDS", "").split(",") if pid.strip()]
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()
GITHUB_REPO = os.getenv("GITHUB_REPOSITORY", "").strip()

STORIES = [
    {
        "title": "I rescued a little bear cub that was attacked in the woods 🐻❤️ #shorts",
        "caption": "I found him crying and helpless... Now he feels safe with me ❤️ #animalrescue #wildlife #bear #wholesome #shorts #viral",
        "scenes": [
            {
                "prompt": "POV authentic iPhone photo, a human hand gently touching the head of a tiny real baby brown bear cub sitting in the forest dirt, wet realistic fur, big black shiny wet eyes, raw candid smartphone snapshot, unedited real life",
                "text": "I saw this tiny cub crying all alone in the woods..."
            },
            {
                "prompt": "POV authentic smartphone footage, human hand holding a cute real small bear cub wrapped inside a dirty warm winter jacket inside a car seat, real documentary photo, natural lighting",
                "text": "He was shivering, so I rushed him to my car."
            },
            {
                "prompt": "first person view photo, human hand feeding milk from a baby bottle to a real tiny brown bear cub, messy drinking, realistic room lighting, candid real photo",
                "text": "He was so hungry and started drinking immediately."
            },
            {
                "prompt": "POV handheld phone camera photo, a happy healthy baby bear cub resting on a soft blanket, looking right at the camera, safe and peaceful, real candid home photo",
                "text": "Now he is safe and never leaves my side ❤️"
            }
        ]
    },
    {
        "title": "A helpless golden puppy left behind in the heavy rain 🐶💔 #shorts",
        "caption": "He was soaked and crying... Look at his happy ending! 🥺❤️ #dog #puppy #rescue #emotional #shorts #viral",
        "scenes": [
            {
                "prompt": "POV authentic candid mobile photo, human hand reaching down to a tiny shivering wet golden retriever puppy trapped in a cold alley puddle, crying teary eyes, extremely realistic wet fur, raw real life photography",
                "text": "I found this poor puppy crying in the cold rain..."
            },
            {
                "prompt": "POV first person smartphone photo, human arms holding a soaking wet puppy wrapped inside a thick towel inside a warm car, realistic relief, real candid shot",
                "text": "I immediately wrapped him up to keep him warm."
            },
            {
                "prompt": "POV candid home photo, tiny clean golden puppy eating warm food from a small bowl on the kitchen floor, wagging tail, realistic natural indoor lighting",
                "text": "After a warm bath, he had his first good meal."
            },
            {
                "prompt": "POV phone snapshot, fluffy cute golden puppy happily sleeping on the sofa next to a human hand, peaceful smiling face, warm sunlight, authentic real photo",
                "text": "He finally found his forever home ❤️"
            }
        ]
    }
]

def add_top_subtitle(image_path, text):
    """إضافة شريط النص التوضيحي أعلى الصورة تماماً مثل قنوات Shorts الاحترافية"""
    img = PIL.Image.open(image_path).convert("RGBA")
    w, h = img.size
    
    # إنشاء طبقة شفافة للنص
    overlay = PIL.Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = PIL.ImageDraw.Draw(overlay)
    
    # شريط داكن شبه شفاف في الجزء العلوي
    banner_top = int(h * 0.08)
    banner_bottom = int(h * 0.16)
    draw.rectangle([0, banner_top, w, banner_bottom], fill=(0, 0, 0, 160))
    
    # اختيار حجم الخط
    font_size = int(w * 0.045)
    try:
        font = PIL.ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except Exception:
        font = PIL.ImageFont.load_default()
        
    # توسيط النص
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    text_x = (w - text_w) // 2
    text_y = banner_top + (banner_bottom - banner_top - text_h) // 2
    
    # رسم النص باللون الأبيض
    draw.text((text_x, text_y), text, font=font, fill=(255, 255, 255, 255))
    
    # دمج وحفظ الصورة كـ RGB
    final_img = PIL.Image.alpha_composite(img, overlay).convert("RGB")
    final_img.save(image_path, "JPEG", quality=95)

def download_image(prompt, filename):
    # تعزيز الوصف لمنع أي مظهر كرتوني أو 3D أو AI art
    real_prompt = (
        f"{prompt}, raw photo, candid smartphone camera, 35mm lens, natural imperfect daylight, "
        "grain, real life, hyperrealistic, no 3d render, no anime, no cartoon, no digital art"
    )
    encoded = urllib.parse.quote(real_prompt)
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    # استخدام سيرفر التوليد الواقعي مع seed عشوائي
    for attempt in range(4):
        seed = random.randint(100000, 9999999)
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=720&height=1280&model=flux-realism&nologo=true&seed={seed}"
        
        try:
            print(f"Requesting realistic scene (attempt {attempt+1})...")
            res = requests.get(url, headers=headers, timeout=60)
            if res.status_code == 200 and len(res.content) > 15000:
                with open(filename, "wb") as f:
                    f.write(res.content)
                return
            # fallback لموديل flux الأساسي إذا كان realism مشغولاً
            elif res.status_code != 200:
                alt_url = f"https://image.pollinations.ai/prompt/{encoded}?width=720&height=1280&model=flux&nologo=true&seed={seed}"
                alt_res = requests.get(alt_url, headers=headers, timeout=60)
                if alt_res.status_code == 200 and len(alt_res.content) > 15000:
                    with open(filename, "wb") as f:
                        f.write(alt_res.content)
                    return
        except Exception as e:
            print(f"Error downloading: {e}")
        time.sleep(3)
        
    raise Exception("Failed to generate image")

def create_video(scenes):
    clips = []
    for i, item in enumerate(scenes):
        img_name = f"scene_{i}.jpg"
        print(f"Generating scene {i+1}...")
        download_image(item["prompt"], img_name)
        
        # إضافة النص التوضيحي أعلى المشهد
        add_top_subtitle(img_name, item["text"])
        
        clip = ImageClip(img_name)
        clip = clip.with_duration(3.5) if hasattr(clip, "with_duration") else clip.set_duration(3.5)
        # حركة زوم بطيئة جداً لإعطاء إيحاء الفيديو
        clip = clip.resize(lambda t: 1 + 0.02 * t)
        clips.append(clip)
        
    print("Stitching video...")
    final_clip = concatenate_videoclips(clips, method="compose")
    output_path = "shorts_video.mp4"
    final_clip.write_videofile(output_path, fps=30, codec="libx264", preset="fast")
    return output_path

def upload_video_to_github_release(video_path):
    print("Uploading to GitHub CDN Release...")
    tag_name = f"video-{int(time.time())}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    create_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases"
    release_data = {
        "tag_name": tag_name,
        "name": f"Video Release {tag_name}",
        "draft": False,
        "prerelease": False
    }
    r = requests.post(create_url, json=release_data, headers=headers)
    upload_url_template = r.json()["upload_url"].split("{")[0]
    
    upload_url = f"{upload_url_template}?name=shorts_video.mp4"
    upload_headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Content-Type": "video/mp4"
    }
    with open(video_path, "rb") as f:
        up_res = requests.post(upload_url, data=f, headers=upload_headers)
        
    return up_res.json()["browser_download_url"]

def post_to_buffer_graphql(title, caption, video_url):
    endpoint = "https://api.buffer.com"
    headers = {
        "Authorization": f"Bearer {BUFFER_TOKEN}",
        "Content-Type": "application/json"
    }

    query = """
    mutation CreatePost($input: CreatePostInput!) {
        createPost(input: $input) {
            ... on PostActionSuccess {
                post {
                    id
                    status
                }
            }
            ... on MutationError {
                message
            }
        }
    }
    """

    for pid in PROFILE_IDS:
        variables = {
            "input": {
                "channelId": pid,
                "text": caption,
                "schedulingType": "automatic",
                "mode": "shareNow",
                "assets": [
                    {
                        "video": {
                            "url": video_url
                        }
                    }
                ],
                "metadata": {
                    "youtube": {
                        "title": title,
                        "categoryId": "15"
                    }
                }
            }
        }
        res = requests.post(endpoint, json={"query": query, "variables": variables}, headers=headers)
        print(f"Publish result for {pid}: {res.status_code}")
        print(f"Response: {res.text}")

if __name__ == "__main__":
    story = random.choice(STORIES)
    print(f"Producing: {story['title']}")
    video_file = create_video(story["scenes"])
    public_url = upload_video_to_github_release(video_file)
    print(f"Public URL: {public_url}")
    post_to_buffer_graphql(story["title"], story["caption"], public_url)
