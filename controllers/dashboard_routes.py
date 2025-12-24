from flask import Blueprint, render_template, session, redirect, url_for, jsonify
from utils.auth import login_required
from utils.db import get_user_crops, get_user_fertilizers, find_user_by_id, get_dashboard_notifications, get_user_growing_activities
from datetime import datetime, timedelta
import json
import os
import random
import requests

dashboard_bp = Blueprint('dashboard', __name__)

# Weather cache to prevent random changes on every refresh
weather_cache = {}
WEATHER_CACHE_DURATION = 300  # 5 minutes in seconds

def get_price_predictions(user_district, user_state):
    """Generate price trend predictions for user's district"""
    # Load market data
    market_file = 'data/market_prices.json'
    if not os.path.exists(market_file):
        return []
    
    with open(market_file, 'r', encoding='utf-8') as f:
        market_data = json.load(f)
    
    # Get commodities for user's district
    district_data = [item for item in market_data['data'] 
                     if item['state'] == user_state and item['district'] == user_district]
    
    if not district_data:
        return []
    
    # Generate predictions for top commodities
    predictions = []
    top_commodities = ['Tomato', 'Onion', 'Potato', 'Cabbage', 'Banana', 'Mango']
    
    for commodity in top_commodities[:4]:  # Top 4 predictions
        commodity_data = [item for item in district_data if item['commodity'] == commodity]
        if commodity_data:
            item = commodity_data[0]
            current_price = item['modal_price']
            
            # Simulate prediction (in real app, use ML model)
            trend = random.choice(['increase', 'decrease', 'stable'])
            if trend == 'increase':
                change_percent = random.randint(8, 25)
                predicted_price = int(current_price * (1 + change_percent/100))
                icon = '📈'
                trend_class = 'bullish'
                message = f"likely to increase by {change_percent}%"
            elif trend == 'decrease':
                change_percent = random.randint(5, 15)
                predicted_price = int(current_price * (1 - change_percent/100))
                icon = '📉'
                trend_class = 'bearish'
                message = f"expected to decrease by {change_percent}%"
            else:
                change_percent = random.randint(-3, 3)
                predicted_price = int(current_price * (1 + change_percent/100))
                icon = '➡️'
                trend_class = 'stable'
                message = "expected to remain stable"
            
            predictions.append({
                'commodity': commodity,
                'current_price': current_price,
                'current_price_kg': round(current_price / 100, 2),
                'predicted_price': predicted_price,
                'predicted_price_kg': round(predicted_price / 100, 2),
                'change_percent': abs(change_percent),
                'trend': trend,
                'trend_class': trend_class,
                'icon': icon,
                'message': message,
                'market': item['market']
            })
    
    return predictions

