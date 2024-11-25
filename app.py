
from flask import Flask, request, render_template
import requests
from configuration import OPENWEATHER_API_KEY, GOOGLEPLACES_API_KEY 


app = Flask(__name__)
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        city = request.form.get('city')
        if not city:
            return render_template('index.html', error = 'Please enter a city name')
        
        # api request url
        url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}'
        response = requests.get(url)
        data = response.json()


        # getting weather data
        temp = data['main']['temp']
        description = data['weather'][0]['description']
        humidity = data['main']['humidity']

        # return a response with weather data
        return render_template('index.html', temp=temp, city=city,  description=description, humidity=humidity)
   
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)


# extract the location and time from the user query
def process_query(user_query):
    location = extract_location(user_query)
    time_period = extract_time_period(user_query)

    if not location:
        return "I'm sorry, I couldn't find a location in your query. Please try again."
    

    # get the weather data
    weather_data = get_weather_data(location, time_period)
    if not weather_data:
        return "I'm sorry, I couldn't find the weather data for that location. Please try again."
    
    # get activities suggestions
    activities = get_activities(location, weather_data)

    response = generate_response(weather_data, activities)
    return response



def extract_location(query):
   words = query.split()
   prepositions = ['in', 'at', 'on', 'near', 'around', 'by','for']
   for i, word in enumerate(words):
       if word.lower() in prepositions and i + 1 < len(words):
               return words[i + 1]
       return None

          
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


def get_activities_suggestions(location, weather_data):
   # first determine the weather condition  
    weather_condition = weather_data['current']['weather'][0]['main'].lower()

    # set activities based on the weather conditions
    if 'rain' in weather_condition:
        activities_type = 'museum'
    else:
        activities_type = 'park'

    # using google places API to get the activities suggestions
    geolocation_url = f'https://maps.googleapis.com/maps/api/geocode/json?address={location}&key={GOOGLEPLACES_API_KEY}'
    geolocation_response = requests.get(geolocation_url).json()
    if not geolocation_response['results']:
        return []
    
    lat = geolocation_response['results'][0]['geometry']['location']['lat']
    lon = geolocation_response['results'][0]['geometry']['location']['lng']

    places_url = (
        'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
        f'?location={lat},{lon}'
        f'&radius=5000'
        f'&type={activity_type}'
        f'&key={GOOGLEPLACES_API_KEY}'

    )

    places_response = requests.get(places_url).json()
    activities = []
    for place in places_response['results']:
        activities.append(place['name'])
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