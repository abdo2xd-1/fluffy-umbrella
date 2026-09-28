import os
import time
import random
import urllib.parse
import requests
import PIL.Image

# حل مشكلة MoviePy مع إصدارات Pillow الحديثة
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.Resampling.LANCZOS

try:
    from moviepy.editor import VideoFileClip, concatenate_videoclips
except (ImportError, ModuleNotFoundError):
    from moviepy import VideoFileClip, concatenate_videoclips

BUFFER_TOKEN = os.getenv("BUFFER_ACCESS_TOKEN", "").strip()
PROFILE_IDS = [pid.strip() for pid in os.getenv("BUFFER_PROFILE_IDS", "").split(",") if pid.strip()]
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()
GITHUB_REPO = os.getenv("GITHUB_REPOSITORY", "").strip()
PEXELS_KEY = os.getenv("PEXELS_API_KEY", "").strip()

FUNNY_TOPICS = [
    {
        "title": "Try Not To Laugh - Funniest Cats & Dogs Ever! 😂🐶🐱 #shorts",
        "caption": "Cats and dogs being absolute chaotic goofballs! 😂 Wait for the last clip! #funnyanimals #funnycats #funnydogs #pets #shorts #viral",
        "queries": ["funny cat", "funny dog", "playful kitten", "silly dog playing"]
    },
    {
        "title": "When Cats Think Nobody Is Watching Them 😂🐾 #shorts",
        "caption": "Orange cat energy is unmatched! 😭🤣 Drop a like for these silly pets! #catlovers #funnypets #catmemes #shorts #humor",
        "queries": ["crazy cat jump", "silly cat", "kitten chasing", "clumsy cat"]
    },
    {
        "title": "Guilty Dogs Caught Red-Handed! 🐶🤣 #shorts",
        "caption": "Their reactions when they get busted doing nonsense! 😭😂 #funnydogs #doggo #petsfunny #shorts #viralvideos",
        "queries": ["guilty dog", "excited dog run", "dog funny reaction", "clumsy dog"]
    }
]

def download_pexels_video(query, filename):
    print(f"Searching Pexels for FUNNY video clip: '{query}'...")
    headers = {"Authorization": PEXELS_KEY} if PEXELS_KEY else {}
    
    url = f"https://api.pexels.com/videos/search?query={urllib.parse.quote(query)}&orientation=portrait&per_page=12"
    videos = []
    
    try:
        res = requests.get(url, headers=headers, timeout=25)
        if res.status_code == 200:
            videos = res.json().get("videos", [])
    except Exception as e:
        print(f"Error connecting to Pexels Video API: {e}")

    if not videos:
        try:
            res = requests.get("https://api.pexels.com/videos/search?query=funny pet&orientation=portrait&per_page=10", headers=headers, timeout=25)
            if res.status_code == 200:
                videos = res.json().get("videos", [])
        except Exception:
            pass

    if videos:
        vid = random.choice(videos)
        chosen_file = None
        for file in vid.get("video_files", []):
            if file.get("file_type") == "video/mp4":
                chosen_file = file.get("link")
                if file.get("height", 0) >= 720:
                    break
                    
        if not chosen_file and vid.get("video_files"):
            chosen_file = vid["video_files"][0].get("link")

        if chosen_file:
            print(f"Downloading MP4 clip from: {chosen_file[:40]}...")
            vid_data = requests.get(chosen_file, timeout=60).content
            with open(filename, "wb") as f:
                f.write(vid_data)
            print("Clip downloaded successfully.")
            return

    fallback_url = "https://assets.mixkit.co/videos/preview/mixkit-cat-looking-attentively-41004-large.mp4"
    vid_data = requests.get(fallback_url, timeout=60).content
    with open(filename, "wb") as f:
        f.write(vid_data)
    print("Used fallback funny pet clip.")

def build_compilation(queries):
    clips = []
    for i, q in enumerate(queries):
        clip_name = f"clip_{i}.mp4"
        download_pexels_video(q, clip_name)
        
        sub = VideoFileClip(clip_name)
        duration = min(4.0, sub.duration)
        sub = sub.subclip(0, duration)
        
        # تغيير الأبعاد مع الحفاظ على التوافق التام
        sub = sub.resize(height=1280)
        if sub.w != 720:
            sub = sub.resize((720, 1280))
            
        clips.append(sub)
        
    print("Combining funny moments into final Shorts video...")
    final = concatenate_videoclips(clips, method="compose")
    output_path = "shorts_video.mp4"
    final.write_videofile(output_path, fps=30, codec="libx264", audio=False, preset="fast")
    return output_path

def upload_video_to_github_release(video_path):
    print("Uploading to GitHub CDN...")
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
    topic = random.choice(FUNNY_TOPICS)
    print(f"Producing funny compilation: {topic['title']}")
    video_file = build_compilation(topic["queries"])
    public_url = upload_video_to_github_release(video_file)
    print(f"Direct CDN URL: {public_url}")
    post_to_buffer_graphql(topic["title"], topic["caption"], public_url)
