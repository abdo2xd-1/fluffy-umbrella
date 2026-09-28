import os
import time
import random
import requests
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
PEXELS_KEY = os.getenv("PEXELS_API_KEY", "").strip()

STORIES = [
    {
        "title": "A shivering kitten found alone gets a second chance 🥺❤️ #shorts",
        "caption": "Look at how much love and care can change a life! 🥺❤️ Wait till the end! #kitten #cat #rescue #heartwarming #shorts #viral",
        "queries": [
            ("kitten crying", "I found this poor shivering kitten all alone..."),
            ("cat rescue", "I immediately picked him up and kept him warm."),
            ("feeding kitten", "He was starving and drank his milk right away."),
            ("happy kitten", "Now he is safe, healthy, and full of love ❤️")
        ]
    },
    {
        "title": "Helpless puppy left behind finds a loving family 🐶❤️ #shorts",
        "caption": "Nobody stopped for him until today 😭❤️ Look at that happy smile! #puppy #dog #dogrescue #wholesome #shorts #viral",
        "queries": [
            ("sad puppy", "This little puppy was abandoned on the sidewalk..."),
            ("dog rescue", "I couldn't just walk away and leave him there."),
            ("feeding puppy", "We gave him a warm bath and a good meal."),
            ("happy dog", "He finally found his forever home and family ❤️")
        ]
    }
]

def add_top_subtitle(image_path, text):
    img = PIL.Image.open(image_path).convert("RGBA")
    w, h = img.size
    
    overlay = PIL.Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = PIL.ImageDraw.Draw(overlay)
    
    banner_top = int(h * 0.08)
    banner_bottom = int(h * 0.16)
    draw.rectangle([0, banner_top, w, banner_bottom], fill=(0, 0, 0, 180))
    
    font_size = int(w * 0.045)
    try:
        font = PIL.ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except Exception:
        font = PIL.ImageFont.load_default()
        
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    text_x = (w - text_w) // 2
    text_y = banner_top + (banner_bottom - banner_top - text_h) // 2
    
    draw.text((text_x, text_y), text, font=font, fill=(255, 255, 255, 255))
    final_img = PIL.Image.alpha_composite(img, overlay).convert("RGB")
    final_img.save(image_path, "JPEG", quality=95)

def download_pexels_image(query, filename):
    print(f"Searching Pexels for real photo: '{query}'...")
    headers = {"Authorization": PEXELS_KEY} if PEXELS_KEY else {}
    
    # محاولة البحث عن الكلمة المطلوبة
    url = f"https://api.pexels.com/v1/search?query={urllib.parse.quote(query)}&orientation=portrait&per_page=15"
    photos = []
    
    try:
        res = requests.get(url, headers=headers, timeout=20)
        if res.status_code == 200:
            photos = res.json().get("photos", [])
    except Exception as e:
        print(f"Error connecting to Pexels: {e}")

    # إذا لم توجد نتائج، ابحث بكلمات عامة مضمونة النتائج
    if not photos:
        fallback_queries = ["cat", "dog", "kitten", "puppy"]
        for fb in fallback_queries:
            try:
                res = requests.get(f"https://api.pexels.com/v1/search?query={fb}&orientation=portrait&per_page=15", headers=headers, timeout=20)
                if res.status_code == 200 and res.json().get("photos"):
                    photos = res.json()["photos"]
                    break
            except Exception:
                pass

    if photos:
        photo = random.choice(photos)
        img_url = photo["src"].get("portrait") or photo["src"].get("large2x") or photo["src"].get("large")
        img_data = requests.get(img_url, timeout=60).content
        with open(filename, "wb") as f:
            f.write(img_data)
        print(f"Successfully downloaded high-res photo from Pexels.")
    else:
        # رابط مباشر كحل أخير آمن حتى لا يسقط الاسكريبت
        fallback_url = "https://images.pexels.com/photos/45201/kitty-cat-kitten-pet-45201.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=1280&w=720"
        img_data = requests.get(fallback_url, timeout=60).content
        with open(filename, "wb") as f:
            f.write(img_data)
        print("Used high-res fallback photo.")

def create_video(story_items):
    clips = []
    for i, (search_query, subtitle) in enumerate(story_items):
        img_name = f"scene_{i}.jpg"
        download_pexels_image(search_query, img_name)
        add_top_subtitle(img_name, subtitle)
        
        clip = ImageClip(img_name)
        clip = clip.with_duration(3.5) if hasattr(clip, "with_duration") else clip.set_duration(3.5)
        clip = clip.resize(lambda t: 1 + 0.02 * t)
        clips.append(clip)
        
    print("Combining real scenes into final video...")
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
    video_file = create_video(story["queries"])
    public_url = upload_video_to_github_release(video_file)
    print(f"Direct CDN URL: {public_url}")
    post_to_buffer_graphql(story["title"], story["caption"], public_url)
