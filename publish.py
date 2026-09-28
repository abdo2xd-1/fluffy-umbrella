import os
import time
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

def upload_video_to_github_release(video_path):
    print("Uploading video directly to GitHub CDN Release...")
    tag_name = f"video-{int(time.time())}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    # 1. إنشاء Release جديد
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
    
    # 2. رفع ملف الفيديو داخل الـ Release للحصول على رابط CDN رسمي
    upload_url = f"{upload_url_template}?name=shorts_video.mp4"
    upload_headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Content-Type": "video/mp4"
    }
    with open(video_path, "rb") as f:
        up_res = requests.post(upload_url, data=f, headers=upload_headers)
        
    if up_res.status_code not in [200, 201]:
        raise Exception(f"Failed to upload asset: {up_res.status_code} - {up_res.text}")
        
    download_url = up_res.json()["browser_download_url"]
    return download_url

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
    
    print("Uploading video to stable CDN...")
    public_url = upload_video_to_github_release(video_file)
    print(f"Direct CDN URL: {public_url}")
    
    print("Posting to YouTube via Buffer GraphQL...")
    post_to_buffer_graphql(video_title, video_caption, public_url)
