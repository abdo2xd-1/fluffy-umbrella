import os
import time
import requests

LUMA_API_KEY = os.getenv("LUMA_API_KEY")
BUFFER_TOKEN = os.getenv("BUFFER_ACCESS_TOKEN")
PROFILE_IDS = os.getenv("BUFFER_PROFILE_IDS", "").split(",")

def generate_luma_video(prompt):
    headers = {
        "Authorization": f"Bearer {LUMA_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "prompt": prompt,
        "aspect_ratio": "9:16",
        "loop": False
    }
    
    print("Initiating Luma video generation...")
    res = requests.post("https://api.lumalabs.ai/dream-machine/v1/generations", json=payload, headers=headers)
    
    if res.status_code not in [200, 201]:
        raise Exception(f"Luma API Error ({res.status_code}): {res.text}")
        
    generation_id = res.json()["id"]
    print(f"Generation started successfully! Task ID: {generation_id}")
    
    # متابعة حالة التوليد حتى يكتمل الفيديو
    status_url = f"https://api.lumalabs.ai/dream-machine/v1/generations/{generation_id}"
    while True:
        time.sleep(12)
        status_res = requests.get(status_url, headers=headers).json()
        state = status_res.get("state")
        print(f"Current Generation State: {state}...")
        
        if state == "completed":
            video_url = status_res["assets"]["video"]
            return video_url
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
        pid = pid.strip()
        if not pid:
            continue
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
        print(f"Publish result for channel {pid}: {res.status_code}")
        print(res.text)

if __name__ == "__main__":
    prompt = "Hyper-realistic dramatic cinematic 8k, tiny poor crying ginger kitten sitting under heavy rain in a dark street puddle, big tearful eyes looking up desperately, detailed wet fur, emotional warm light in the background"
    caption = "He was left all alone in the freezing rain 💔🥺 #cat #kitten #sadstory #viral #shorts #lumaai"
    
    print("Generating AI Video via Luma Dream Machine...")
    video_url = generate_luma_video(prompt)
    print(f"Finished! Video direct link: {video_url}")
    
    print("Publishing to YouTube via Buffer GraphQL...")
    post_to_buffer_graphql(caption, video_url)
