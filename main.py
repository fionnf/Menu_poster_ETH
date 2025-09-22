import os
import requests
from slack_sdk import WebClient
from dotenv import load_dotenv
import openai
from datetime import date
from bs4 import BeautifulSoup

# Load environment variables from .env file
load_dotenv()

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")


def fetch_eth_menu_html():
    """Fetch raw HTML from ETH menu page."""
    today = date.today().isoformat()
    mensa_id = 19  # ETH Zentrum - Polyterrasse
    url = f"https://ethz.ch/de/campus/erleben/gastronomie-und-einkaufen/gastronomie/menueplaene/offerDay.html?date={today}&id={mensa_id}"
    print(f"Fetching ETH menu from: {url}")

    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print("⚠️ Failed to fetch page:", response.status_code)
        return None

    return response.text


def extract_menu_with_gpt(page_html):
    """Send ETH HTML to GPT and extract the daily menu in English Slack-friendly format."""
    if not page_html:
        return "Couldn't fetch the menu today. ☹️"

    # Use only relevant content to avoid context overflow
    soup = BeautifulSoup(page_html, "html.parser")
    menu_div = soup.find("div", {"id": "eth_menu_day"}) or soup  # fallback to whole page
    menu_html = menu_div.get_text(separator="\n", strip=True)[:8000]  # max ~8k chars

    prompt = f"""
You're an ETH Zurich student reading the raw text of today's cafeteria menu.

Extract the key meals (title, description, price) from the following text and rewrite it in a friendly English style for a Slack message.

If the content is missing, say "No menu found today."

Here is the text:
{menu_html}
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print("❌ GPT failed:", e)
        return "Menu translation failed today."


def post_to_slack(message):
    """Post the message to Slack using environment credentials."""
    slack_token = os.getenv("SLACK_BOT_TOKEN")
    channel_id = os.getenv("SLACK_CHANNEL_ID")

    if not slack_token or not channel_id:
        raise EnvironmentError("Missing Slack credentials in .env file")

    client = WebClient(token=slack_token)
    try:
        client.chat_postMessage(channel=channel_id, text=message)
        print("✅ Menu posted to Slack.")
    except Exception as e:
        print("❌ Failed to post to Slack:", e)


if __name__ == "__main__":
    raw_html = fetch_eth_menu_html()
    translated_menu = extract_menu_with_gpt(raw_html)
    print("🔍 Translated menu:\n", translated_menu)
    post_to_slack(translated_menu)