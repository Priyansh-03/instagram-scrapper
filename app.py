from flask import Flask, request, jsonify
import requests
import json
import os

app = Flask(__name__)

# 🔁 Your existing functions: scrape_instagram_profile, clean_instagram_data go here...
def scrape_instagram_profile(username):
    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"

    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "x-ig-app-id": "936619743392459",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122 Safari/537.36",
        "referer": f"https://www.instagram.com/{username}/",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin"
    }

    response = requests.get(url, headers=headers)
    print(f"🔄 Status Code: {response.status_code}")

    if response.status_code != 200:
        print(f"❌ Error fetching data: {response.text}")
        return None

    try:
        user = response.json()["data"]["user"]
    except Exception as e:
        print("❌ Exception while parsing response:", e)
        return None

    profile_info = {
        "username": username,
        "biography": user.get("biography", ""),
        "link_in_bio": user.get("bio_links")[0]["url"] if user.get("bio_links") else "",
        "followers": user["edge_followed_by"]["count"],
        "following": user["edge_follow"]["count"],
        "num_posts": user["edge_owner_to_timeline_media"]["count"],
        "profile_pic_url": user.get("profile_pic_url_hd", ""),
        "is_verified": user.get("is_verified", False),
    }


    posts = []
    post_edges = user["edge_owner_to_timeline_media"]["edges"]
    for post_edge in post_edges:
        node = post_edge["node"]

        # Get caption if available
        caption = ""
        caption_edges = node.get("edge_media_to_caption", {}).get("edges", [])
        if caption_edges:
            caption = caption_edges[0]["node"]["text"]

        post_data = {
            "display_url": node.get("display_url"),
            "num_comments": node.get("edge_media_to_comment", {}).get("count", 0),
            "num_likes": node.get("edge_liked_by", {}).get("count", 0),
            "caption": caption,
            "is_video": node.get("is_video", False)
        }

        if post_data["is_video"]:
            post_data["video_url"] = node.get("video_url", "")
            post_data["video_view_count"] = node.get("video_view_count", 0)

        posts.append(post_data)

    return {
        "profile_info": profile_info,
        "recent_posts": posts
    }


def clean_instagram_data(data):
    profile = data["profile_info"]
    posts = data["recent_posts"]

    top_posts = []
    for post in posts:
        p = {
            "image": post.get("display_url"),
            "likes": post.get("num_likes"),
            "comments": post.get("num_comments"),
            "caption": post.get("caption", "")
        }
        if post.get("is_video"):
            p["video_url"] = post.get("video_url", "")
            p["views"] = post.get("video_view_count", 0)
        top_posts.append(p)

    return {
        "username": profile["username"],
        "bio": profile["biography"],
        "followers": profile["followers"],
        "following": profile["following"],
        "total_posts": profile["num_posts"],
        "profile_picture": profile["profile_pic_url"],
        "verified": profile["is_verified"],
        "top_posts": top_posts
    }


def save_to_json(data, filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as file:
            existing = json.load(file)
    else:
        existing = {}

    existing[data["username"]] = data

    with open(filename, "w", encoding="utf-8") as file:
        json.dump(existing, file, indent=2)
        print(f"✅ Saved/Updated data to {filename}")


@app.route("/scrape", methods=["POST"])
def insta_scrape_api():
    try:
        username = request.json.get("username")
        if not username:
            return jsonify({"error": "Username is required"}), 400

        result = scrape_instagram_profile(username)
        if not result:
            return jsonify({"error": "Failed to fetch data"}), 500

        cleaned = clean_instagram_data(result)
        return jsonify(cleaned), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(port=5005)
