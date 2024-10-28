import requests
import numpy as np
import json
import os
import pandas as pd

# TEMPERATURE API CALLS
API_LINK = 'https://api.mapmycrop.store/weather/past-data'
farm_id = 'e8826bbeac7448b4abbb6de9c5ab300c'
api_key = 'df85ac22fb354478b9c69ba005260fd7'

api_url = f"{API_LINK}?api_key={api_key}&farm_id={farm_id}"
response = requests.get(api_url)
data = response.json()

# Load crop dictionaries and data from CSV files
crop_dict_stages = pd.read_csv('crop_dict_stages.csv').set_index('crop_name').to_dict()['base_temperature']
crop_dict_GDD_only = pd.read_csv('crop_dict_GDD_only.csv').set_index('crop_name').to_dict()['base_temperature']
crop_data = pd.read_csv('crop_data.csv')

# Process the crop data as in your original code
crop = data['crop_name'].lower().strip()  # Normalize the crop name

# Initialize GDD and Cumulative GDD lists
data['GDD'] = []
data['Cumulative GDD'] = []

# Check which dictionary contains the crop and set the base temperature (j)
if crop in crop_dict_stages:
    j = crop_dict_stages[crop]
    stages_present = True
else:
    j = crop_dict_GDD_only.get(crop)
    stages_present = False

# Ensure j is defined and valid
if j is None:
    raise ValueError(f"Crop name '{crop}' not found in any database")

# Calculate GDD
base_temp = j

for max_temp, min_temp in zip(data['daily_temperature']['apparent_temperature_max'],
                              data['daily_temperature']['apparent_temperature_min']):
    if max_temp is not None and min_temp is not None:
        avg_temp = (max_temp + min_temp) / 2
        gdd = max(0, avg_temp - base_temp)  # Ensure GDD is not negative
    else:
        gdd = None  # Handle missing temperature data
    data['GDD'].append(gdd)

# Calculate Cumulative GDD using numpy's cumsum, ignoring None values
cumulative_gdd = np.nancumsum([gdd if gdd is not None else 0 for gdd in data['GDD']])
data['Cumulative GDD'] = cumulative_gdd.tolist()

# Output dictionary structure based on the crop type
if stages_present:
    data['Growth_stage'] = []  # Initialize Growth Stage
    data['info'] = []          # Initialize info

    for cum_gdd in data['Cumulative GDD']:
        # Find the growth stage based on Cumulative GDD
        stage_found = False
        for _, stage in crop_data.iterrows():
            if stage['crop_name'].lower() == crop and stage['min_GDD_C'] <= cum_gdd <= stage['max_GDD_C']:
                data['Growth_stage'].append(stage['growth_stage'])
                data['info'].append(stage.get('info', ''))  # Append the info for the growth stage
                stage_found = True
                break
        if not stage_found:
            data['Growth_stage'].append('Unknown stage')
            data['info'].append('')  # No info if no stage matches

else:
    # Remove Growth_stage and info if the crop only uses GDD data
    if 'Growth_stage' in data:
        del data['Growth_stage']
    if 'info' in data:
        del data['info']

# Create the final output dictionary
final_output = {
    "Date": data['daily_temperature']['time'],  # Assuming time is a list of dates
    "Cumulative GDD": data['Cumulative GDD'],
}
# Include 'Growth Stage' and 'info' if stages are present
if stages_present:
    final_output["Growth Stage"] = data['Growth_stage']
    final_output["Info"] = data['info']

# Define the JSON file path
json_file = "output.json"

# Try to load existing data or start with an empty list if the file is empty or invalid
if os.path.exists(json_file):
    try:
        with open(json_file, "r") as file:
            existing_data = json.load(file)
            if not isinstance(existing_data, list):  # Ensure it's a list
                existing_data = []
    except json.JSONDecodeError:
        print("Warning: data.json is empty or corrupted. Initializing with an empty list.")
        existing_data = []
else:
    existing_data = []

# Append the new final_output to the existing data
existing_data.append(final_output)

# Write the updated data back to 'data.json'
with open(json_file, "w") as file:
    json.dump(existing_data, file, indent=4)

# Print the final output dictionary for verification
print(final_output)
