
from flask import Flask, request, render_template
import requests
import urllib.parse
import logging
import re
from configuration import OPENWEATHER_API_KEY, GOOGLEPLACES_API_KEY 

import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

import re

def extract_location(query):
    # remove leading/trailing spaces and convert all letters to lowercase
    query = query.lower().strip()
    
    # remove common phrases and words used in weather queries
    query = re.sub(
        r'\s*\b(what\'?s the weather in|what is|give me weather|what is the weather for|what is the weather in|give me the weather in|weather for|show me the weather in|weather in|get weather for|please show me the weather in|please show me weather in|weather|right now|now|please|hello|can you|currently|current|today|give|me|thank|thanks|look|good|bad|tell|like|report|the|on|in|at|forecast|around|this|moment|going|to|be|of|activities|outside|does|what|can|I|do|description|will|you|list)\b\s*', 
        '', 
        query, 
        flags=re.IGNORECASE)
    
    # remove punctuation
    query = re.sub(r'[^\w\s,]', '', query)

    # regex to match "City" or "City, State/Country"
    location_pattern = re.compile(r'([a-zA-Z\s]+),\s*([a-zA-Z\s]+)$', re.IGNORECASE)
    match = location_pattern.search(query)

    if match:
        # if a city and state were found, get and return them with proper capitalization
        city = match.group(1).strip().title()  
        state_or_country = match.group(2).strip().title()
        return [city, state_or_country]
    
    # if no comma is found, return the query as just a city with capitalization
    return [query.title()]

          
def extract_time_period(query):
    if 'tomorrow' in query.lower():
        return 'tomorrow'
    else:
        return 'today'
    

def get_weather_data(location, time_period):
  geocoding_url = f'http://api.openweathermap.org/geo/1.0/direct?q={location}&limit=1&appid={OPENWEATHER_API_KEY}'
  geo_response = requests.get(geocoding_url).json()
  if not geo_response:
      return None
  
  lat = geo_response[0]['lat']
  lon = geo_response[0]['lon']
  
  if time_period == 'today':
      weather_url = f'http://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude=minutely,hourly&appid={OPENWEATHER_API_KEY}'
  else:
      weather_url = f'http://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude=minutely&appid={OPENWEATHER_API_KEY}'          

  weather_response = requests.get(weather_url).json() 
  return weather_response




def get_activities_suggestions(location, activity_type):
    # get coords needed
    geocoding_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={location}&key={GOOGLEPLACES_API_KEY}"
    geo_response = requests.get(geocoding_url).json()

    logging.debug(f"Geocoding Response for {location}: {geo_response}")


    # see if api request was successful
    if not geo_response['results']:
        return ["No activities found"]

    # get the coords
    lat = geo_response['results'][0]['geometry']['location']['lat']
    lon = geo_response['results'][0]['geometry']['location']['lng']

# debugging
    print(f"Coordinates for {location}: Latitude: {lat}, Longitude: {lon}")


    places_url = (
        f"https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        f"?location={lat},{lon}"
        f"&radius=5000"
        f"&type={activity_type}"
        f"&key={GOOGLEPLACES_API_KEY}"
    )

    places_response = requests.get(places_url).json()
    logging.debug(f"Google Places API Response: {places_response}")
    print(f"Google Places API Response: {places_response}")

    activities =[place['name'] for place in places_response['results']]
    activities = list(set(activities))
    
    if not activities:
        error_message = "No activities found \n\n(Note: Weather may not allow activities or enter more specific location)"
        error_message = error_message.replace("\n", "<br>")
        return [error_message]
    return activities






def generate_response(weather_data, activities):
    # get the current weather details
    location_name = weather_data.get('name', 'location')
    weather_description = weather_data['weather'][0]['description']
    temperature = weather_data['main']['temp']
    humidity = weather_data['main']['humidity']

    response = (
         f"The current weather in {location_name} is {weather_description} "
        f"with a temperature of {temperature}°C and humidity of {humidity}%."
    )

    if activities: 
        response += f" You might enjoy visiting: {', '.join(activities)}."
        for activity in activities:
            response += f" {activity}\n"
    else:
        response += " I couldn't find any activities nearby."
    return response




