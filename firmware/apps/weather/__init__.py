# This example grabs current weather details from Open Meteo and displays them on Badger 2350.
# Find out more about the Open Meteo API at https://open-meteo.com

import os
import secrets
import sys

import urequests
import wifi

secrets.require("LAT", "LON")

sys.path.insert(0, "/system/apps/weather")
os.chdir("/system/apps/weather")

import ui

# Set your latitude/longitude here (find yours by right clicking in Google Maps!)
LAT = secrets.LAT
LNG = secrets.LON

URL = "http://api.open-meteo.com/v1/forecast?latitude=" + str(LAT) + "&longitude=" + str(LNG) + "&current_weather=true&timezone=" + "auto"


ICONS = {
    "cloud": image.load("assets/cloud.png"),
    "rainy": image.load("assets/rainy.png"),
    "weather_snowy": image.load("assets/snowy.png"),
    "thunderstorm": image.load("assets/thunderstorm.png"),
    "sunny": image.load("assets/sunny.png")
}


def get_data():
    try:
        global weathercode, temperature, windspeed, winddirection, date, time, winddirection_degrees
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
        winddirection_degrees = current["winddirection"]
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


def draw():

    # Clear the display
    screen.pen = brush.pattern(color.white, color.dark_grey, 12)
    screen.clear()

    ui.draw_header("Weather", rect(-1, -1, screen.width, 16))

    # info boxes
    temp_win = rect(88, 20, 170, 70)
    ui.draw_window(temp_win)
    ui.draw_header("Temperature", temp_win)

    wind_win = rect(5, 97, 170, 30)
    ui.draw_window(wind_win)

    status = rect(5, 137, 170, 30)
    ui.draw_window(status)

    wind_dir = rect(188, 97, 70, 70)
    ui.draw_window(wind_dir)

    # draw the icon window
    icon_win = rect(5, 20, 70, 70)
    ui.draw_window(icon_win)

    if temperature is not None:
        # Choose an appropriate icon based on the weather code
        # Weather codes from https://open-meteo.com/en/docs
        if weathercode in [71, 73, 75, 77, 85, 86]:  # codes for snow
            screen.blit(ICONS["weather_snowy"], vec2(5, 20))
        elif weathercode in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82]:  # codes for rain
            screen.blit(ICONS["rainy"], vec2(5, 20))
        elif weathercode in [1, 2, 3, 45, 48]:  # codes for cloud
            screen.blit(ICONS["cloud"], vec2(5, 20))
        elif weathercode in [0]:  # codes for sun
            screen.blit(ICONS["sunny"], vec2(5, 20))
        elif weathercode in [95, 96, 99]:  # codes for storm
            screen.blit(ICONS["thunderstorm"], vec2(5, 20))

        # draw the temperature text in the centre of the rect
        screen.pen = color.black
        screen.font = rom_font.nope
        temp_text = f"{temperature}°C"
        tw, _ = screen.measure_text(temp_text)
        tx = temp_win.x + (temp_win.w // 2) - (tw // 2)
        screen.text(temp_text, tx, temp_win.y + temp_win.h - 20)
        outer = ui.thermometer()

        # draw the horizontal thermometer and fill based on temperature
        fill = (temperature - 0) / (40 - 0)
        inner = ui.thermometer(thickness=0.8, fill=fill)
        outer.transform = (mat3()
                           .translate(temp_win.x + 37, temp_win.y + 37)
                           .rotate(90)
                           .scale(15))
        inner.transform = (mat3()
                           .translate(temp_win.x + 37, temp_win.y + 37)
                           .rotate(90)
                           .scale(15))
        screen.pen = color.black
        screen.shape(outer)
        screen.pen = brush.pattern(color.white, color.dark_grey, 3)
        screen.shape(inner)

        # Draw the wind speed and direction arrow
        screen.pen = color.black
        screen.text(f"Wind Speed: {windspeed}kmph", wind_win.x + 5, wind_win.y + 8)
        tw, _ = screen.measure_text(winddirection)
        x = wind_dir.x + (wind_dir.w // 2) - (tw // 2)
        screen.text(f"{winddirection}", x, (wind_dir.y + wind_dir.h) - 18)

        ax = wind_dir.x + (wind_dir.w // 2)
        ay = wind_dir.y + (wind_dir.h // 2) - 3
        arrow = ui.custom_arrow(sweep=30)
        arrow.transform = (mat3()
                           .translate(ax, ay)
                           .rotate(winddirection_degrees)
                           .scale(30)
                           .translate(0, 0.2))

        screen.shape(arrow)

        screen.text(f"Last Updated: {time}", status.x + 5, status.y + 8)

    else:
        screen.pen = color.black
        ui.draw_alert("Error getting weather data")


def update():

    ui.draw_alert("Connecting to WiFi Network...")
    wifi.connect()

    # wait here until the wifi has connected
    while not wifi.tick():
        pass

    ui.draw_alert("Getting weather data...")
    get_data()
    draw()

    # wake up again in 30 minutes to refresh the data
    rtc.set_alarm(minutes=30)


def on_exit():
    rtc.clear_alarm()


run(update)
