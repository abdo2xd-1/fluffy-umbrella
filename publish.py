import os
import time
import random
import asyncio
import datetime
import urllib.parse
import requests
import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont
import edge_tts

# توافق مع Pillow و MoviePy
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.Resampling.LANCZOS

try:
    from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip, concatenate_videoclips
except (ImportError, ModuleNotFoundError):
    from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip, concatenate_videoclips

BUFFER_TOKEN = os.getenv("BUFFER_ACCESS_TOKEN", "").strip()
PROFILE_IDS = [pid.strip() for pid in os.getenv("BUFFER_PROFILE_IDS", "").split(",") if pid.strip()]
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()
GITHUB_REPO = os.getenv("GITHUB_REPOSITORY", "").strip()
PEXELS_KEY = os.getenv("PEXELS_API_KEY", "").strip()

# روابط موسيقى خلفية بدون حقوق ملكية للمقاطع
BGM_SHORT_URL = "https://cdn.pixabay.com/download/audio/2022/03/15/audio_c8c8a73467.mp3?filename=funny-quirky-comedy-111162.mp3"
BGM_LONG_URL = "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3?filename=lofi-study-112191.mp3"

# استهداف سيو أمريكا وكندا وأستراليا (High CPM Geo SEO)
GEO_HASHTAGS = "#viral #shorts #pets #funnyanimals #usa #australia #canada #trending #fyp"

SHORTS_TOPICS = [
    {
        "hook": "Wait till the end! 😂",
        "title": "Funniest Cats Being Absolute Chaos Goofballs! 😂🐱 [2K Ultra HD] #shorts",
        "voice_line": "Wait till the end! Cats do the weirdest things when they think no one is watching!",
        "caption": "Cats doing the weirdest things when they think no one is watching 😭🤣 Which cat was the funniest? Comment 1, 2, or 3! 👇\n\n" + GEO_HASHTAGS,
        "queries": ["crazy cat jumping", "funny cat face", "kitten playing funny", "silly cat running"]
    },
    {
        "hook": "You won't believe clip #3! 🐶🤣",
        "title": "Dogs Being 100% Clumsy & Silly Goobers! 🐶🤣 [2K Ultra HD] #shorts",
        "voice_line": "Not a single thought behind those cute eyes! Drop a like for these silly dogs!",
        "caption": "Not a single thought behind those cute eyes 😂🐾 Are you a cat person or a dog person? Vote in the comments! 👇\n\n" + GEO_HASHTAGS,
        "queries": ["silly dog playing", "clumsy puppy walking", "excited dog jumping", "funny dog running"]
    },
    {
        "hook": "Try not to laugh challenge! 🐾",
        "title": "Try Not To Laugh: Crazy Pets Caught Red-Handed! 🐾😂 [2K Ultra HD] #shorts",
        "voice_line": "Try not to laugh! Pets acting like complete clowns caught in 4K!",
        "caption": "Did you laugh? Be honest in the comments! 😭 Wait for the last clip!\n\n" + GEO_HASHTAGS,
        "queries": ["funny pet playing", "kitten chasing tail", "puppy playing toy", "cute funny animal"]
    }
]

LONG_DOC_TOPICS = [
    {
        "title": "Mind-Blowing Facts About Cats You Never Knew! 🐱 [2K Documentary]",
        "caption": "Did you know cats can make over 100 different vocal sounds? Watch till the end for the secret! Which fact surprised you most? Comment below! 👇\n\nBest pet accessories & toys recommended in description!\n#cats #documentary #animals #nature #facts #usa #australia",
        "sections": [
            {"query": "cat eyes close up", "fact": "Did you know? Cats have a unique reflective layer behind their retinas, allowing them to see in near darkness."},
            {"query": "cat jumping slow motion", "fact": "A healthy domestic cat can jump up to six times its own height in a single leap."},
            {"query": "cat purring sleeping", "fact": "Purring is not just for happiness. Cats purr at frequencies between 25 and 150 Hertz to heal their bones and muscles."},
            {"query": "kitten playing outdoors", "fact": "Cats can rotate their ears 180 degrees independently using 32 separate muscles in each ear."},
            {"query": "cute cat looking camera", "fact": "Every cat's nose print is completely unique, just like a human fingerprint! Which fact was your favorite? Let us know below!"}
        ]
    },
    {
        "title": "Incredible Secrets of Man's Best Friend: Amazing Dog Facts! 🐶 [2K Documentary]",
        "caption": "Dogs are far more intelligent and emotional than we thought. Did your dog ever do this? Share your pet story below! 👇\n\n#dogs #wildlife #animalfacts #documentary #viral #canada #usa",
        "sections": [
            {"query": "dog sniffing grass", "fact": "A dog's sense of smell is up to 100,000 times stronger than a human's. They can even sense human emotions."},
            {"query": "dog running slow motion", "fact": "Dogs can understand up to 250 words and gestures, giving them the intelligence of a two-year-old child."},
            {"query": "happy golden retriever smiling", "fact": "When your dog looks into your eyes, both of your brains release oxytocin, the love hormone."},
            {"query": "dog sleeping dream", "fact": "Dogs dream just like humans do. If their paws twitch during sleep, they are likely chasing something in their dreams."},
            {"query": "dog wagging tail", "fact": "Tail wagging is a language: wagging to the right means happiness, while wagging to the left shows anxiety."}
        ]
    }
]

