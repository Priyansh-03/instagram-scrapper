from flask import Flask, request, jsonify
import requests
import re

app = Flask(__name__)

def extract_username_from_url(insta_url: str) -> str:
    """
    Extracts the username from a full Instagram profile URL.
    Example: https://www.instagram.com/tulipgardenresort/ -> tulipgardenresort
    """
    match = re.search(r"instagram\.com/([^/?]+)", insta_url)
    return match.group(1) if match else insta_url

def scrape_instagram_profile(username):
    url = f"https://www.instagram.com/{username}/?__a=1&__d=dis"
    headers = {
        "User-Agent": "Mozilla/5.0",
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return {"error": f"Failed to fetch profile. Status code: {response.status_code}"}

        data = response.json()
        return clean_instagram_data(data)
    except Exception as e:
        return {"error": str(e)}

def clean_instagram_data(raw_data):
    user = raw_data.get("graphql", {}).get("user", {})
    return {
        "username": user.get("username"),
        "full_name": user.get("full_name"),
        "bio": user.get("biography"),
        "followers": user.get("edge_followed_by", {}).get("count"),
        "following": user.get("edge_follow", {}).get("count"),
        "total_posts": user.get("edge_owner_to_timeline_media", {}).get("count"),
        "profile_picture": user.get("profile_pic_url_hd"),
        "is_verified": user.get("is_verified"),
    }

@app.route("/")
def home():
    return jsonify({"status": "ok", "message": "Insta Scraper API is running 🚀"})

@app.route("/scrape", methods=["GET"])
def scrape():
    username_or_url = request.args.get("username")
    if not username_or_url:
        return jsonify({"error": "Missing 'username' parameter"}), 400

    username = extract_username_from_url(username_or_url)
    result = scrape_instagram_profile(username)
    return jsonify(result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
