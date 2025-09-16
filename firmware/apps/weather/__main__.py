# This example grabs current weather details from Open Meteo and displays them on Badger 2350.
# Find out more about the Open Meteo API at https://open-meteo.com

import ezwifi
import urequests
from picovector import ANTIALIAS_BEST, HALIGN_CENTER, PicoVector, Polygon, Transform

import badger2350
from badger2350 import HEIGHT, WIDTH

# Set your latitude/longitude here (find yours by right clicking in Google Maps!)
LAT = 53.38609085276884
LNG = -1.4239983439328177
TIMEZONE = "auto"  # determines time zone from lat/long

URL = "http://api.open-meteo.com/v1/forecast?latitude=" + str(LAT) + "&longitude=" + str(LNG) + "&current_weather=true&timezone=" + TIMEZONE

CENTRE_X = WIDTH // 2
CENTRE_Y = HEIGHT // 2

ICONS = {
    "cloud": "\ue2bd",
    "rainy": "\uf176",
    "weather_snowy": "\ue2cd",
    "thunderstorm": "\uebdb",
    "sunny": "\ue81a"
}

# Display Setup
display = badger2350.Badger2350()
# display.led(128)
display.set_update_speed(2)

# Pico Vector
vector = PicoVector(display.display)
vector.set_antialiasing(ANTIALIAS_BEST)
t = Transform()
vector.set_font("Roboto-Medium-With-Material-Symbols.af", 35)
vector.set_font_align(HALIGN_CENTER)
vector.set_transform(t)

TITLE_BAR = Polygon()
TITLE_BAR.rectangle(2, 2, 260, 16, (8, 8, 8, 8))
TITLE_BAR.circle(253, 10, 4)

INFO_BOX = Polygon()
INFO_BOX.rectangle(2, 92, 260, 80, (8, 8, 8, 8))

try:
    # Connects to the wireless network. Ensure you have entered your details in WIFI_CONFIG.py :).
    ezwifi.connect(verbose=True, retries=3)
except ValueError:
    pass


def get_data():
    try:
        global weathercode, temperature, windspeed, winddirection, date, time
        print(f"Requesting URL: {URL}")
        r = urequests.get(URL)
        # open the json data
        j = r.json()
        print("Data obtained!")
        print(j)

        # parse relevant data from JSON
        current = j["current_weather"]
        temperature = current["temperature"]
        windspeed = current["windspeed"]
        winddirection = calculate_bearing(current["winddirection"])
        weathercode = current["weathercode"]
        date, time = current["time"].split("T")

        r.close()
    except OSError:
        temperature = None


def calculate_bearing(d):
    # calculates a compass direction from the wind direction in degrees
    dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    ix = round(d / (360. / len(dirs)))
    return dirs[ix % len(dirs)]


def draw_page():
    # Clear the display
    display.set_pen(3)
    display.clear()
    display.set_pen(0)

    # Draw the page header
    display.set_pen(0)
    vector.draw(TITLE_BAR)
    display.set_pen(3)
    display.text("badgerOS", 7, 6, WIDTH, 1)
    display.text("Weather", WIDTH - 60, 6, WIDTH, 1)
    display.set_pen(2)

    display.set_font("bitmap8")

    vector.draw(INFO_BOX)

    display.set_pen(1)
    if temperature is not None:
        icon_y = 55
        # Choose an appropriate icon based on the weather code
        # Weather codes from https://open-meteo.com/en/docs
        # Weather icons from https://fontawesome.com/
        if weathercode in [71, 73, 75, 77, 85, 86]:  # codes for snow
            vector.text(ICONS["weather_snowy"], CENTRE_X, icon_y)
        elif weathercode in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82]:  # codes for rain
            vector.text(ICONS["rainy"], CENTRE_X, icon_y)
        elif weathercode in [1, 2, 3, 45, 48]:  # codes for cloud
            vector.text(ICONS["cloud"], CENTRE_X, icon_y)
        elif weathercode in [0]:  # codes for sun
            vector.text(ICONS["sunny"], CENTRE_X, icon_y)
        elif weathercode in [95, 96, 99]:  # codes for storm
            vector.text(ICONS["thunderstorm"], CENTRE_X, icon_y)

        display.set_pen(0)
        display.text(f"Temperature: {temperature}°C", 8, 98, WIDTH, 2)
        display.text(f"Wind Speed: {windspeed}kmph", 8, 118, WIDTH, 2)
        display.text(f"Wind Direction: {winddirection}", 8, 138, WIDTH, 2)
        display.text(f"Last update: {date}, {time}", 8, 158, WIDTH, 1)

    else:
        display.set_pen(1)
        display.text("Unable to display weather! Check your network settings in secrets.py", 5, 107, WIDTH - 10, 2)

    display.update()


get_data()
draw_page()

# Call halt in a loop, on battery this switches off power.
# On USB, the app will exit when A+C is pressed because the launcher picks that up.
while True:
    # display.keepalive()  # TODO: No longer a problem because "halt" puts the board into powman sleep()
    display.halt()