def generate_voiceover(text, output_audio_path):
    """توليد صوت بشري طبيعي وواقعي جداً من مايكروسوفت (Edge-TTS)"""
    async def _speak():
        communicate = edge_tts.Communicate(text=text, voice="en-US-ChristopherNeural")
        await communicate.save(output_audio_path)
    asyncio.run(_speak())

def download_bgm(url, filename):
    if not os.path.exists(filename):
        try:
            res = requests.get(url, timeout=30)
            if res.status_code == 200:
                with open(filename, "wb") as f:
                    f.write(res.content)
        except Exception as e:
            print(f"BGM download note: {e}")

def add_hook_overlay(clip, hook_text):
    """إضافة نص خطاف (Hook) في أول ثانيتين لرفع الـ Retention"""
    # نقتطع أول إطار لنرسم عليه الـ Banner
    w, h = clip.w, clip.h
    banner_img_path = "hook_banner.png"
    
    img = PIL.Image.new("RGBA", (w, int(h * 0.12)), (0, 0, 0, 180))
    draw = PIL.ImageDraw.Draw(img)
    font_size = int(w * 0.05)
    try:
        font = PIL.ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except Exception:
        font = PIL.ImageFont.load_default()
        
    bbox = draw.textbbox((0, 0), hook_text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    draw.text(((w - text_w) // 2, (int(h * 0.12) - text_h) // 2), hook_text, font=font, fill=(255, 230, 0, 255))
    img.save(banner_img_path)
    
    from moviepy.editor import ImageClip
    hook_clip = ImageClip(banner_img_path).set_duration(min(2.5, clip.duration)).set_position(("center", int(h * 0.1)))
    from moviepy.editor import CompositeVideoClip
    return CompositeVideoClip([clip, hook_clip])

def download_pexels_video(query, filename, orientation="portrait"):
    headers = {"Authorization": PEXELS_KEY} if PEXELS_KEY else {}
    url = f"https://api.pexels.com/videos/search?query={urllib.parse.quote(query)}&orientation={orientation}&per_page=15"
    videos = []
    try:
        res = requests.get(url, headers=headers, timeout=25)
        if res.status_code == 200:
            videos = res.json().get("videos", [])
    except Exception as e:
        print(f"Pexels error: {e}")

    if not videos:
        try:
            res = requests.get(f"https://api.pexels.com/videos/search?query=funny pet&orientation={orientation}&per_page=10", headers=headers, timeout=25)
            if res.status_code == 200:
                videos = res.json().get("videos", [])
        except Exception:
            pass

    if videos:
        vid = random.choice(videos)
        files = vid.get("video_files", [])
        files_sorted = sorted([f for f in files if f.get("file_type") == "video/mp4"], key=lambda x: (x.get("height", 0) * x.get("width", 0)), reverse=True)
        chosen = files_sorted[0].get("link") if files_sorted else None
        if chosen:
            with open(filename, "wb") as f:
                f.write(requests.get(chosen, timeout=90).content)
            return

    fallback = "https://assets.mixkit.co/videos/preview/mixkit-cat-looking-attentively-41004-large.mp4"
    with open(filename, "wb") as f:
        f.write(requests.get(fallback, timeout=60).content)

def build_shorts_2k(topic, output_filename):
    """إنتاج فيديو Shorts بدقة 2K رأسية مع تعليق صوتي طبيعي وموسيقى خلفية"""
    clips = []
    for i, q in enumerate(topic["queries"]):
        clip_name = f"short_{i}_{int(time.time())}.mp4"
        download_pexels_video(q, clip_name, orientation="portrait")
        try:
            sub = VideoFileClip(clip_name)
            sub = sub.subclip(0, min(3.2, sub.duration))
            sub = sub.resize(height=2560)
            if sub.w != 1440:
                sub = sub.resize((1440, 2560))
            clips.append(sub)
        except Exception as e:
            print(f"Clip error: {e}")

    final_video = concatenate_videoclips(clips, method="compose")
    
    # إضافة Hook في الثواني الأولى
    try:
        final_video = add_hook_overlay(final_video, topic["hook"])
    except Exception as e:
        print(f"Hook overlay warning: {e}")

    # توليد التعليق الصوتي الصوتي الخاطف من Edge-TTS
    voice_path = f"voice_short_{int(time.time())}.mp3"
    generate_voiceover(topic["voice_line"], voice_path)
    voice_clip = AudioFileClip(voice_path)

    # موسيقى خلفية بدون حقوق مع تخفيض مستوى الصوت (Audio Ducking)
    bgm_path = "short_bgm.mp3"
    download_bgm(BGM_SHORT_URL, bgm_path)
    
    audio_tracks = [voice_clip.volumex(1.2)]
    if os.path.exists(bgm_path):
        try:
            bgm = AudioFileClip(bgm_path).subclip(0, final_video.duration).volumex(0.2)
            audio_tracks.append(bgm)
        except Exception:
            pass

    final_audio = CompositeAudioClip(audio_tracks)
    final_video = final_video.set_audio(final_audio)

    final_video.write_videofile(
        output_filename,
        fps=30,
        codec="libx264",
        audio_codec="aac",
        bitrate="15000k",
        ffmpeg_params=["-crf", "18", "-pix_fmt", "yuv420p"],
        preset="fast"
    )
    return output_filename

def build_long_documentary_2k(sections, output_filename):
    """إنتاج فيديو وثائقي طويل 2K (16:9) مع Edge-TTS وموسيقى هادئة"""
    clips = []
    bgm_path = "long_bgm.mp3"
    download_bgm(BGM_LONG_URL, bgm_path)

    for i, sec in enumerate(sections):
        clip_name = f"long_clip_{i}_{int(time.time())}.mp4"
        audio_name = f"voice_doc_{i}_{int(time.time())}.mp3"
        download_pexels_video(sec["query"], clip_name, orientation="landscape")
        
        # صوت Edge-TTS البشري
        generate_voiceover(sec["fact"], audio_name)
        voice_clip = AudioFileClip(audio_name)
        
        sub = VideoFileClip(clip_name)
        needed_duration = voice_clip.duration + 0.5
        
        if sub.duration < needed_duration:
            sub = sub.loop(duration=needed_duration)
        else:
            sub = sub.subclip(0, needed_duration)
            
        sub = sub.set_audio(voice_clip.volumex(1.3))
        sub = sub.resize(width=2560)
        if sub.h != 1440:
            sub = sub.resize((2560, 1440))
        clips.append(sub)

    final_video = concatenate_videoclips(clips, method="compose")

    # إضافة موسيقى Lo-Fi خفيفة جداً في الخلفية مع التعليق الصوتي
    if os.path.exists(bgm_path):
        try:
            bgm = AudioFileClip(bgm_path).subclip(0, final_video.duration).volumex(0.15)
            final_audio = CompositeAudioClip([final_video.audio, bgm])
            final_video = final_video.set_audio(final_audio)
        except Exception as e:
            print(f"Long BGM warning: {e}")

    final_video.write_videofile(
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
                    "categoryId": "15"
                }
            }
        }
    }
    res = requests.post(endpoint, json={"query": query, "variables": variables}, headers=headers)
    print(f"Publish result for {channel_id}: {res.status_code}")
    print(f"Response: {res.text}")

