"""
Written by BEMZlabs (github@bemz.info)

Copyright 2024 BEMZlabs

This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public 
Licence as published by the Free Software Foundation; either version 2 of the Licence, or (at your option) any later 
version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied 
warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public Licence for more details.

You should have received a copy of the GNU General Public Licence along with this program; if not, see 
<https://www.gnu.org/licenses/>.
"""

import googlemaps
import datetime
import os.path
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly", "https://www.googleapis.com/auth/calendar.events.owned",
          "https://www.googleapis.com/auth/calendar.events.readonly"]

MAPS = googlemaps.Client(key=os.getenv("GOOGLE_MAPS_API_KEY"))

def main():
  """Shows basic usage of the Google Calendar API.
  Prints the start and name of the next 10 events on the user's calendar.
  """
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  try:
    service = build("calendar", "v3", credentials=creds)

    # Call the Calendar API
    if os.getenv("CALENDARS_TO_LISTEN") is None or os.getenv("CALENDARS_TO_LISTEN") == "":
        print("You need to specify the calendars to listen to in the environment variable CALENDARS_TO_LISTEN.\nHere"
              "are a list of your calendars:")
        calendar_list = service.calendarList().list().execute()
        for calendar_list_entry in calendar_list["items"]:
            # print calendar id
            print(f"{calendar_list_entry['summary']}: {calendar_list_entry['id']}")

        return
    calendars = os.getenv("CALENDARS_TO_LISTEN").split(",")
    for calendar_id in calendars:
        print(f"Getting the upcoming events from {calendar_id}")
        last_location = None
        current_day = 0
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        # index through calendar events
        events_result = service.events().list(calendarId=calendar_id, timeMin=now,
                                              maxResults=10, singleEvents=True,
                                              orderBy="startTime").execute()
        events = events_result.get("items", [])
        if not events:
            print("No upcoming events found.")
        for event in events:
            # check if we are on a new day
            if event["start"].get("dateTime", event["start"].get("date"))[:10] != current_day:
                current_day = event["start"].get("dateTime", event["start"].get("date"))[:10]
                print(f"New day: {current_day}!")
                # reset last location unless there is an event that stretches over multiple days
                if last_location is not None:
                    last_location = None
            start = event["start"].get("dateTime", event["start"].get("date"))
            print(start, event["summary"])
            if "location" in event:
                print("Location: ", event["location"])
                geocode_result = MAPS.geocode(event["location"])
                if len(geocode_result) == 0:
                    print("Invalid location")
                else:
                    print("Valid location")
                    if os.getenv("CAR_EMOJI") is not None:
                        car_emoji = os.getenv("CAR_EMOJI")
                        print(f"Car emoji specified: {car_emoji}")
                        # get the previous event
                        prev_event = service.events().list(calendarId=calendar_id, timeMax=start,
                                                           maxResults=1, singleEvents=True,
                                                           orderBy="startTime").execute()
                        if len(prev_event["items"]) > 0:
                            prev_event = prev_event["items"][0]
                            if car_emoji in prev_event["summary"]:
                                print("Previous event has a car emoji. Not adding a commute event.")
                                continue
                        print("Previous event does not have a car emoji. Adding a commute event.")
                    # how long will it take to get to the location
                    if os.getenv("TIME_BUFFER") is not None:
                        time_buffer = int(os.getenv("TIME_BUFFER"))
                    else:
                        time_buffer = 0
                    # get start time of event, then subtract time buffer (minutes)
                    event_start = datetime.datetime.fromisoformat(start) - datetime.timedelta(minutes=time_buffer)
                    if last_location is None:
                        last_location = [os.getenv("HOME_LAT"), os.getenv("HOME_LNG")]
                    directions_result = MAPS.directions(last_location, event["location"],
                                                        mode=os.getenv("TRAVEL_MODE", "driving"),
                                                        arrival_time=event_start.timestamp())
                    total_time = 0
                    for leg in directions_result[0]["legs"]:
                        total_time += leg["duration"]["value"]
                    print(f"Total time to get to location: {total_time/60} minutes.")
                    if os.getenv("MIN_TRAVEL_TIME") is not None:
                        min_travel_time = int(os.getenv("MIN_TRAVEL_TIME"))
                        if total_time/60 < min_travel_time:
                            print(f"Total time to get to location is less than {min_travel_time} minutes. Not adding a calendar event.")
                            continue
                    if os.getenv("MAX_TRAVEL_TIME") is not None:
                        max_travel_time = int(os.getenv("MAX_TRAVEL_TIME"))
                        if total_time/60 > max_travel_time:
                            print(f"Total time to get to location is greater than {max_travel_time} minutes. Not adding a calendar event.")
                            continue
                    # get start time of travel
                    travel_start = event_start - datetime.timedelta(seconds=total_time)
                    # add calendar event
                    com_event = {
                        "summary": f"🚗 Commute to {event['summary']}",
                        "description": os.getenv("EVENT_DESCRIPTION", "Commute to event."),
                        "start": {
                            "dateTime": travel_start.isoformat(),
                            "timeZone": "America/New_York",
                        },
                        "end": {
                            "dateTime": event_start.isoformat(),
                            "timeZone": "America/New_York",
                        },
                        "reminders": {
                            # remind 15 minutes before
                            "useDefault": False,
                            "overrides": os.getenv("REMINDERS", [{"method": "popup", "minutes": 15}]),
                        },
                    }
                    service.events().insert(calendarId=calendar_id, body=com_event).execute()
                    print("Event added.")
                try:
                    last_location = event["location"]
                except KeyError:
                    print(f"No location for event. {event['summary']}")








  except HttpError as error:
    print(f"An error occurred: {error}")


if __name__ == "__main__":
  main()