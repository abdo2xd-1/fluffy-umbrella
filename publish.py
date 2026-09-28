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

def upload_to_tmpfiles(video_path):
    print("Uploading video to get public URL...")
    with open(video_path, "rb") as f:
        res = requests.post("https://tmpfiles.org/api/v1/upload", files={"file": f})
    data = res.json()
    url = data["data"]["url"]
    return url.replace("https://tmpfiles.org/", "https://tmpfiles.org/dl/")

def post_to_buffer_graphql(caption, video_url):
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
            ... on UserError {
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
                "media": {
                    "video": {
                        "url": video_url
                    }
                },
                "schedulingType": "now"
            }
        }
        res = requests.post(endpoint, json={"query": query, "variables": variables}, headers=headers)
        print(f"Publish result for channel {pid}: {res.status_code} - {res.text}")

if __name__ == "__main__":
    caption = "A poor kitten abandoned in the rain gets a second chance 🥺❤️ #cat #kitten #story #shorts #viral"
    
    print("Creating AI Video...")
    video_file = create_video()
    
    print("Generating public download link...")
    public_url = upload_to_tmpfiles(video_file)
    print(f"Direct URL: {public_url}")
    
    print("Posting to social channels via Buffer GraphQL...")
    post_to_buffer_graphql(caption, public_url)