if __name__ == "__main__":
    now = datetime.datetime.utcnow()
    day_of_week = now.weekday()
    hour = now.hour

    publish_long_doc = (day_of_week in [0, 2, 4]) and (hour >= 11 and hour <= 15)
    
    print(f"Time (UTC): Weekday={day_of_week}, Hour={hour}")
    print("Always Publishing: High-Retention 2K Shorts (9:16)")
    if publish_long_doc:
        print("Bonus Scheduled: Also Publishing LONG DOCUMENTARY 2K (16:9) today!")

    random_shorts = SHORTS_TOPICS.copy()
    random.shuffle(random_shorts)
    
    random_longs = LONG_DOC_TOPICS.copy()
    random.shuffle(random_longs)

    for index, pid in enumerate(PROFILE_IDS):
        print(f"\n==========================================")
        print(f"Processing Channel {index+1} ({pid})")
        print(f"==========================================")
        
        # 1. Shorts مع صوت طبيعي وموسيقى وHook
        short_topic = random_shorts[index % len(random_shorts)]
        print(f"Creating Short: {short_topic['title']}")
        short_name = f"shorts_ch{index+1}_{int(time.time())}.mp4"
        short_file = build_shorts_2k(short_topic, short_name)
        
        short_url = upload_video_to_github_release(short_file, f"short_ch{index+1}")
        post_single_channel_to_buffer(pid, short_topic["title"], short_topic["caption"], short_url)
        time.sleep(5)
        
        # 2. فيديو طويل وثائقي 2K بصوت Edge-TTS وموسيقى في أيام النشر المخصصة
        if publish_long_doc:
            long_topic = random_longs[index % len(random_longs)]
            print(f"Creating Long Documentary: {long_topic['title']}")
            long_name = f"long_ch{index+1}_{int(time.time())}.mp4"
            long_file = build_long_documentary_2k(long_topic["sections"], long_name)
            
            long_url = upload_video_to_github_release(long_file, f"long_ch{index+1}")
            post_single_channel_to_buffer(pid, long_topic["title"], long_topic["caption"], long_url)
            time.sleep(5)
        
    print("\nAll channels updated with High-Retention Audio & 2K Video successfully!")
