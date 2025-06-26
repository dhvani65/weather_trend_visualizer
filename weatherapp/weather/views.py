import pdb

import requests
import pandas as pd
import matplotlib
from django.conf import settings
import matplotlib.pyplot as plt
from django.contrib import messages
from django.shortcuts import render, redirect
from .forms import LocationForm
import os

matplotlib.use('Agg')  # Use non-GUI backend for image generation

GEO_API_KEY = '6d809f54ba214dff9c2ab5b9b699facc'
GEO_API_URL = 'https://api.opencagedata.com/geocode/v1/json'
WEATHER_API_URL = 'https://archive-api.open-meteo.com/v1/archive'


def dashboard(request):
    form = LocationForm()
    return render(request, 'weather/dashboard.html', {'form': form})


def get_coordinates(state, country):

    response = requests.get(GEO_API_URL, params={
        "q": f"{state}, {country}",
        "key": GEO_API_KEY
    })
    data = response.json()
    coords = data['results'][0]['geometry']

    return coords['lat'], coords['lng']


def get_weather_data(lat, lon, year):
    start = f"{year}-01-01"
    end = f"{year}-12-31"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start,
        "end_date": end,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "auto"
    }
    response = requests.get(WEATHER_API_URL, params=params)
    return response.json()


def result(request):
    if request.method == 'POST':
        form = LocationForm(request.POST)
        if form.is_valid():
            state = form.cleaned_data['state']
            country = form.cleaned_data['country']
            lat, lon = get_coordinates(state, country)

            graphs_dir = os.path.join(settings.BASE_DIR, 'static', 'graphs')
            os.makedirs(graphs_dir, exist_ok=True)

            years = list(range(2014, 2025))  # Example: 2015 to 2023
            available_graphs = []

            for year in years:
                weather = get_weather_data(lat, lon, year)

                dates = pd.to_datetime(weather['daily']['time'])
                df = pd.DataFrame({
                    'Date': dates,
                    'Max Temp': weather['daily']['temperature_2m_max'],
                    'Min Temp': weather['daily']['temperature_2m_min'],
                    'Precipitation': weather['daily']['precipitation_sum']
                })
                df['Month'] = df['Date'].dt.month
                monthly_avg = df.groupby('Month').mean()

                temp_path = f'monthly_temp_{year}.png'
                precip_path = f'monthly_precip_{year}.png'

                # Temperature plot
                plt.figure()
                monthly_avg[['Max Temp', 'Min Temp']].plot(kind='bar')
                plt.title(f"Monthly Average Temperature - {year}")
                plt.xlabel("Month")
                plt.ylabel("°C")
                plt.savefig(os.path.join(graphs_dir, precip_path))
                plt.close()

                available_graphs.append({
                    'year': year,
                    'temp': f'graphs/{temp_path}',
                    'precip': f'graphs/{precip_path}',
                })
            return render(request, 'weather/result.html', {
                'state': state,
                'country': country,
                'graphs_by_year': available_graphs,
                'default_year': 2023,
            })
        else:
            for error in form.non_field_errors():
                messages.error(request, error)
                return redirect('dashboard')

