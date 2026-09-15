# INF601 - Advanced Programming in Python
# Brennan Adams
# Scheduled Check-In Bot

import os
import json
import requests

from dotenv import load_dotenv
load_dotenv()

BASE_URL = os.getenv("BASE_URL")
TOKEN = os.getenv("TOKEN")

OUTPUT_DIR = "artifact"
FILES_DIR = os.path.join(OUTPUT_DIR, "files")
INSTRUCTOR_ID = int(os.getenv("INSTRUCTOR_ID", "7"))
MY_USER_ID = int(os.getenv("MY_USER_ID", "21"))

os.makedirs(FILES_DIR, exist_ok=True)

def get_posts():
    try:
        headers = {"Authorization": f"Bearer {TOKEN}"}
        resp = requests.get(f"{BASE_URL}/api/v1/posts", headers=headers)
        if resp.status_code != 200:
            print("Error:", resp.status_code, resp.text)
            return None
    except requests.exceptions.HTTPError as e:
        print("HTTP error: ", e)
    except Exception as e:
        print("Unexpected error: ", e)

    return resp.json()

def download_attachment(att):
    filename=att["filename"]
    url=att["download_url"]

    if(url.startswith("/")):
        url = BASE_URL + url

    file_path = os.path.join(FILES_DIR, filename)

    r=requests.get(url,headers={"Authorization": f"Bearer {TOKEN}"})
    r.raise_for_status()

    with open(file_path, "wb") as f:
        f.write(r.content)

    return file_path

def is_checkin_post(post):
    title = post.get("title", "").lower()
    return "check-in" in title

def reply_to_checkin(post_id):
    try:
        url=f"{BASE_URL}/api/v1/posts/{post_id}/comments"
        headers={"Authorization": f"Bearer {TOKEN}"}
        payload={"body": "Checking in!"}

        resp = requests.post(url, headers=headers, json=payload)

        if(resp.status_code==201):
            #print(f"✓ Replied to check-in {post_id}")
            return True

        if resp.status_code==423:
            #print(f"✗ Window closed for {post_id} (423)")
            return False

        #print(f"✗ Error replying to {post_id}: {resp.status_code} {resp.text}")
        return False
    except requests.exceptions.HTTPError as e:
        #print("HTTP error: ", e)
        return False
    except Exception as e:
        #print("Unexpected error: ", e)
        return False

def has_already_replied(post_id):
    url = f"{BASE_URL}/api/v1/posts/{post_id}/comments"
    headers = {"Authorization": f"Bearer {TOKEN}"}

    resp= requests.get(url, headers=headers)

    if resp.status_code != 200:
        #print("Error fetching comments for {post_id}: {resp.status_code}")
        return False

    comments = resp.json()

    #Find one of my responses if it exists
    for c in comments:
        if(c.get("author_id") == MY_USER_ID):
            return True

    return False

def main():
    raw_posts = get_posts()

    if raw_posts == None: return
    instructor_posts = [p for p in raw_posts if p.get("author_id", 0) == INSTRUCTOR_ID]
    collected = []

    for post in instructor_posts:
        attachments = post.get("attachments", [])
        saved_files = []

        for att in attachments:
            saved_path = download_attachment(att)
            saved_files.append({
                "filename": att["filename"],
                "savedPath": saved_path
            })

        collected.append({
            "title": post.get("title"),
            "body": post.get("body"),
            "tags": post.get("tags"),
            "createdAt": post.get("createdAt"),
            "updatedAt": post.get("updatedAt"),
            "attachments": saved_files
        })

    with open(os.path.join(OUTPUT_DIR, "collected.json"), "w") as f:
        json.dump(collected, f, indent=2)

    #Task 2: Reply to check-ins
    checkins = [p for p in instructor_posts if is_checkin_post(p)]

    for chk in checkins:
        if not has_already_replied(chk["id"]):
            reply_to_checkin(chk["id"])
            continue

if __name__ == "__main__":
    main()