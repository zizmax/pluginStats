import requests
import json
import csv
from datetime import datetime
import os
import subprocess

print("Scraping...")

directory = "/home/pi/pluginStats/"

bstats_URL = "https://bstats.org/api/v1/plugins/7348/charts/"
spigot_URL = "https://api.spigotmc.org/simple/0.1/index.php?action=getResource&id=81899"

charts = ["servers", "players", "onlineMode", "minecraftVersion",
          "serverSoftware", "pluginVersion", "coreCount", "osArch", "location", "os",
           "javaVersion"]

results = {}
for chart in charts:
    if chart == "servers" or chart == "players":
        #maxElements=1 to get only the current count, not every historical value
        results[chart] = requests.get(bstats_URL + chart + "/data/?maxElements=1").json()
    else:
        results[chart] = requests.get(bstats_URL + chart + "/data").json()

fmt = '%Y-%m-%d %H:%M:%S'
release_date = datetime.strptime('2020-07-24 18:30:00', fmt)
time = datetime.now()
time_since = time - release_date
hours = time_since.total_seconds()/3600

if not os.path.isdir(directory):
    os.mkdir(directory)
    print("Created: " + directory)

def write_csv(filename, row_data):
    with open(filename + ".csv", 'a') as csv_file:
        csv_writer = csv.writer(csv_file)
        if "stats" in filename and os.stat(filename + ".csv").st_size == 0:
            csv_writer.writerow(["time", "servers", "players", "online", "downloads", "reviews", "rating", "updates"])
        csv_writer.writerow(row_data)

print("Writing")

for chart in charts[3:-2]:  # minecraftVersion through location
    row_data = [time]
    for element in results[chart]:
        row_data.append(element["name"])
        row_data.append(element["y"])
    write_csv(directory + chart, row_data)

for chart in charts[-2:]: #os and javaVersion
    row_data = [time]
    for parent in results[chart]["drilldownData"]:
        for element in parent["data"]:
            row_data.append(element[0])  # Name
            row_data.append(element[1])  # Count
    write_csv(directory + chart, row_data)

spigot_stats = ["downloads", "reviews", "rating", "updates"]
spigot_response = requests.get(spigot_URL).json()

row_data = [time]
row_data.append(results["servers"][0][1])
row_data.append(results["players"][0][1])
row_data.append(results["onlineMode"][1]["y"])
for stat in spigot_stats:
    row_data.append(spigot_response["stats"][stat])

print(row_data)

write_csv(directory + "stats", row_data)

print("Drawing...")

try:
    cpu = subprocess.check_output(["cat", "/proc/cpuinfo"], stderr=subprocess.STDOUT).decode("ascii")
    if "ARMv6" in cpu:
        on_pi = True
        print("on_pi = True")
    else:
        on_pi = False
except subprocess.CalledProcessError as e:
    on_pi = False
    print("on_pi = False")

print("Total downloads: " + str(spigot_response["stats"]["downloads"]))
print("Total Reviews: " + str(spigot_response["stats"]["reviews"]))
print("Rating: " + str(spigot_response["stats"]["rating"]))
print("Updates: " + str(spigot_response["stats"]["updates"]))
print("Updates per week: " + str(int(spigot_response["stats"]["updates"]) / (hours / 168)))
print("Updating today would be: " + str((int(spigot_response["stats"]["updates"]) + 1) / (hours / 168)))
print("Current Servers: " + str(results["servers"][0][1]))
print("Current Players: " + str(results["players"][0][1]))
print("Downloads per day: " + "{:.2f}".format(int(spigot_response["stats"]["downloads"]) / (hours/24)))

if on_pi:
    corner_x = 10
    corner_y = 8
    vertical_spacing = 13
    from inky import InkyPHAT
    from PIL import Image, ImageFont, ImageDraw
    from font_fredoka_one import FredokaOne
    inky_display = InkyPHAT("red")
    font = ImageFont.truetype(FredokaOne, 13)
    img = Image.new("P", (inky_display.WIDTH, inky_display.HEIGHT))
    draw = ImageDraw.Draw(img)
    draw.text((corner_x, corner_y), "Total Downloads: " + str(spigot_response["stats"]["downloads"]), inky_display.BLACK, font)
    draw.text((corner_x, corner_y + vertical_spacing*1), "Total Reviews: " + str(spigot_response["stats"]["reviews"]), inky_display.BLACK, font)
    draw.text((corner_x, corner_y + vertical_spacing*2), "Rating: " + str(spigot_response["stats"]["rating"]), inky_display.BLACK, font)
    draw.text((corner_x, corner_y + vertical_spacing*3), "Current Servers: " + str(results["servers"][0][1]), inky_display.BLACK, font)
    draw.text((corner_x, corner_y + vertical_spacing*4), "Current Players: " + str(results["players"][0][1]), inky_display.BLACK, font)
    draw.text((corner_x, corner_y + vertical_spacing*5), "Downloads per day: " + "{:.2f}".format(int(spigot_response["stats"]["downloads"]) / (hours/24)), inky_display.BLACK, font)
    draw.text((corner_x, corner_y + vertical_spacing*6), "Updates per week: " + "{:.2f}".format(int(spigot_response["stats"]["updates"]) / (hours / 168)), inky_display.BLACK, font)

    inky_display.set_image(img)
    inky_display.show()
