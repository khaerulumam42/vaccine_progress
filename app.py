import os
from datetime import datetime, timedelta
import pandas as pd
import time
import tweepy
from apscheduler.schedulers.blocking import BlockingScheduler

API_KEY = os.getenv("API_KEY")
API_SECRET_KEY = os.getenv("API_SECRET_KEY")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN_SECRET")

auth = tweepy.OAuthHandler(API_KEY, API_SECRET_KEY)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

api = tweepy.API(auth)

country = "Indonesia"

sched = BlockingScheduler()

def progress_bar(count, total, country, shot="1st", prefix=""):
    percent = round((count/total), 4)
    length = 35
    progress = percent*length
    filled_bar = "█"*int(progress)
    unfilled_bar = "-"*int(length-int(progress))
    if shot == "1st":
        return f"1st shot \n|{filled_bar}{unfilled_bar}| {round((percent*100), 3)}%"
    else:
        return f"2nd shot \n|{filled_bar}{unfilled_bar}| {round((percent*100), 3)}%"

@sched.scheduled_job('interval', hour=1, minutes=0)
def main():
    fname = "vaccinations/vaccinations.csv"

    ts = os.path.getmtime(fname)

    if not datetime.fromtimestamp(ts).date() == datetime.today().date():
        print(f"data more than 1 day {datetime.fromtimestamp(ts)} {datetime.today().date()}")
        os.popen("sh update_data.sh")

    time.sleep(5)

    df = pd.read_csv(fname)

    country_data = df[df["location"] == country].sort_values("date").iloc[-1]

    last_update = country_data["date"]
    at_least_one_shot = country_data["people_vaccinated_per_hundred"]
    fully_vaccinated = country_data["people_fully_vaccinated_per_hundred"]

    data = {"1st": at_least_one_shot, "2nd": fully_vaccinated}
    tweet = f"{country}, {last_update}\n\n"

    for vaccine in data:
        text = progress_bar(data[vaccine], 100, country, vaccine) + "\n"
        tweet += text

    api.update_status(tweet)
    print(tweet)

sched.start()