import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import threading as th
from datetime import datetime
import time
import pandas as pd
from urllib.parse import urlparse
from pathlib import Path
import csv
import os
import tkinter

locations = []
locations_file = "kunnat"

settings_file = "settings"

# default location
location_name = "Helsinki"
latitude = "60.17"
longitude = "24.94"

temp_location = []

is_auto_refresh = 0

###############################################################################

def check_default_location(sf):
    settings_file = Path(sf)
    if settings_file.is_file():
        try:
            f = open(settings_file, "r")
        except OSError as err:
            print("Unable to open settings file. Default location (Helsinki) will be used.")
            print(err)
        with f:
            try:
                if (os.path.getsize(settings_file) > 0):
                    def_location = read_lf(f)
                    if (len(*def_location) == 3):
                        location_name = def_location[0][0]
                        latitude = def_location[0][1]
                        longitude = def_location[0][2]
                        fig.clear()
                        set_location(location_name, latitude, longitude)
                        canvas.draw()
                        print("Default location validated successfully (" + location_name + ").")
                    else:
                        print("Settings file is corrupt.")
                else:
                    print("Settings file is empty.")
            except ValueError as err:
                print("Invalid data in settings file, default location (Helsinki) will be used.")
                print(err)
            finally:
                f.close()

def set_default_location():
    if (len(temp_location) == 3):
        f = open(settings_file, "w")
        na, la, lo = temp_location[0], temp_location[1], temp_location[2]
        f.write(na + " " + la + " " + lo)
        f.close()
        tkinter.messagebox.showinfo( "Notification", "New default location set!")


def read_lf(f):
    data = list(csv.reader(f, delimiter=' '))
    return data

def validate_locations(locations):
    valid = True
    print(locations)
    for row in locations:
        if (len(row) != 3):
            valid = False
            # KESKEN
        print(row)
    return valid

def change_location(event):
    new_location = location_entry.get().capitalize()
    location_stringvar.set("")
    for row in locations:
        if (row[0] == new_location):
            location_name = row[0]
            latitude = row[1]
            longitude = row[2]
            print(row)
            global temp_location
            temp_location = row
            fig.clear()
            set_location(location_name, latitude, longitude)
            canvas.draw()

def set_location(location_name, latitude, longitude):
    data = pd.read_json("https://api.open-meteo.com/v1/forecast?latitude=" + latitude + "&longitude=" + longitude + "&hourly=cloudcover,cloudcover_low,cloudcover_mid,cloudcover_high")

    x = []
    y = []
    y_low = []
    y_mid = []
    y_high = []

    data2 = data.itertuples()

    for row in data2:
        if (row[0] == "time"):
            x = row[9]
        elif (row[0] == "cloudcover"):
            y = row[9]
        elif (row[0] == "cloudcover_low"):
            y_low = row[9]
        elif (row[0] == "cloudcover_mid"):
            y_mid = row[9]
        elif (row[0] == "cloudcover_high"):
            y_high = row[9]
        else:
            break
    
    plt.plot(x, y_low, label="Low")
    plt.plot(x, y_mid, label="Mid")
    plt.plot(x, y_high, label="High")
    plt.plot(x, y, label="Total")

    d = {'Datetime': x, 'Low': y_low, 'Mid': y_mid, 'High': y_high, 'Total': y}
    df = pd.DataFrame(d)
    #df.set_index('Datetime', inplace = True)

    #fig, ax = plt.subplots(num="Cloudiness", figsize=(16, 6), dpi=80, facecolor='w', edgecolor='k')
    #df.plot(x="Datetime", y="Low", ax=ax)
    #df.plot(x="Datetime", y="Mid", ax=ax)
    #df.plot(x="Datetime", y="High", ax=ax)
    #df.plot(x="Datetime", y="Total", ax=ax)

    plt.gcf().autofmt_xdate()
    
    frame1 = plt.gca()
    frame1.axes.get_xaxis().set_ticks([])

    plt.legend()

    plt.title("Cloudiness in " + location_name)

    #plt.gca().xaxis.grid(True, which='major')

