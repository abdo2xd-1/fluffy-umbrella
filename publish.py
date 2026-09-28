import os
import time
import random
import datetime
import urllib.parse
import requests
import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont
from gtts import gTTS

# إصلاح توافق MoviePy مع إصدارات Pillow الحديثة
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.Resampling.LANCZOS

try:
    from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
except (ImportError, ModuleNotFoundError):
    from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips

BUFFER_TOKEN = os.getenv("BUFFER_ACCESS_TOKEN", "").strip()
PROFILE_IDS = [pid.strip() for pid in os.getenv("BUFFER_PROFILE_IDS", "").split(",") if pid.strip()]
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()
GITHUB_REPO = os.getenv("GITHUB_REPOSITORY", "").strip()
PEXELS_KEY = os.getenv("PEXELS_API_KEY", "").strip()

# مواضيع الشورتس المضحكة (2K Vertical)
SHORTS_TOPICS = [
    {
        "title": "Funniest Cats Being Absolute Chaos Goofballs! 😂🐱 [2K Ultra HD] #shorts",
        "caption": "Cats doing the weirdest things when they think no one is watching 😭🤣 #funnycats #catmemes #catlovers #funnypets #shorts #viral",
        "queries": ["crazy cat jumping", "funny cat face", "kitten playing funny", "silly cat running"]
    },
    {
        "title": "Dogs Being 100% Clumsy & Silly Goobers! 🐶🤣 [2K Ultra HD] #shorts",
        "caption": "Not a single thought behind those cute eyes 😂🐾 Drop a like for these silly dogs! #funnydogs #doggo #dogmemes #petlover #shorts #viral",
        "queries": ["silly dog playing", "clumsy puppy walking", "excited dog jumping", "funny dog running"]
    },
    {
        "title": "Try Not To Laugh: Crazy Pets Caught Red-Handed! 🐾😂 [2K Ultra HD] #shorts",
        "caption": "Pets acting like complete clowns caught in 2K 😭 Wait for the last clip! #funnyanimals #pets #humor #wholesome #shorts #viralvideo",
        "queries": ["funny pet playing", "kitten chasing tail", "puppy playing toy", "cute funny animal"]
    },
    {
        "title": "When The Orange Cat Braincell Disappears Completely 🐱😭 [2K Ultra HD] #shorts",
        "caption": "Orange cat energy is undefeated! Watch till the end 🤣 #orangecat #catvideos #funnycats #petsfunny #shorts",
        "queries": ["orange cat funny", "cat slipping", "kitten jumping funny", "cat playing crazy"]
    },
    {
        "title": "Golden Retrievers Being The Biggest Clowns Ever 🦮😂 [2K Ultra HD] #shorts",
        "caption": "Pure golden retriever chaos and happiness! 🥺❤️ #goldenretriever #funnydogvideos #doglovers #shorts #viral",
        "queries": ["golden retriever playing", "puppy falling playfully", "happy dog run", "dog chasing ball"]
    }
]

