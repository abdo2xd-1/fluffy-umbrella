import os
import time
import requests
from lumaai import LumaAI

LUMA_API_KEY = os.getenv("LUMA_API_KEY", "").strip()
BUFFER_TOKEN = os.getenv("BUFFER_ACCESS_TOKEN", "").strip()
PROFILE_IDS = [pid.strip() for pid in os.getenv("BUFFER_PROFILE_IDS", "").split(",") if pid.strip()]

def generate_luma_video(prompt):
    if not LUMA_API_KEY:
        raise ValueError("LUMA_API_KEY is missing or empty.")

    client = LumaAI(auth_token=LUMA_API_KEY)

    print("Initiating Luma video generation via official SDK...")
    generation = client.generations.create(
        model="ray-1",
        prompt=prompt,
        aspect_ratio="9:16",
        loop=False
    )
    generation_id = generation.id
    print(f"Generation started successfully! Task ID: {generation_id}")

    while True:
        time.sleep(12)
        status = client.generations.get(id=generation_id)
        print(f"Current Generation State: {status.state}...")

        if status.state == "completed":
            return status.assets.video
        elif status.state == "failed":
            raise Exception(f"Luma generation failed: {status.failure_reason}")

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
        print(f"Buffer response for {pid}: {res.status_code} - {res.text}")

if __name__ == "__main__":
    prompt = "Hyper-realistic dramatic cinematic 8k, tiny poor crying ginger kitten sitting under heavy rain in a dark street puddle, big tearful eyes looking up desperately, detailed wet fur, emotional warm light in the background"
    caption = "He was left all alone in the freezing rain 💔🥺 Wait for the end! #cat #kitten #sadstory #viral #shorts #lumaai"

    print("Generating AI Video via Luma SDK...")
    video_url = generate_luma_video(prompt)
    print(f"Video direct link: {video_url}")

    print("Publishing to YouTube via Buffer GraphQL...")
    post_to_buffer_graphql(caption, video_url)
