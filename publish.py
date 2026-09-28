import os
import time
import random
import urllib.parse
import requests
import PIL.Image

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
        "title": "I rescued a little bear cub that was attacked by wolves 🐺🐻 #shorts",
        "caption": "While driving through the forest, I saw a tiny cub in danger... Now he feels safe with me ❤️ #animalrescue #wildlife #bear #heartwarming #shorts #viral",
        "scenes": [
            "POV real iPhone camera shot, first-person view, human hand reaching out to touch a tiny shivering baby bear cub in the forest grass, hyperrealistic natural lighting, amateur video frame",
            "POV mobile camera footage, a cute fluffy brown bear cub sitting in the passenger seat of a car, human hand gently stroking its head, warm natural sunlight",
            "first-person perspective phone recording, little bear cub happily drinking warm milk from a bowl on the floor, authentic home video",
            "POV smartphone video frame, human hand petting a playful healthy bear cub lying on a cozy rug next to a fireplace, cozy mood"
        ]
    },
    {
        "title": "I found a tiny freezing kangaroo joey left behind 🦘❤️ #shorts",
        "caption": "He was so small and scared. Look at him now! 🥹❤️ #animalrescue #kangaroo #wildlife #wholesome #shorts #viral",
        "scenes": [
            "POV iPhone camera shot, two human hands gently holding a very tiny adorable baby kangaroo joey outdoors, looking directly into the camera lens, real smartphone video frame",
            "first-person view amateur mobile recording, baby kangaroo wrapped inside a warm green towel pouch, big glassy curious eyes, natural soft outdoor lighting",
            "POV smartphone frame, feeding a tiny kangaroo joey with a small milk bottle, human fingers holding the bottle, authentic documentary style",
            "POV phone camera footage, healthy smiling baby kangaroo hopping towards the camera indoors, cozy living room background, heartwarming"
        ]
    }
]

def download_image(prompt, filename):
    full_prompt = (
        f"{prompt}, real smartphone camera photo, candid handheld shot, natural lighting, "
        "hyperrealistic, highly detailed, unedited documentary style"
    )
    encoded = urllib.parse.quote(full_prompt)
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    # تجربة الموديلات المستقرة بالترتيب لضمان عدم السقوط
    models = ["turbo", "default"]
    
    for attempt in range(5):
        seed = random.randint(1000, 999999)
        model = models[attempt % len(models)]
        # نستخدم دقة 720x1280 وهي نسبة 9:16 المعتمدة لفيديوهات Shorts
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=720&height=1280&model={model}&nologo=true&seed={seed}"
        
        try:
            print(f"Requesting image (attempt {attempt+1}, model={model})...")
            res = requests.get(url, headers=headers, timeout=45)
            if res.status_code == 200 and len(res.content) > 10000:
                with open(filename, "wb") as f:
                    f.write(res.content)
                print(f"Successfully saved {filename}")
                return
            else:
                print(f"Status code {res.status_code}, retrying...")
        except Exception as e:
            print(f"Connection issue: {e}, retrying...")
            
        time.sleep(3)
        
    raise Exception(f"Failed to generate realistic POV image after retries")

def create_video(scenes):
    clips = []
    for i, prompt in enumerate(scenes):
        img_name = f"scene_{i}.jpg"
        print(f"Generating POV scene {i+1}...")
        download_image(prompt, img_name)
        
        clip = ImageClip(img_name)
        clip = clip.with_duration(3.5) if hasattr(clip, "with_duration") else clip.set_duration(3.5)
        # زوم ديناميكي يحاكي حركة كاميرا الموبايل الحقيقية
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