# مواضيع الفيديوهات الطويلة الوثائقية والمعلوماتية (2K Landscape 16:9)
LONG_DOC_TOPICS = [
    {
        "title": "Mind-Blowing Facts About Cats You Never Knew! 🐱 [2K Documentary]",
        "caption": "Did you know cats can make over 100 different vocal sounds? Discover 5 fascinating facts about your feline friends! #cats #documentary #animals #nature #facts",
        "sections": [
            {"query": "cat eyes close up", "fact": "Did you know? Cats have a unique reflective layer behind their retinas, allowing them to see in near darkness."},
            {"query": "cat jumping slow motion", "fact": "A healthy domestic cat can jump up to six times its own height in a single leap."},
            {"query": "cat purring sleeping", "fact": "Purring is not just for happiness. Cats purr at frequencies between 25 and 150 Hertz to heal their bones and muscles."},
            {"query": "kitten playing outdoors", "fact": "Cats can rotate their ears 180 degrees independently using 32 separate muscles in each ear."},
            {"query": "cute cat looking camera", "fact": "Every cat's nose print is completely unique, just like a human fingerprint!"}
        ]
    },
    {
        "title": "Incredible Secrets of Man's Best Friend: Amazing Dog Facts! 🐶 [2K Documentary]",
        "caption": "Dogs are far more intelligent and emotional than we thought. Here are incredible facts about canines! #dogs #wildlife #animalfacts #documentary",
        "sections": [
            {"query": "dog sniffing grass", "fact": "A dog's sense of smell is up to 100,000 times stronger than a human's. They can smell diseases and human emotions."},
            {"query": "dog running slow motion", "fact": "Dogs can understand up to 250 words and gestures, giving them the intelligence of a two-year-old child."},
            {"query": "happy golden retriever smiling", "fact": "When your dog looks into your eyes, both of your brains release oxytocin, the love hormone."},
            {"query": "dog sleeping dream", "fact": "Dogs dream just like humans do. If their paws twitch during sleep, they are likely chasing something in their dreams."},
            {"query": "dog wagging tail", "fact": "Tail wagging is a language: wagging to the right means happiness, while wagging to the left shows anxiety."}
        ]
    },
    {
        "title": "The Most Intelligent Animals on Earth Explained! 🐬🐘 [2K Wildlife]",
        "caption": "From memory champions to tool users, nature is full of geniuses! Watch these fascinating animal facts! #nature #wildlife #documentary #animals",
        "sections": [
            {"query": "dolphin swimming ocean", "fact": "Dolphins give each other unique names through signature whistles, calling out specific friends in the pod."},
            {"query": "elephant family nature", "fact": "Elephants have legendary memories and can recognize past companions even after decades of separation."},
            {"query": "crow bird intelligent", "fact": "Crows and ravens are master problem solvers. They can craft tools, recognize human faces, and hold grudges for years."},
            {"query": "octopus underwater", "fact": "An octopus has three hearts, nine brains, and blue blood. Two-thirds of their neurons are in their arms!"},
            {"query": "wild animals nature landscape", "fact": "Nature never ceases to amaze us with its incredible wisdom, empathy, and beauty."}
        ]
    }
]

def download_pexels_video(query, filename, orientation="portrait"):
    print(f"Searching Pexels for ({orientation}): '{query}'...")
    headers = {"Authorization": PEXELS_KEY} if PEXELS_KEY else {}
    url = f"https://api.pexels.com/videos/search?query={urllib.parse.quote(query)}&orientation={orientation}&per_page=15"
    
    videos = []
    try:
        res = requests.get(url, headers=headers, timeout=25)
        if res.status_code == 200:
            videos = res.json().get("videos", [])
    except Exception as e:
        print(f"Pexels API error: {e}")

    if not videos:
        try:
            res = requests.get(f"https://api.pexels.com/videos/search?query=wildlife animal&orientation={orientation}&per_page=10", headers=headers, timeout=25)
            if res.status_code == 200:
                videos = res.json().get("videos", [])
        except Exception:
            pass

    if videos:
        vid = random.choice(videos)
        files = vid.get("video_files", [])
        files_sorted = sorted(
            [f for f in files if f.get("file_type") == "video/mp4"],
            key=lambda x: (x.get("height", 0) * x.get("width", 0)),
            reverse=True
        )
        chosen_file = files_sorted[0].get("link") if files_sorted else None
        if chosen_file:
            print("Downloading highest quality clip...")
            vid_data = requests.get(chosen_file, timeout=90).content
            with open(filename, "wb") as f:
                f.write(vid_data)
            return

    # رابط بديل آمن
    fallback = "https://assets.mixkit.co/videos/preview/mixkit-cat-looking-attentively-41004-large.mp4"
    with open(filename, "wb") as f:
        f.write(requests.get(fallback, timeout=60).content)

def build_shorts_2k(queries, output_filename):
    """بناء فيديو شورتس بدقة 2K رأسية (1440x2560)"""
    clips = []
    for i, q in enumerate(queries):
        clip_name = f"short_{i}_{int(time.time())}.mp4"
        download_pexels_video(q, clip_name, orientation="portrait")
        try:
            sub = VideoFileClip(clip_name)
            sub = sub.subclip(0, min(3.5, sub.duration))
            sub = sub.resize(height=2560)
            if sub.w != 1440:
                sub = sub.resize((1440, 2560))
            clips.append(sub)
        except Exception as e:
            print(f"Error processing short clip: {e}")

    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(
        output_filename,
        fps=30,
        codec="libx264",
        audio=False,
        bitrate="15000k",
        ffmpeg_params=["-crf", "18", "-pix_fmt", "yuv420p"],
        preset="fast"
    )
    return output_filename

