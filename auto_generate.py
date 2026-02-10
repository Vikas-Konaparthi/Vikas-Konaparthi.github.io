import os
import requests
import json
import re
from datetime import datetime
from zoneinfo import ZoneInfo

# ------------------------
# Config
# ------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("GEMINI_API_KEY not found.")
    exit(1)

# IST Time
now = datetime.now(ZoneInfo("Asia/Kolkata"))
date_str = now.strftime("%Y-%m-%d")

# ------------------------
# Fetch Top Hacker News Stories
# ------------------------
def fetch_hn_top():
    try:
        ids = requests.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            timeout=10
        ).json()[:25]

        stories = []

        for story_id in ids:
            item = requests.get(
                f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json",
                timeout=10
            ).json()

            if item and "title" in item:
                stories.append({
                    "title": item["title"],
                    "score": item.get("score", 0),
                    "comments": item.get("descendants", 0)
                })

        return stories

    except Exception as e:
        print("Error fetching HN:", e)
        return []

stories = fetch_hn_top()

if not stories:
    print("No trending stories found.")
    exit(0)

# ------------------------
# Rank by Engagement
# ------------------------
stories.sort(key=lambda x: (x["score"] + x["comments"]), reverse=True)
top_candidates = stories[:5]

trend_context = "\n".join(
    [
        f"{s['title']} (score: {s['score']}, comments: {s['comments']})"
        for s in top_candidates
    ]
)

# ------------------------
# Gemini Editorial Prompt
# ------------------------
prompt = f"""
You are the editorial intelligence behind a serious global technical publication called Hilaight.

These are the most trending global technology stories right now:

{trend_context}

Your task:

1. Analyze which topic is the most globally impactful and technically important.
2. Choose ONE topic.
3. Write a deeply analytical, highly engaging, production-level technical article about it.

Rules:
- Title must be compelling and specific.
- Explain why this topic matters globally.
- Break down architecture or technical reasoning.
- Include system-level insights.
- Include code examples if relevant.
- Avoid hype, marketing tone, or fluff.
- 1000–1500 words.
- End with a strong thought-provoking question.

Return format EXACTLY as:

TITLE: <title here>

CONTENT:
<full article>
"""

url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

payload = {
    "contents": [
        {
            "parts": [
                {"text": prompt}
            ]
        }
    ],
    "generationConfig": {
        "temperature": 0.85,
        "topP": 0.95
    }
}

headers = {"Content-Type": "application/json"}

response = requests.post(url, headers=headers, data=json.dumps(payload))

if response.status_code != 200:
    print("Gemini API Error:", response.text)
    exit(1)

result = response.json()

try:
    raw_text = result["candidates"][0]["content"]["parts"][0]["text"]
except Exception as e:
    print("Unexpected Gemini response:", result)
    exit(1)

# ------------------------
# Extract Title & Content
# ------------------------
title_match = re.search(r"TITLE:\s*(.+)", raw_text)
content_match = re.search(r"CONTENT:\s*(.+)", raw_text, re.DOTALL)

if not title_match or not content_match:
    print("Could not parse Gemini response.")
    exit(1)

title = title_match.group(1).strip()
content = content_match.group(1).strip()

# ------------------------
# Generate SEO Slug
# ------------------------
slug = re.sub(r"[^a-zA-Z0-9\s-]", "", title)
slug = slug.lower().strip()
slug = re.sub(r"\s+", "-", slug)

filename = f"_posts/{date_str}-{slug}.md"

# ------------------------
# Write Markdown File
# ------------------------
markdown = f"""---
title: "{title}"
date: {now.strftime('%Y-%m-%d %H:%M:%S %z')}
categories: [engineering, system-design, tech-news]
tags: [trending, deep-dive]
---

{content}
"""

with open(filename, "w", encoding="utf-8") as f:
    f.write(markdown)

print("Generated:", filename)
