# Commute Calendar Event Automation

This project automates the addition of commute events to your Google Calendar based on your scheduled events. It calculates travel time using the Google Maps API and adds a commute event if the travel time is within specified limits.

## Prerequisites

- Python 3.x
- Google Maps API Key with access to:
  - Directions API
  - Distance Matrix API
  - Geocoding API
- Google Calendar API enabled

## Setup

1. Clone the repository:
   ```bash
   git clone https://www.github.com/BEMZ01/travelCalc.git
    cd travelCalc
    ```
2. Create a virtual environment and activate it:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install the required packages:
   ```bash
    pip install -r requirements.txt
    ```
4. Create a new project in the Google Cloud Console and enable the Google Calendar API.
5. Create a new API key and restrict it to the following APIs:
   - Directions API
   - Distance Matrix API
   - Geocoding API
   - Google Calendar API
   - Places API
6. Create a new OAuth 2.0 client ID and download the credentials file.
7. Rename the credentials file to `credentials.json` and place it in the project directory.
8. Configure the .env file. You can use the provided .env.example file as a template.
9. Run the script:
   ```bash
   python main.py
   ```

## Licence

This project is licensed under the MIT Licence - see the LICENCE file for details.
