import requests
import argparse
import re

# Set your qBittorrent Web UI URL and credentials
QB_URL = "http://127.0.0.1:10923"
QB_USERNAME = "username"
QB_PASSWORD = "password"

# Parse command line arguments
parser = argparse.ArgumentParser(description="This script looks for torrents with the noHL tag in qBittorent and checks if they match a regex pattern for either season packs or episodes. It then tags them with \"noHL seasons\" or \"noHL episodes\" respectively.")
parser.add_argument("--seasons", action="store_true", help="Search for season packs matching the regex pattern.")
parser.add_argument("--episodes", action="store_true", help="Search for episode packs matching the regex pattern.")
args = parser.parse_args()

def has_noHL_tag(tags: str) -> bool:
    return 'noHL' in tags.split(',')

def has_nohl_episodes_or_seasons(tags: str) -> bool:
    tags_list = tags.split(',')
    return 'noHL episodes' in tags_list or 'noHL seasons' in tags_list

# Set the regex pattern and the tag based on the command line arguments
if args.seasons:
    regex_pattern = r"(?i).*s(\d{1,2})\..*"
    tag = "noHL seasons"
elif args.episodes:
    regex_pattern = r"(?i).*s(\d{1,2}e(\d{1,2}))\..*"
    tag = "noHL episodes"
else:
    parser.print_help()
    exit()

# Authenticate with qBittorrent Web UI
session = requests.Session()
auth_response = session.post(
    f"{QB_URL}/api/v2/auth/login",
    data={"username": QB_USERNAME, "password": QB_PASSWORD},
)

print(f"Auth status code: {auth_response.status_code}")
print(f"Auth response text: {auth_response.text}")

# Get the list of torrents
response = session.get(f"{QB_URL}/api/v2/torrents/info", verify=False)

print(f"Torrents status code: {response.status_code}")
print(f"Torrents response text: {response.text}")

try:
    torrents = response.json()
except requests.exceptions.JSONDecodeError:
    print("Failed to decode JSON.")
    torrents = []

# Find torrent names matching the regex pattern and without both "noHL" and "noHL episodes" or "noHL seasons" tags
matching_torrent_names = [
    torrent["name"] for torrent in torrents if re.match(regex_pattern, torrent["name"]) and "noHL" in torrent["tags"] and ("tv" in torrent["category"] or "4ktv" in torrent["category"]) and not (has_noHL_tag(torrent["tags"]) and has_nohl_episodes_or_seasons(torrent["tags"]))
]

# Add the tag to the matching torrents
total_torrents = len(matching_torrent_names)
for index, name in enumerate(matching_torrent_names):
    # Find the corresponding torrent object
    torrent = next((t for t in torrents if t["name"] == name), None)
    if torrent is not None:
        tags = torrent["tags"]
        tags_list = tags.split(",")
        
        print(f"Processing torrent {index + 1}/{total_torrents}: {torrent['name']}")
        print(f"Current tags: {tags}")

        if tag not in tags:
            tags_list.append(tag)

        session.post(f"{QB_URL}/api/v2/torrents/addTags", data={"hashes": torrent["hash"], "tags": ",".join(tags_list)})
        print(f"Updated tags: {','.join(tags_list)}\n")

# Print the matching torrent names
print("Matching torrent names:")
for name in matching_torrent_names:
    print(name)