def get_weather_notifications(user_district, user_state):
    """Generate weather alerts and forecasts for user's location using real WeatherAPI"""
    # Check cache first
    cache_key = f"{user_state}_{user_district}"
    current_time = datetime.now()
    
    if cache_key in weather_cache:
        cached_data, cache_time = weather_cache[cache_key]
        # Return cached data if less than 5 minutes old
        if (current_time - cache_time).total_seconds() < WEATHER_CACHE_DURATION:
            return cached_data
    
    # Use real WeatherAPI
    api_key = 'f4f904e64c374434a87104606252811'
    location = f"{user_district}, {user_state}, India"
    
    try:
        # Fetch current weather and forecast
        url = f'https://api.weatherapi.com/v1/forecast.json?key={api_key}&q={location}&days=7&aqi=no'
        response = requests.get(url, timeout=5)
        data = response.json()
        
        if 'error' in data:
            raise Exception(data['error']['message'])
        
        # Extract current weather
        current = data['current']
        current_temp = int(current['temp_c'])
        humidity = int(current['humidity'])
        wind_speed = int(current['wind_kph'])
        current_condition = current['condition']['text']
        
        # Map API conditions to icons
        condition_text = current_condition.lower()
        if 'sunny' in condition_text or 'clear' in condition_text:
            icon = '☀️'
            display_condition = 'Sunny'
        elif 'partly cloudy' in condition_text:
            icon = '⛅'
            display_condition = 'Partly Cloudy'
        elif 'cloudy' in condition_text or 'overcast' in condition_text:
            icon = '☁️'
            display_condition = 'Cloudy'
        elif 'rain' in condition_text and 'heavy' not in condition_text:
            icon = '🌦️'
            display_condition = 'Light Rain'
        elif 'heavy rain' in condition_text:
            icon = '🌧️'
            display_condition = 'Heavy Rain'
        elif 'thunder' in condition_text or 'storm' in condition_text:
            icon = '⛈️'
            display_condition = 'Thunderstorms'
        elif 'mist' in condition_text or 'fog' in condition_text:
            icon = '🌫️'
            display_condition = 'Mist'
        else:
            icon = '🌤️'
            display_condition = current_condition
        
        # Generate 7-day forecast from API
        forecast = []
        days_labels = ['Today', 'Tomorrow', 'Day 3', 'Day 4', 'Day 5', 'Day 6', 'Day 7']
        forecast_days = data['forecast']['forecastday']
        
        for i, day_data in enumerate(forecast_days):
            if i >= 7:
                break
            
            day_condition = day_data['day']['condition']['text']
            high_temp = int(day_data['day']['maxtemp_c'])
            low_temp = int(day_data['day']['mintemp_c'])
            rain_chance = int(day_data['day']['daily_chance_of_rain'])
            
            # Map condition to icon
            cond_lower = day_condition.lower()
            if 'sunny' in cond_lower or 'clear' in cond_lower:
                day_icon = '☀️'
            elif 'partly cloudy' in cond_lower:
                day_icon = '⛅'
            elif 'cloudy' in cond_lower or 'overcast' in cond_lower:
                day_icon = '☁️'
            elif 'rain' in cond_lower and 'heavy' not in cond_lower:
                day_icon = '🌦️'
            elif 'heavy rain' in cond_lower:
                day_icon = '🌧️'
            elif 'thunder' in cond_lower or 'storm' in cond_lower:
                day_icon = '⛈️'
            else:
                day_icon = '🌤️'
            
            forecast.append({
                'day': days_labels[i] if i < len(days_labels) else f'Day {i+1}',
                'condition': day_condition,
                'icon': day_icon,
                'high': high_temp,
                'low': low_temp,
                'rain_chance': rain_chance
            })
    
    except Exception as e:
        # Fallback to simulated data if API fails
        print(f"Weather API error: {e}")
        weather_conditions = ['Sunny', 'Partly Cloudy', 'Cloudy', 'Light Rain']
        current_condition = random.choice(weather_conditions)
        current_temp = random.randint(22, 35)
        humidity = random.randint(45, 85)
        wind_speed = random.randint(5, 25)
        icon = '⛅'
        display_condition = current_condition
        
        forecast = []
        days = ['Today', 'Tomorrow', 'Day 3', 'Day 4', 'Day 5', 'Day 6', 'Day 7']
        for i, day in enumerate(days):
            condition = random.choice(weather_conditions)
            forecast.append({
                'day': day,
                'condition': condition,
                'icon': '🌤️',
                'high': random.randint(28, 38),
                'low': random.randint(18, 26),
                'rain_chance': random.randint(0, 30)
            })
    
    # Generate farming alerts based on weather
    alerts = []
    
    # Rain alerts
    heavy_rain_days = [f for f in forecast[:3] if 'Heavy Rain' in f['condition'] or 'Thunder' in f['condition'] or 'storm' in f['condition'].lower()]
    if heavy_rain_days:
        alerts.append({
            'type': 'warning',
            'icon': '⚠️',
            'title': 'Heavy Rainfall Expected',
            'message': f'Heavy rain forecasted in next 3 days. Postpone irrigation and protect young crops.',
            'priority': 'high'
        })
    
    # Temperature alerts
    if current_temp > 35:
        alerts.append({
            'type': 'alert',
            'icon': '🌡️',
            'title': 'High Temperature Alert',
            'message': f'Temperature at {current_temp}°C. Ensure adequate irrigation for heat-sensitive crops.',
            'priority': 'medium'
        })
    
    # Humidity alerts
    if humidity > 75:
        alerts.append({
            'type': 'info',
            'icon': '💧',
            'title': 'High Humidity Warning',
            'message': f'Humidity at {humidity}%. Monitor for fungal diseases and reduce watering.',
            'priority': 'medium'
        })
    
    # Good weather for farming activities
    if display_condition in ['Sunny', 'Partly Cloudy'] and current_temp < 32:
        alerts.append({
            'type': 'success',
            'icon': '✅',
            'title': 'Ideal Farming Conditions',
            'message': 'Perfect weather for field activities like sowing, transplanting, and spraying.',
            'priority': 'low'
        })
    
    # Wind alerts
    if wind_speed > 20:
        alerts.append({
            'type': 'warning',
            'icon': '💨',
            'title': 'Strong Wind Alert',
            'message': f'Wind speed at {wind_speed} km/h. Avoid pesticide spraying and secure young plants.',
            'priority': 'high'
        })
    
    weather_data = {
        'current': {
            'condition': display_condition,
            'icon': icon,
            'temperature': current_temp,
            'humidity': humidity,
            'wind_speed': wind_speed,
            'location': f"{user_district}, {user_state}"
        },
        'forecast': forecast,
        'alerts': alerts
    }
    
    # Cache the weather data
    weather_cache[cache_key] = (weather_data, current_time)
    
    return weather_data

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    
    # Get complete user data from database (excluding password)
    user = find_user_by_id(user_id)
    
    # If user not found in database, use session data as fallback
    if not user:
        user = {
            '_id': user_id,
            'name': session.get('user_name', 'Unknown User'),
            'email': session.get('user_email', 'No email'),
            'phone': session.get('user_phone', 'Not provided'),
            'state': session.get('user_state', 'Not provided'), 
            'district': session.get('user_district', 'Not provided'),
            'created_at': datetime.utcnow()
        }
    else:
        # Ensure created_at exists for existing users
        if 'created_at' not in user or user['created_at'] is None:
            user['created_at'] = datetime.utcnow()
    
    saved_crops = get_user_crops(user_id)
    saved_fertilizers = get_user_fertilizers(user_id)
    growing_activities = get_user_growing_activities(user_id)
    notifications = get_dashboard_notifications(user_id)
    
    # Get price predictions for user's district
    price_predictions = []
    weather_data = {}
    if user.get('district') and user.get('state'):
        price_predictions = get_price_predictions(user['district'], user['state'])
        weather_data = get_weather_notifications(user['district'], user['state'])
    
    # Calculate statistics
    stats = {
        'total_recommendations': len(saved_crops) + len(saved_fertilizers),
        'crops_suggested': len(saved_crops),
        'fertilizers_saved': len(saved_fertilizers),
        'active_crops': len(growing_activities)
    }
    
    return render_template('dashboard.html', 
                         user=user,  # Complete user object with real data
                         saved_crops=saved_crops,
                         saved_fertilizers=saved_fertilizers,
                         growing_activities=growing_activities,
                         weather_data=weather_data,
                         notifications=notifications,
                         price_predictions=price_predictions,
                         stats=stats)

@dashboard_bp.route('/api/weather-update')
@login_required
def weather_update():
    """API endpoint for real-time weather updates"""
    user_id = session['user_id']
    user = find_user_by_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if user.get('district') and user.get('state'):
        weather_data = get_weather_notifications(user['district'], user['state'])
        weather_data['last_updated'] = datetime.now().strftime('%I:%M %p')
        return jsonify(weather_data)
    
    return jsonify({'error': 'Location not set'}), 400
