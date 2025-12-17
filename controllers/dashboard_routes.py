from flask import Blueprint, render_template, session, redirect, url_for
from utils.auth import login_required
from utils.db import get_user_crops, get_user_fertilizers, get_user_diseases, find_user_by_id, get_dashboard_notifications, get_user_growing_activities
from datetime import datetime

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    
    # Get complete user data from database (excluding password)
    user = find_user_by_id(user_id)
    
    # If user not found in database, create a fallback using session data
    if not user:
        user = {
            'name': session.get('user_name', 'Unknown User'),
            'email': session.get('user_email', 'No email'),
            'phone': 'Not provided',
            'state': 'Not provided', 
            'district': 'Not provided',
            'created_at': None
        }
    
    saved_crops = get_user_crops(user_id)
    saved_fertilizers = get_user_fertilizers(user_id)
    disease_history = get_user_diseases(user_id)
    growing_activities = get_user_growing_activities(user_id)
    notifications = get_dashboard_notifications(user_id)
    
    # Calculate statistics
    stats = {
        'total_recommendations': len(saved_crops) + len(saved_fertilizers),
        'crops_suggested': len(saved_crops),
        'diseases_detected': len(disease_history),
        'fertilizers_saved': len(saved_fertilizers),
        'active_crops': len(growing_activities)
    }
    
    return render_template('dashboard.html', 
                         user=user,  # Complete user object with real data
                         saved_crops=saved_crops,
                         saved_fertilizers=saved_fertilizers,
                         disease_history=disease_history,
                         growing_activities=growing_activities,
                         notifications=notifications,
                         stats=stats)
