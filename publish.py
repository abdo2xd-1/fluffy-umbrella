import os
import requests
import fal_client

FAL_KEY = os.getenv("FAL_KEY", "").strip()
BUFFER_TOKEN = os.getenv("BUFFER_ACCESS_TOKEN", "").strip()
PROFILE_IDS = [pid.strip() for pid in os.getenv("BUFFER_PROFILE_IDS", "").split(",") if pid.strip()]

def generate_video_with_fal(prompt):
    if not FAL_KEY:
        raise ValueError("FAL_KEY is missing or empty in secrets.")

    print("Sending generation request to Fal.ai...")

    # استخدام نموذج LTX-Video السريع والسينمائي
    result = fal_client.subscribe(
        "fal-ai/ltx-video",
        arguments={
            "prompt": prompt,
            "aspect_ratio": "9:16"
        },
        with_logs=True
    )

    video_url = result.get("video", {}).get("url")
    if not video_url:
        raise Exception(f"Failed to extract video url from result: {result}")

    return video_url

def post_to_buffer_graphql(caption, video_url):
    endpoint = "https://api.buffer.com"
    headers = {
        "Authorization": f"Bearer {BUFFER_TOKEN}",
        "Content-Type": "application/json"
    }

    query = """
    mutation CreatePost($input: CreatePostInput!) {
        createPost(input: $input) {
            post {
                id
                status
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
    prompt_text = "Cinematic slow motion, adorable tiny crying ginger kitten shivering under heavy rain in a dark alley, big glassy emotional tearful eyes, photorealistic 8k, hyper detailed fur"
    caption_text = "Nobody would stop for him in the freezing rain 💔🥺 Wait till the end! #cat #kitten #sadstory #viral #shorts #ai"

    print("Generating cinematic AI video via Fal.ai...")
    video_url = generate_video_with_fal(prompt_text)
    print(f"Video generated successfully: {video_url}")

    print("Publishing to YouTube via Buffer GraphQL...")
    post_to_buffer_graphql(caption_text, video_url)
