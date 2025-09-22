import os
import requests
from bs4 import BeautifulSoup
from slack_sdk import WebClient
from dotenv import load_dotenv
from datetime import date

# Load environment variables from .env file
load_dotenv()


def get_menu():
    today = date.today().isoformat()
    mensa_id = 19  # ETH Zentrum - Polyterrasse
    url = f"https://ethz.ch/en/campus/food-and-shopping/gastronomy/menueplaene/offerDay.html?date={today}&id={mensa_id}"

    response = requests.get(url)
    if response.status_code != 200:
        return "Couldn't fetch the menu today. ☹️"

    soup = BeautifulSoup(response.text, "html.parser")
    menu_items = soup.select(".mensa-offer")

    if not menu_items:
        return "No meals available for today."

    result = f"*ETH Mensa Polyterrasse – {today}*\n"
    for item in menu_items:
        title = item.select_one(".mensa-meal-title")
        description = item.select_one(".mensa-meal-description")
        price = item.select_one(".mensa-meal-price")

        title_text = title.text.strip() if title else "No title"
        desc_text = description.text.strip() if description else ""
        price_text = price.text.strip() if price else "No price"

        result += f"- *{title_text}*: {desc_text} ({price_text})\n"

    return result.strip()


def post_to_slack(message):
    slack_token = os.getenv("SLACK_BOT_TOKEN")
    channel_id = os.getenv("SLACK_CHANNEL_ID")

    if not slack_token or not channel_id:
        raise EnvironmentError("Missing Slack credentials in .env file")

    client = WebClient(token=slack_token)
    client.chat_postMessage(channel=channel_id, text=message)


if __name__ == "__main__":
    menu = get_menu()
    print(menu)  # See output in terminal
    post_to_slack(menu)