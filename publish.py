import os
import time
import requests

LUMA_API_KEY = os.getenv("LUMA_API_KEY", "").strip()
BUFFER_TOKEN = os.getenv("BUFFER_ACCESS_TOKEN", "").strip()
PROFILE_IDS = [pid.strip() for pid in os.getenv("BUFFER_PROFILE_IDS", "").split(",") if pid.strip()]

def generate_luma_video(prompt):
    if not LUMA_API_KEY:
        raise ValueError("LUMA_API_KEY is missing or empty.")

    headers = {
        "Authorization": f"Bearer {LUMA_API_KEY}",
        "accept": "application/json",
        "content-type": "application/json"
    }
    payload = {
        "prompt": prompt,
        "aspect_ratio": "9:16",
        "loop": False
    }

    print("Initiating Luma video generation...")
    res = requests.post(
        "https://api.lumalabs.ai/dream-machine/v1/generations",
        json=payload,
        headers=headers
    )

    if res.status_code not in [200, 201]:
        raise Exception(f"Luma API Error ({res.status_code}): {res.text}")

    generation_id = res.json()["id"]
    print(f"Generation started successfully. Task ID: {generation_id}")

    status_url = f"https://api.lumalabs.ai/dream-machine/v1/generations/{generation_id}"
    while True:
        time.sleep(12)
        status_res = requests.get(status_url, headers=headers).json()
        state = status_res.get("state")
        print(f"Current Generation State: {state}...")

        if state == "completed":
            return status_res["assets"]["video"]
        elif state == "failed":
            reason = status_res.get("failure_reason", "Unknown error")
            raise Exception(f"Luma generation failed: {reason}")

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
        res = requests.post(
            endpoint,
            json={"query": query, "variables": variables},
            headers=headers
        )
        print(f"Publish result for channel {pid}: {res.status_code} - {res.text}")

if __name__ == "__main__":
    prompt = "Hyper-realistic cinematic slow motion, tiny poor crying ginger kitten sitting under heavy rain in a dark street puddle, big tearful eyes looking up desperately, detailed wet fur, emotional warm light in the background, 8k"
    caption = "He was left all alone in the freezing rain 💔🥺 Wait for the end! #cat #kitten #sadstory #viral #shorts #lumaai"

    print("Generating AI Video via Luma Dream Machine...")
    video_url = generate_luma_video(prompt)
    print(f"Video direct link: {video_url}")

    print("Publishing to YouTube via Buffer GraphQL...")
    post_to_buffer_graphql(caption, video_url)