@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == "POST":
        user_query = request.form.get("city")
        logging.debug(f"User Query: {user_query}")

        if user_query:
            locationResult = extract_location(user_query)
            city = None
            state_or_country = None
            location = None
            if len(locationResult) == 1:
                city = locationResult[0]
                location =  city
            else:
                city = locationResult[0]
                state_or_country = locationResult[1]
                location = f"{city.title()}, {state_or_country.title()}"
                logging.debug(f"State/Country: {state_or_country}")
                logging.debug(f"Location: {location}")

            
            if state_or_country != None:
                logging.debug(f"City: {city}")
            else: 
                logging.debug(f"State/Country: {state_or_country}")
        else:
            city = None

        if not city:
            return render_template("index.html", error="Please enter a valid city name or ask in a way that I can understand.")

        encoded_city =urllib.parse.quote(city)
        
        # api request 
        url = None
        if state_or_country != None:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city},{state_or_country}&appid={OPENWEATHER_API_KEY}&units=metric"
        else: 
             url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
        response = requests.get(url)
        data = response.json()

        logging.debug(f"OpenWeather API Response: {data}")
    
        # debugging
        print(data)
        if response.status_code != 200 or "main" not in data:
            error_message = data.get("message", "")
            if error_message == "city not found":
                error_message = "Please enter a valid city name or ask in a way that I can understand. <br><br>Note: try formatting your location as follows:<br><div style='text-align: left; padding-left: 47%; color: red'>&#10023; City, State<br>&#10023; City, Country<br>&#10023; City<br>&#10023; State<br>&#10023; Country</div>"
            else:
                return render_template("index.html", error=f"Error: {error_message}")
            return render_template("index.html", error=f"Error: {error_message}")
        else:
            #successful
            response = ""
        # getting weather data

        # degrees in C
        temp_celsius = round(float(data["main"]["temp"]))
        feels_like_celsius = round(float(data["main"]["feels_like"]))
        temp_min_celsius = round(float(data["main"]["temp_min"]))
         
        temp_max_celsius = round(float(data["main"]["temp_max"]))


        # degrees in F
        temp_fahrenheit = round(temp_celsius * 9 / 5 + 32)
        feels_like_fahrenheit = round(feels_like_celsius * 9 / 5 + 32)
        temp_min_fahrenheit = round(temp_min_celsius * 9 / 5 + 32)
        temp_max_fahrenheit = round(temp_max_celsius * 9 / 5 + 32)

       
        # other weather data
        humidity = data["main"]["humidity"]
        pressure = round(float(data["main"]["pressure"]))
        description = (data["weather"][0]["description"])
        wind_speed = round(float(data["wind"]["speed"]))
        wind_direction = round(float(data["wind"]["deg"]))
        visibility = round(float(data["visibility"]))
        city_name = (data["name"])


        # determine activity type based on weather conditions
        if "rain" in description or "storm" in description:
            activity_type = "museum"
        elif "snow" in description:
            activity_type = "ski_resort"
        elif "clear" in description or "sunny" in description:
            activity_type = "park"
        else:
            activity_type = "cafe" 

        # get activities suggestions
        activities = get_activities_suggestions(location, activity_type)

        totalResponse = generate_response(data, activities)

        # rendering the weather data
        return render_template(
            "index.html",
            city=city.title(),
            location = location,
            totalResponse=totalResponse,
            temp_celsius=temp_celsius,
            temp_fahrenheit=temp_fahrenheit,
            feels_like_celsius=feels_like_celsius,
            feels_like_fahrenheit=feels_like_fahrenheit,
            temp_min_celsius=temp_min_celsius,
            temp_max_celsius=temp_max_celsius,
            temp_min_fahrenheit=temp_min_fahrenheit,
            temp_max_fahrenheit=temp_max_fahrenheit,
            humidity=humidity,
            pressure=pressure,
            description=description,
            wind_speed=wind_speed,
            wind_direction=wind_direction,
            visibility=visibility,
             activities=activities,
             
        )
    return render_template("index.html")



# for about page
@app.route('/about/')
def about():    
    return render_template('about.html')


if __name__ == '__main__':
    app.run(debug=True)

