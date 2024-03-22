# pip install meteostat
from datetime import datetime
import pandas as pd
from geopy import Nominatim   #not required if lat long is picked from the dashboard
import meteostat
from meteostat import Point, Daily
import json

# Open the text file
with open('C:\\Users\\Admin\\PycharmProjects\\Growing Degree Days 13 crops\\growth stage for 13 crops_json.txt', 'r') as f:
    # Read the contents of the file
    data = f.read()

# Replace single quotes with double quotes
data = data.replace("'", "\"")

# Attempt to load data into a JSON object
try:
    json_data = json.loads(data)
    # print(json_data)
except json.JSONDecodeError as e:
    print("Error decoding JSON:", e)


crop = str(input('insert crop name:'))  # input by user
start = input('enter date: ')  # input by user
address = input('insert crop location:')  #Please Remove this line if lat long is taken from the dashboard

# from geopy import Nominatim
geolocator = Nominatim(user_agent="Your_Name")  #Please Remove this line if lat long is taken from the dashboard
location = geolocator.geocode(address)    #Please Remove this line if lat long is taken from the dashboard
loc_variable = Point(location.latitude, location.longitude)   #Please Remove this line if lat long is taken from the dashboard

# loc_variable = Point(latitude, longitude) #input latitude and longitude value here from teh dashboard

end = datetime.today()
data = Daily(loc_variable, start, end)
data = data.fetch()
n = len(data)

# List of base temperature for the crops
crop_dict = {
    'barley': 0,
    'wheat (hard red)': 0,
    'oat': 4.5,  #4.444
    'canary seed': 7,
    'flax': 5,
    'canola (B. napus)': 5,
    'canola (B. rapa)': 5,
    'mustard (B. juncea)': 5,
    'mustard (S. alba)': 5,
    'chick pea desi': 5,
    'lentil': 5,
    'pea': 5,     #green pea
    'sunflower': 6.7,
}

output_data = {}  # Dictionary to store output data

if crop in crop_dict:
    tbase = crop_dict[crop]
    print(f"The value of j for {crop} is {tbase}")
    output_data['crop'] = crop
else:
    print('Enter valid sowing date')

GDU = data.tavg.sum() - n * tbase  # Growing Degree Units

output_data['GDU'] = GDU

for entry in json_data:
    if entry['crop_name'] == crop and entry['min_GDD_C'] < GDU < entry['max_GDD_C']:
        output_data['growth_stage'] = entry['growth_stage']
        output_data['BBCH'] = entry['BBCH']
        break
else:
    output_data['growth_stage'] = 'Not found'
    output_data['BBCH'] = 'Not found'

# Write output data to a JSON file
output_file = 'output.json'
with open(output_file, 'w') as f:
    json.dump(output_data, f, indent=4)

print("Output data written to:", output_file)
