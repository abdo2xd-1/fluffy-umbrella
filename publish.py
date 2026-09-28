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
        "title": "A shivering kitten found alone in the cold gets a second chance 🥺❤️ #shorts",
        "caption": "Look at how much love and care can change a life! 🥺❤️ Wait till the end! #kitten #cat #rescue #heartwarming #shorts #viral",
        "queries": [
            ("sad wet kitten", "I found this poor shivering kitten all alone..."),
            ("person holding kitten", "I immediately picked him up and kept him warm."),
            ("feeding baby kitten milk", "He was starving and drank his milk right away."),
            ("cute happy sleeping kitten", "Now he is safe, healthy, and full of love ❤️")
        ]
    },
    {
        "title": "Helpless puppy left behind finds a loving family 🐶❤️ #shorts",
        "caption": "Nobody stopped for him until today 😭❤️ Look at that happy smile! #puppy #dog #dogrescue #wholesome #shorts #viral",
        "queries": [
            ("sad lonely puppy street", "This little puppy was abandoned on the sidewalk..."),
            ("human hands holding puppy", "I couldn't just walk away and leave him there."),
            ("puppy eating food bowl", "We gave him a warm bath and a good meal."),
            ("happy golden puppy playing", "He finally found his forever home and family ❤️")
        ]
    },
    {
        "title": "Rescuing an injured baby animal in the woods 🐻🌲 #shorts",
        "caption": "Every life deserves a helping hand 🥺❤️ #wildlife #rescue #nature #animalrescue #shorts #viral",
        "queries": [
            ("baby animal forest woods", "We spotted this tiny baby animal lost in the woods..."),
            ("caring hands wild animal", "Carefully making sure it wasn't hurt."),
            ("wildlife rehab animal care", "Giving him the shelter and care he needed."),
            ("happy cute baby animal nature", "Now healthy, protected, and thriving in peace ❤️")
        ]
    }
]

def add_top_subtitle(image_path, text):
    """إضافة شريط النص التوضيحي أعلى الصورة تماماً كالفيديوهات الاحترافية"""
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
    url = f"https://api.pexels.com/v1/search?query={query}&orientation=portrait&per_page=15"
    headers = {"Authorization": PEXELS_KEY}
    
    res = requests.get(url, headers=headers, timeout=30)
    data = res.json()
    
    photos = data.get("photos", [])
    if not photos:
        # بحث بديل عام في حال لم توجد نتائج محددة
        url = f"https://api.pexels.com/v1/search?query=cute animal&orientation=portrait&per_page=15"
        res = requests.get(url, headers=headers, timeout=30)
        photos = res.json().get("photos", [])

    photo = random.choice(photos)
    # جلب الصورة بأعلى دقة عمودية portrait
    img_url = photo["src"].get("portrait") or photo["src"].get("large2x")
    
    img_data = requests.get(img_url, timeout=60).content
    with open(filename, "wb") as f:
        f.write(img_data)
    print(f"Successfully downloaded high-res photo from Pexels.")

def create_video(story_items):
    clips = []
    for i, (search_query, subtitle) in enumerate(story_items):
        img_name = f"scene_{i}.jpg"
        download_pexels_image(search_query, img_name)
        
        # إضافة شريط السرد في الأعلى
        add_top_subtitle(img_name, subtitle)
        
        clip = ImageClip(img_name)
        clip = clip.with_duration(3.5) if hasattr(clip, "with_duration") else clip.set_duration(3.5)
        # حركة سينمائية هادئة
        clip = clip.resize(lambda t: 1 + 0.02 * t)
        clips.append(clip)
        
    print("Combining real 4K scenes into final video...")
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
