import os
import re
import requests
from datetime import date
from slack_sdk import WebClient
from dotenv import load_dotenv
from openai import OpenAI as OpenAIClient
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from bs4 import BeautifulSoup

# Load env vars
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SLACK_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL_ID")

client = OpenAIClient(api_key=OPENAI_API_KEY)


def fetch_eth_webpage_raw(target_date: str) -> str:
    today = date.today().isoformat()  # returns YYYY-MM-DD
    url = f"https://ethz.ch/de/campus/erleben/gastronomie-und-einkaufen/gastronomie/menueplaene/offerDay.html?date={target_date}&id=19#content"
    print(f"📥 Downloading raw ETH menu from: {url}")

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raises a proper error if 404
        return response.text
    except Exception as e:
        return f"Failed to fetch page: {e}"


def extract_visible_text(raw_html: str) -> str:
    soup = BeautifulSoup(raw_html, "html.parser")
    for script in soup(["script", "style"]):
        script.extract()  # Remove scripts and styles
    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(line for line in lines if line)
    return text

def fetch_eth_webpage_raw_selenium(date_str):
    today = date.today().isoformat()  # returns YYYY-MM-DD
    url = f"https://ethz.ch/de/campus/erleben/gastronomie-und-einkaufen/gastronomie/menueplaene/offerDay.html?date={today}&id=19#content"
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    time.sleep(3)  # Wait for JS to load
    html = driver.page_source
    driver.quit()
    return html


def translate_menu_with_gpt(visible_text: str) -> str:
    prompt = f"""You are a helpful assistant.

The following is the full visible **text content** of the ETH Zürich cafeteria page for today. 
Your job is to extract ONLY the relevant **menu items**, and translate them into a clean, friendly, readable English list for Slack.

Ignore opening hours, prices, promotions, allergens, and dates. Focus just on dishes and sides.

If no food items are found, say so politely.

--- PAGE TEXT START ---
{visible_text}
--- PAGE TEXT END ---
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("❌ GPT failed:", e)
        return "Menu translation failed today."


def post_to_slack(message: str):
    client = WebClient(token=SLACK_TOKEN)
    client.chat_postMessage(channel=SLACK_CHANNEL, text=message)
    print("✅ Menu posted to Slack.")


if __name__ == "__main__":
    today = date.today().isoformat()
    raw_html = fetch_eth_webpage_raw_selenium(today)
    # 💾 Save raw HTML for inspection (optional)
    with open("raw_menu_page.html", "w", encoding="utf-8") as f:
        f.write(raw_html)

    visible_text = extract_visible_text(raw_html)

    with open("raw_menu_text.txt", "w", encoding="utf-8") as f:
        f.write(visible_text)

    print("\n📄 Extracted visible text:\n")
    print(visible_text[:2000])  # preview
    print("\n--- END OF TEXT SNIPPET ---\n")

    translated_menu = translate_menu_with_gpt(visible_text)
    print("🔍 Translated menu:\n", translated_menu)
    post_to_slack(translated_menu)