def refresh():
    print("Updating forecast...")
    change_location(None)
    print("Done.")


def auto_refresh():
    global is_auto_refresh
    if (is_auto_refresh == 0):
        #ajastin käyntiin
        print("Auto refresh on.")
        is_auto_refresh = 1
        root.after(60*60000, timeout) # one hour

    else:
        #ajastin pois
        print("Auto refresh off.")
        is_auto_refresh = 0

def timeout():
    print("Timeout!")
    refresh()
    if (is_auto_refresh):
        root.after(60*60000, timeout) # one hour

def update_frequency(new_val):
    # retrieve frequency
    f = float(new_val)

    # required to update canvas and attached toolbar!
    canvas.draw()

###############################################################################

root = tkinter.Tk()
root.iconbitmap("cloudiness.ico")
root.wm_title("Cloudiness")

fig, ax = plt.subplots(num="Cloudiness", figsize=(16, 6), dpi=80, facecolor='w', edgecolor='k')

canvas = FigureCanvasTkAgg(fig, master=root)
canvas.draw()

bottom_canvas = tkinter.Canvas(master=root, width=200, height=120, bd=0, highlightthickness=0)

toolbar = NavigationToolbar2Tk(canvas, root, pack_toolbar=False)
toolbar.update()

canvas.mpl_connect(
    "key_press_event", lambda event: print(f"you pressed {event.key}"))
canvas.mpl_connect("key_press_event", key_press_handler)

location_stringvar = tkinter.StringVar()
checkbutton_auto_refresh = tkinter.Checkbutton(master=bottom_canvas, text="Auto refresh", variable=is_auto_refresh, onvalue=1, offvalue=0, command=auto_refresh)
button_set = tkinter.Button(master=bottom_canvas, text="Set default", command=set_default_location)
button_refresh = tkinter.Button(master=bottom_canvas, text="Refresh", command=refresh)
button_quit = tkinter.Button(master=bottom_canvas, text="Quit", command=root.destroy)
location_entry = tkinter.Entry(master=bottom_canvas, textvariable=location_stringvar)

location_entry.bind("<Return>", change_location)

locations_file = Path(locations_file)
if locations_file.is_file():
    try:
        f = open(locations_file, "r")
    except OSError as err:
        print("Unable to open locations file. Default location (Helsinki) will be used.")
        print(err)
    with f:
        try:
            if (os.path.getsize(locations_file) > 0):
                locations = read_lf(f)
                if (validate_locations(locations)):
                    print("Locations file validated successfully.")
                else:
                    print("Locations file is corrupt.")
            else:
                print("Locations file is empty.")
        except ValueError as err:
            print("Invalid data in locations file, locations not loaded. Default (Helsinki) will be used.")
            print(err)
        finally:
            f.close()

plt.xlabel("Datetime")
plt.ylabel("Cloudiness")

# Packing order is important. Widgets are processed sequentially and if there
# is no space left, because the window is too small, they are not displayed.
# The canvas is rather flexible in its size, so we pack it last which makes
# sure the UI controls are displayed as long as possible.
#button_quit.pack(side=tkinter.BOTTOM, pady=16)
#location_entry.pack(side=tkinter.BOTTOM, fill=tkinter.X)
#button_set.pack(side=tkinter.BOTTOM, pady=16)
#button_refresh.pack(side=tkinter.BOTTOM, pady=16)
#checkbutton_auto_refresh.pack(side=tkinter.BOTTOM, pady=16)
#toolbar.pack(side=tkinter.BOTTOM, fill=tkinter.X)
#canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=True)
canvas.get_tk_widget().grid(row=0, columnspan=3)
toolbar.grid(row=1, columnspan=3)

bottom_canvas.grid(row=2, columnspan=3)
checkbutton_auto_refresh.grid(row=2, column=0)
button_set.grid(row=2, column=1)
button_refresh.grid(row=2, column=2)
location_entry.grid(row=3, column=1, pady=16)
#button_quit.grid(row=4, column=1)

check_default_location(settings_file)

tkinter.mainloop()