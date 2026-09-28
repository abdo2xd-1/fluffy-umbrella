import os
import time
import random
import urllib.parse
import requests

try:
    from moviepy.editor import ImageClip, concatenate_videoclips
except (ImportError, ModuleNotFoundError):
    from moviepy import ImageClip, concatenate_videoclips

BUFFER_TOKEN = os.getenv("BUFFER_ACCESS_TOKEN", "").strip()
PROFILE_IDS = [pid.strip() for pid in os.getenv("BUFFER_PROFILE_IDS", "").split(",") if pid.strip()]
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()
GITHUB_REPO = os.getenv("GITHUB_REPOSITORY", "").strip()

# مكتبة قصص وسيناريوهات عشوائية لتنويع المحتوى يومياً
STORIES = [
    {
        "title": "Abandoned Kitten Gets a Second Chance 🥺❤️ #shorts",
        "caption": "A poor shivering kitten abandoned in the freezing rain gets saved 🥺❤️ Wait till the end! #cat #kitten #sadstory #shorts #viral #rescue",
        "scenes": [
            "cinematic close-up portrait of a tiny cute wet ginger kitten with huge glassy crying reflective eyes shivering under heavy raindrops, dark moody alley at night, street lamp reflections",
            "cinematic low angle, helpless shivering kitten sitting soaked in a rain puddle looking directly at the camera, extreme emotional facial expression, hyper-detailed whiskers and wet fur",
            "cinematic warm lighting, gentle hands softly lifting the freezing little wet kitten from the wet pavement, raindrops falling around, hope and warmth",
            "cinematic indoor cozy scene, clean fluffy dry ginger kitten happily sleeping wrapped in a thick wool blanket, peaceful face, warm ambient fire light"
        ]
    },
    {
        "title": "Little Lost Golden Puppy Left Behind in the Cold 💔🐾 #shorts",
        "caption": "He thought nobody was coming back for him 😭 Watch his reaction at the end! #dog #puppy #rescue #sadstory #emotional #shorts #viral",
        "scenes": [
            "cinematic detailed portrait of a tiny dirty golden retriever puppy shivering alone on an empty dark sidewalk, teary glassy big sad eyes",
            "cinematic cinematic street shot, muddy little puppy curled up by a closed storefront door in cold heavy rain, shivering helplessly",
            "cinematic emotional shot, a caring person wrapping the wet crying puppy inside a warm soft jacket, safe and loved",
            "cinematic bright warm home, healthy smiling fluffy puppy eating a bowl of warm food, wagging tail, cinematic soft sunlight"
        ]
    }
]

def download_image(prompt, filename):
    prompt_details = (
        f"{prompt}, ultra-realistic photography, 8k resolution, cinematic lighting, "
        "highly detailed fur, octane render, photorealistic, sharp focus, masterpiece"
    )
    encoded_prompt = urllib.parse.quote(prompt_details)
    seed = random.randint(1000, 999999)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1920&model=flux&nologo=true&seed={seed}"
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    res = requests.get(url, headers=headers, timeout=120)
    if res.status_code == 200:
        with open(filename, "wb") as f:
            f.write(res.content)
    else:
        raise Exception(f"Failed to generate high-quality image: {res.status_code}")

def create_video(scenes):
    clips = []
    for i, prompt in enumerate(scenes):
        img_name = f"scene_{i}.jpg"
        print(f"Generating scene {i+1} with Flux high-fidelity model...")
        download_image(prompt, img_name)
        
        # إنشاء مشهد مع زوم تدريجي ديناميكي (Ken Burns Effect)
        clip = ImageClip(img_name)
        clip = clip.with_duration(3.5) if hasattr(clip, "with_duration") else clip.set_duration(3.5)
        clip = clip.resize(lambda t: 1 + 0.03 * t)
        clips.append(clip)
        
    print("Combining cinematic scenes...")
    final_clip = concatenate_videoclips(clips, method="compose")
    output_path = "shorts_video.mp4"
    final_clip.write_videofile(output_path, fps=30, codec="libx264", preset="fast")
    return output_path

def upload_video_to_github_release(video_path):
    print("Uploading video directly to GitHub CDN Release...")
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
    if r.status_code not in [200, 201]:
        raise Exception(f"Failed to create release: {r.status_code} - {r.text}")
    
    upload_url_template = r.json()["upload_url"].split("{")[0]
    upload_url = f"{upload_url_template}?name=shorts_video.mp4"
    upload_headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Content-Type": "video/mp4"
    }
    with open(video_path, "rb") as f:
        up_res = requests.post(upload_url, data=f, headers=upload_headers)
        
    if up_res.status_code not in [200, 201]:
        raise Exception(f"Failed to upload asset: {up_res.status_code} - {up_res.text}")
        
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
        print(f"Publish result for channel {pid}: {res.status_code}")
        print(f"Response: {res.text}")

if __name__ == "__main__":
    story = random.choice(STORIES)
    print(f"Starting creation: {story['title']}")
    
    video_file = create_video(story["scenes"])
    public_url = upload_video_to_github_release(video_file)
    print(f"Direct CDN URL: {public_url}")
    
    print("Posting to YouTube via Buffer GraphQL...")
    post_to_buffer_graphql(story["title"], story["caption"], public_url)
