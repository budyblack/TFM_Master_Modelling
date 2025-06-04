#!/usr/bin/env python 
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import requests
import utils


def update_week_summaries():
    today = datetime.now().date()
    last_week = today - timedelta(weeks=1)
    period = f"{last_week.strftime('%Y-%m-%d')} y {today.strftime('%Y-%m-%d')}"
    app = utils.create_app_summary()
    summary = utils.generate_summary(app, period)
    with open("summaries/week_summary_esp.txt", "w") as file:
        file.write(summary)
    
    #Generate Catalan summaries
    config = {"configurable": {"thread_id": "5"}}
    for event in app.stream({"messages": [f"Tradueix el seguent text al Català: {summary}"]}, config, stream_mode="values"):
        summary = event["messages"][-1].content
    with open("summaries/week_summary_cat.txt", "w") as file:
        file.write(summary)

    #Generate English summaries
    for event in app.stream({"messages": [f"Translate the following text to English: {summary}"]}, config, stream_mode="values"):
        summary = event["messages"][-1].content
    with open("summaries/week_summary_en.txt", "w") as file:
        file.write(summary)


def post_to_discourse():
    load_dotenv()
    DISCOURSE_URL = "https://talkai.iiia.es/"
    API_KEY = os.getenv("DISCOURSE_API_KEY")
    API_USERNAME = os.getenv("DISCOURSE_API_USERNAME")

    if not API_KEY or not API_USERNAME:
        raise ValueError("Missing API_KEY or API_USERNAME in the environment variables.")

    today = datetime.today().date()
    last_week = today - timedelta(weeks=1)
    study_date = f"{last_week.strftime('%Y-%m-%d')} - {today.strftime('%Y-%m-%d')}"
    with open("summaries/week_summary_esp.txt", "r") as file:
        content = file.read()

    post_data = {
        "title": f"Resumen Semanal de Observaciones Relevantes ({study_date})",
        "raw": content,
        "category": 4  # Adjust to the desired category ID
    }

    headers = {
        "Api-Key": API_KEY,
        "Api-Username": API_USERNAME,
        "Content-Type": "application/json"
    }

    response = requests.post(
        f"{DISCOURSE_URL}/posts.json",
        json=post_data,
        headers=headers
    )

    if response.status_code == 200:
        print("Post created successfully!")
    else:
        print("Failed to create post:", response.json())


if __name__ == "__main__":
    update_week_summaries()