def build_long_documentary_2k(sections, output_filename):
    """بناء فيديو طويل وثائقي بدقة 2K أفقية (2560x1440) مع تعليق صوتي بالإنجليزية"""
    clips = []
    for i, sec in enumerate(sections):
        clip_name = f"long_clip_{i}_{int(time.time())}.mp4"
        audio_name = f"voice_{i}_{int(time.time())}.mp3"
        download_pexels_video(sec["query"], clip_name, orientation="landscape")
        
        # توليد صوت السرد الصوتي
        tts = gTTS(text=sec["fact"], lang='en', tld='com')
        tts.save(audio_name)
        audio_clip = AudioFileClip(audio_name)
        
        sub = VideoFileClip(clip_name)
        needed_duration = audio_clip.duration + 0.5
        
        if sub.duration < needed_duration:
            sub = sub.loop(duration=needed_duration)
        else:
            sub = sub.subclip(0, needed_duration)
            
        sub = sub.set_audio(audio_clip)
        sub = sub.resize(width=2560)
        if sub.h != 1440:
            sub = sub.resize((2560, 1440))
        clips.append(sub)

    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(
        output_filename,
        fps=30,
        codec="libx264",
        audio_codec="aac",
        bitrate="16000k",
        ffmpeg_params=["-crf", "18", "-pix_fmt", "yuv420p"],
        preset="fast"
    )
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
    now = datetime.datetime.utcnow()
    day_of_week = now.weekday()  # 0: الاثنين, 2: الأربعاء, 4: الجمعة
    hour = now.hour

    # شرط الفيديوهات الطويلة: 3 مرات في الأسبوع (الاثنين، الأربعاء، والجمعة) في وقت الذروة (13:00 UTC)
    publish_long_doc = (day_of_week in [0, 2, 4]) and (hour >= 11 and hour <= 15)
    
    print(f"Time (UTC): Weekday={day_of_week}, Hour={hour}")
    print(f"Always Publishing: SHORTS 2K (9:16)")
    if publish_long_doc:
        print(f"Bonus Scheduled: Also Publishing LONG DOCUMENTARY 2K (16:9) today!")

    # تجهيز مواضيع مختلفة لكل قناة
    random_shorts = SHORTS_TOPICS.copy()
    random.shuffle(random_shorts)
    
    random_longs = LONG_DOC_TOPICS.copy()
    random.shuffle(random_longs)

    for index, pid in enumerate(PROFILE_IDS):
        print(f"\n==========================================")
        print(f"Processing Channel {index+1} ({pid})")
        print(f"==========================================")
        
        # 1. نشر فيديو Shorts 2K دائماً وبشكل أساسي
        short_topic = random_shorts[index % len(random_shorts)]
        print(f"Creating Short: {short_topic['title']}")
        short_name = f"shorts_ch{index+1}_{int(time.time())}.mp4"
        short_file = build_shorts_2k(short_topic["queries"], short_name)
        
        short_url = upload_video_to_github_release(short_file, f"short_ch{index+1}")
        post_single_channel_to_buffer(pid, short_topic["title"], short_topic["caption"], short_url)
        time.sleep(5)
        
        # 2. في أيام (الاثنين، الأربعاء، الجمعة) يتم نشر فيديو طويل 2K إضافي على نفس القناة
        if publish_long_doc:
            long_topic = random_longs[index % len(random_longs)]
            print(f"Creating Long Documentary: {long_topic['title']}")
            long_name = f"long_ch{index+1}_{int(time.time())}.mp4"
            long_file = build_long_documentary_2k(long_topic["sections"], long_name)
            
            long_url = upload_video_to_github_release(long_file, f"long_ch{index+1}")
            post_single_channel_to_buffer(pid, long_topic["title"], long_topic["caption"], long_url)
            time.sleep(5)
        
    print("\nAll channels processed successfully with 2K content!")
