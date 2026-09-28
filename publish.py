import os
import time
import random
import urllib.parse
import requests
import PIL.Image

# حل مشكلة توافق Pillow مع MoviePy
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

# مكتبة أفكار متنوعة لضمان محتوى مستقل ومختلف لكل قناة
FUNNY_TOPICS = [
    {
        "title": "Funniest Cats Being Absolute Chaos Goofballs! 😂🐱 #shorts",
        "caption": "Cats doing the weirdest things when they think no one is watching 😭🤣 #funnycats #catmemes #catlovers #funnypets #shorts #viral",
        "queries": ["crazy cat jumping", "funny cat face", "kitten playing funny", "silly cat running"]
    },
    {
        "title": "Dogs Being 100% Clumsy & Silly Goobers! 🐶🤣 #shorts",
        "caption": "Not a single thought behind those cute eyes 😂🐾 Drop a like for these silly dogs! #funnydogs #doggo #dogmemes #petlover #shorts #viral",
        "queries": ["silly dog playing", "clumsy puppy walking", "excited dog jumping", "funny dog running"]
    },
    {
        "title": "Try Not To Laugh: Crazy Pets Caught Red-Handed! 🐾😂 #shorts",
        "caption": "Pets acting like complete clowns caught in 4K 😭 Wait for the last clip! #funnyanimals #pets #humor #wholesome #shorts #viralvideo",
        "queries": ["funny pet playing", "kitten chasing tail", "puppy playing toy", "cute funny animal"]
    },
    {
        "title": "When The Orange Cat Braincell Disappears Completely 🐱😭 #shorts",
        "caption": "Orange cat energy is undefeated! Watch till the end 🤣 #orangecat #catvideos #funnycats #petsfunny #shorts",
        "queries": ["orange cat funny", "cat slipping", "kitten jumping funny", "cat playing crazy"]
    },
    {
        "title": "Golden Retrievers Being The Biggest Clowns Ever 🦮😂 #shorts",
        "caption": "Pure golden retriever chaos and happiness! 🥺❤️ #goldenretriever #funnydogvideos #doglovers #shorts #viral",
        "queries": ["golden retriever playing", "puppy falling playfully", "happy dog run", "dog chasing ball"]
    }
]

def download_pexels_video(query, filename):
    print(f"Searching Pexels for: '{query}'...")
    headers = {"Authorization": PEXELS_KEY} if PEXELS_KEY else {}
    
    url = f"https://api.pexels.com/videos/search?query={urllib.parse.quote(query)}&orientation=portrait&per_page=15"
    videos = []
    
    try:
        res = requests.get(url, headers=headers, timeout=25)
        if res.status_code == 200:
            videos = res.json().get("videos", [])
    except Exception as e:
        print(f"Pexels API issue: {e}")

    if not videos:
        try:
            res = requests.get("https://api.pexels.com/videos/search?query=funny animal&orientation=portrait&per_page=10", headers=headers, timeout=25)
            if res.status_code == 200:
                videos = res.json().get("videos", [])
        except Exception:
            pass

    if videos:
        # اختيار مقطع عشوائي من النتائج لضمان التنوع
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
            print(f"Downloading clip to {filename}...")
            vid_data = requests.get(chosen_file, timeout=60).content
            with open(filename, "wb") as f:
                f.write(vid_data)
            return

    # رابط احتياطي آمن
    fallback_url = "https://assets.mixkit.co/videos/preview/mixkit-cat-looking-attentively-41004-large.mp4"
    vid_data = requests.get(fallback_url, timeout=60).content
    with open(filename, "wb") as f:
        f.write(vid_data)

def build_compilation(queries, output_filename):
    clips = []
    for i, q in enumerate(queries):
        clip_name = f"temp_{i}_{int(time.time())}.mp4"
        download_pexels_video(q, clip_name)
        
        try:
            sub = VideoFileClip(clip_name)
            duration = min(3.5, sub.duration)
            sub = sub.subclip(0, duration)
            sub = sub.resize(height=1280)
            if sub.w != 720:
                sub = sub.resize((720, 1280))
            clips.append(sub)
        except Exception as e:
            print(f"Warning processing clip {clip_name}: {e}")
        
    print(f"Stitching clips into {output_filename}...")
    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(output_filename, fps=30, codec="libx264", audio=False, preset="fast")
    return output_filename

def upload_video_to_github_release(video_path, asset_label):
    print(f"Uploading {asset_label} to GitHub CDN Release...")
    tag_name = f"rel-{asset_label}-{int(time.time())}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    create_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases"
    release_data = {
        "tag_name": tag_name,
        "name": f"Release {tag_name}",
        "draft": False,
        "prerelease": False
    }
    r = requests.post(create_url, json=release_data, headers=headers)
    upload_url_template = r.json()["upload_url"].split("{")[0]
    
    clean_name = os.path.basename(video_path)
    upload_url = f"{upload_url_template}?name={clean_name}"
    upload_headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Content-Type": "video/mp4"
    }
    with open(video_path, "rb") as f:
        up_res = requests.post(upload_url, data=f, headers=upload_headers)
        
    return up_res.json()["browser_download_url"]

def post_single_channel_to_buffer(channel_id, title, caption, video_url):
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

    variables = {
        "input": {
            "channelId": channel_id,
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
                    "categoryId": "15" # تصنيف الحيوانات الأليفة
                }
            }
        }
    }
    res = requests.post(endpoint, json={"query": query, "variables": variables}, headers=headers)
    print(f"Publish result for {channel_id}: {res.status_code}")
    print(f"Response: {res.text}")

if __name__ == "__main__":
    print(f"Found {len(PROFILE_IDS)} connected channels.")
    
    # خلط المواضيع لضمان عدم تكرار نفس الفكرة للقنوات في نفس اليوم
    available_topics = FUNNY_TOPICS.copy()
    random.shuffle(available_topics)

    for index, pid in enumerate(PROFILE_IDS):
        topic = available_topics[index % len(available_topics)]
        print(f"\n==========================================")
        print(f"Generating unique video for Channel {index+1} ({pid})")
        print(f"Topic: {topic['title']}")
        print(f"==========================================")
        
        output_name = f"shorts_channel_{index+1}.mp4"
        video_file = build_compilation(topic["queries"], output_name)
        
        # رفع الفيديو برابط CDN خاص به
        public_url = upload_video_to_github_release(video_file, f"ch{index+1}")
        print(f"Public URL: {public_url}")
        
        # النشر على هذه القناة فقط
        post_single_channel_to_buffer(pid, topic["title"], topic["caption"], public_url)
        time.sleep(5)
        
    print("\nAll channels updated with unique custom videos successfully!")
