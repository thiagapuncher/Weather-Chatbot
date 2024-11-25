
from flask import Flask, request, render_template
import requests
from configuration import OPENWEATHER_API_KEY, GOOGLEPLACES_API_KEY 


app = Flask(__name__)
@app.route('/', methods=['GET', 'POST'])


def index():
    if request.method == "POST":
        city = request.form.get("city")
        if not city:
            return render_template("index.html", error="Please enter a city name.")
        
        # api request 
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
        response = requests.get(url)
        data = response.json()

    
        # debugging
        print(data)
        if response.status_code != 200 or "main" not in data:
            error_message = data.get("message", "Unable to fetch weather data.")
            return render_template("index.html", error=f"Error: {error_message}")

        # getting weather data

        # degrees in C
        temp_celsius = data["main"]["temp"]
        feels_like_celsius = data["main"]["feels_like"]
        temp_min_celsius = data["main"]["temp_min"]
        temp_max_celsius = data["main"]["temp_max"]


        # degrees in F
        temp_fahrenheit = temp_celsius * 9 / 5 + 32
        feels_like_fahrenheit = feels_like_celsius * 9 / 5 + 32
        temp_min_fahrenheit = temp_min_celsius * 9 / 5 + 32
        temp_max_fahrenheit = temp_max_celsius * 9 / 5 + 32

       
        # other weather data
        humidity = data["main"]["humidity"]
        pressure = data["main"]["pressure"]
        description = data["weather"][0]["description"]
        wind_speed = data["wind"]["speed"]
        wind_direction = data["wind"]["deg"]
        visibility = data["visibility"]
        city_name = data["name"]


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
        activities = get_activities_suggestions(city, activity_type)




        # rendering the weather data
        return render_template(
            "index.html",
            city=city_name,
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


def get_activities_suggestions(city, activity_type):
    # get coords needed
    geocoding_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={city}&key={GOOGLEPLACES_API_KEY}"
    geo_response = requests.get(geocoding_url).json()

    # see if api request was successful
    if not geo_response['results']:
        return ["No activities found"]

    # get the coords
    lat = geo_response['results'][0]['geometry']['location']['lat']
    lon = geo_response['results'][0]['geometry']['location']['lng']

# debugging
    print(f"Coordinates for {city}: Latitude: {lat}, Longitude: {lon}")


    places_url = (
        f"https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        f"?location={lat},{lon}"
        f"&radius=5000"
        f"&type={activity_type}"
        f"&key={GOOGLEPLACES_API_KEY}"
    )

    places_response = requests.get(places_url).json()
    print(f"Google Places API Response: {places_response}")

    activities = []
    for place in places_response.get("results", []):
        activities.append(place["name"])
    
    if not activities:
        return ["No activities found"]
    return activities




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