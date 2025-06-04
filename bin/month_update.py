#!/usr/bin/env python 
from datetime import datetime, timedelta
import utils


def update_month_summaries():
    today = datetime.now().date()
    last_month = today - timedelta(weeks=4)
    period = f"{last_month.strftime('%Y-%m-%d')} y {today.strftime('%Y-%m-%d')}"
    app = utils.create_app_summary()
    summary = utils.generate_summary(app, period)
    with open("summaries/month_summary_esp.txt", "w") as file:
        file.write(summary)

    #Generate Catalan summaries
    config = {"configurable": {"thread_id": "5"}}
    for event in app.stream({"messages": [f"Tradueix el seguent text al Català: {summary}"]}, config, stream_mode="values"):
        summary = event["messages"][-1].content
    with open("summaries/month_summary_cat.txt", "w") as file:
        file.write(summary)

    #Generate English summaries
    for event in app.stream({"messages": [f"Translate the following text to English: {summary}"]}, config, stream_mode="values"):
        summary = event["messages"][-1].content
    with open("summaries/month_summary_en.txt", "w") as file:
        file.write(summary)


if __name__ == "__main__":
    update_month_summaries()