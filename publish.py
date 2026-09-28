import os
import urllib.parse
import requests

try:
    from moviepy.editor import ImageClip, concatenate_videoclips
except (ImportError, ModuleNotFoundError):
    from moviepy import ImageClip, concatenate_videoclips

BUFFER_TOKEN = os.getenv("BUFFER_ACCESS_TOKEN", "").strip()
PROFILE_IDS = [pid.strip() for pid in os.getenv("BUFFER_PROFILE_IDS", "").split(",") if pid.strip()]

def download_image(prompt, filename):
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=720&height=1280&nologo=true"
    res = requests.get(url, timeout=60)
    if res.status_code == 200:
        with open(filename, "wb") as f:
            f.write(res.content)
    else:
        raise Exception(f"Failed to generate image: {res.status_code}")

def create_video():
    scenes = [
        "cinematic 8k, cute tiny crying ginger kitten in heavy rain on dark street, emotional tearful eyes",
        "cinematic 8k, shivering sad kitten sitting in water puddle, looking up begging for food",
        "cinematic 8k, warm gentle human hands picking up the wet kitten, safe and cozy",
        "cinematic 8k, happy clean ginger kitten purring in a warm blanket, happy ending"
    ]
    
    clips = []
    for i, prompt in enumerate(scenes):
        img_name = f"scene_{i}.jpg"
        print(f"Generating scene {i+1} via Pollinations (Free)...")
        download_image(prompt, img_name)
        
        clip = ImageClip(img_name)
        clip = clip.with_duration(3) if hasattr(clip, "with_duration") else clip.set_duration(3)
        clips.append(clip)
        
    print("Combining scenes into final video...")
    final_clip = concatenate_videoclips(clips, method="compose")
    output_path = "shorts_video.mp4"
    final_clip.write_videofile(output_path, fps=24, codec="libx264")
    return output_path

def upload_video(video_path):
    print("Uploading video via reliable public host...")
    # محاولة الرفع عبر 0x0.st
    try:
        with open(video_path, "rb") as f:
            res = requests.post("https://0x0.st", files={"file": f}, timeout=120)
            if res.status_code == 200 and res.text.strip().startswith("http"):
                return res.text.strip()
    except Exception as e:
        print(f"0x0.st upload failed ({e}), trying fallback...")

    # حل بديل مؤكد عبر file.io
    with open(video_path, "rb") as f:
        res = requests.post("https://file.io", files={"file": f}, timeout=120)
        data = res.json()
        if data.get("success"):
            return data["link"]
        raise Exception(f"Upload failed: {res.text}")

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
    video_title = "Abandoned Kitten Gets a Second Chance 🥺❤️ #shorts"
    video_caption = "A poor kitten abandoned in the freezing rain gets saved 🥺❤️ Wait till the end! #cat #kitten #sadstory #shorts #viral #rescue"
    
    print("Creating AI Video...")
    video_file = create_video()
    
    print("Uploading video...")
    public_url = upload_video(video_file)
    print(f"Direct CDN URL: {public_url}")
    
    print("Posting to YouTube via Buffer GraphQL...")
    post_to_buffer_graphql(video_title, video_caption, public_url)
