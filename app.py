import os
from datetime import datetime, timedelta, date
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
max_char = 280

sched = BlockingScheduler()

def progress_bar(vaccine, total, country, shot="1st", prefix=""):
    count = vaccine["percent"]
    count_number = vaccine["count_number"]
    
    percent = round((count/total), 4)
    length = 30
    progress = percent*length
    filled_bar = "█"*int(progress)
    unfilled_bar = "-"*int(length-int(progress))
    if shot == "1st":
        return f"1st shot - {count_number}\n|{filled_bar}{unfilled_bar}| {round((percent*100), 3)}%"
    else:
        return f"2nd shot - {count_number}\n|{filled_bar}{unfilled_bar}| {round((percent*100), 3)}%"

@sched.scheduled_job("cron", hour=9, minute=0)
def top_country(top=10) -> None:
    last_days = 3
    anchor_date = date.today() - timedelta(days=last_days)
    anchor_date_str = anchor_date.strftime("%Y-%m-%d")

    fname = "https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/vaccinations/vaccinations.csv"
    df = pd.read_csv(fname)
    df["date"] = pd.to_datetime(df["date"])
    filter_date = df.query(f"date >= '{anchor_date_str}'")
    
    if len(filter_date) == 0:
        print(anchor_date_str)
        return None
    else:
        tweet = f"top {top} country, {anchor_date_str}. last {last_days} days\n\n"
        filter_date = filter_date.sort_values("people_fully_vaccinated_per_hundred", ascending=False).drop_duplicates(["location"]).reset_index()
        for index, row in filter_date[:top].iterrows():
            loc = row["location"]
            percent = row["people_fully_vaccinated_per_hundred"]
            pos = index+1
            text = f"{pos}. {loc} {percent}%\n"
            tweet += text

        api.update_status(tweet)
        print(tweet)
        print(len(tweet))
    
@sched.scheduled_job("cron", hour=2, minute=30)
def main():
    
    fname = "https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/vaccinations/vaccinations.csv"

    df = pd.read_csv(fname)

    country_data = df[df["location"] == country].sort_values("date").iloc[-1]

    last_update = country_data["date"]
    at_least_one_shot = country_data["people_vaccinated_per_hundred"]
    fully_vaccinated = country_data["people_fully_vaccinated_per_hundred"]
    daily_vaccinations = "{:,}".format(country_data["daily_vaccinations"])
    daily_vaccinations = daily_vaccinations.replace(",", ".")

    people_vaccinated = "{:,}".format(country_data["people_vaccinated"])
    people_vaccinated = people_vaccinated.replace(",", ".")

    people_fully_vaccinated = "{:,}".format(country_data["people_fully_vaccinated"])
    people_fully_vaccinated = people_fully_vaccinated.replace(",", ".")

    data = {"1st": {"percent": at_least_one_shot, "count_number": people_vaccinated}, \
        "2nd": {"percent": fully_vaccinated, "count_number": people_vaccinated}
        }

    tweet = f"{country}, {last_update} +{daily_vaccinations}\n\n"

    for vaccine in data:
        text = progress_bar(data[vaccine], 100, country, vaccine) + "\n"
        tweet += text

    api.update_status(tweet)
    print(tweet)

sched.start()