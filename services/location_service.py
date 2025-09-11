#!/usr/bin/env python3
"""
Location Service
Handles GPS location validation for check-in/out
"""

import os
import logging
import math

logger = logging.getLogger(__name__)

# Work location coordinates (configure these for your actual work location)
WORK_LOCATION = {
    'latitude': 37.909416,  # Work location latitude
    'longitude': 23.871109,  # Work location longitude
    'radius_meters': 500   # Acceptable radius in meters
}

def validate_work_location(location):
    """
    Validate if user location is within work area
    
    Args:
        location: Telegram location object or dict with latitude and longitude
        
    Returns:
        bool: True if location is valid, False otherwise
    """
    try:
        # Extract coordinates - handle both object and dict
        if hasattr(location, 'latitude'):
            # Telegram object
            user_lat = location.latitude
            user_lon = location.longitude
        elif isinstance(location, dict):
            # Dict object
            user_lat = location.get('latitude')
            user_lon = location.get('longitude')
        else:
            logger.error(f"Invalid location object type: {type(location)}")
            return False
        
        # Validate coordinates
        if user_lat is None or user_lon is None:
            logger.error("Missing latitude or longitude in location data")
            return False
        
        # Calculate distance from work location
        distance = calculate_distance(
            WORK_LOCATION['latitude'], 
            WORK_LOCATION['longitude'],
            user_lat, 
            user_lon
        )
        
        # Check if within acceptable radius
        is_valid = distance <= WORK_LOCATION['radius_meters']
        
        logger.info(f"Location validation: {user_lat}, {user_lon} - Distance: {distance}m - Valid: {is_valid}")
        
        return is_valid
        
    except Exception as e:
        logger.error(f"Error validating location: {e}")
        return False

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two coordinates using Haversine formula
    
    Args:
        lat1, lon1: First coordinate (work location)
        lat2, lon2: Second coordinate (user location)
        
    Returns:
        float: Distance in meters
    """
    try:
        # Earth's radius in meters
        R = 6371000
        
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Calculate differences
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        # Haversine formula
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Calculate distance
        distance = R * c
        
        return distance
        
    except Exception as e:
        logger.error(f"Error calculating distance: {e}")
        return float('inf')  # Return infinite distance if calculation fails

def get_work_location_info():
    """
    Get work location information for display
    
    Returns:
        dict: Work location details
    """
    return {
        'latitude': WORK_LOCATION['latitude'],
        'longitude': WORK_LOCATION['longitude'],
        'radius_meters': WORK_LOCATION['radius_meters'],
        'radius_km': round(WORK_LOCATION['radius_meters'] / 1000, 2)
    }

def update_work_location(latitude, longitude, radius_meters=100):
    """
    Update work location coordinates
    
    Args:
        latitude: New work location latitude
        longitude: New work location longitude
        radius_meters: Acceptable radius in meters
    """
    global WORK_LOCATION
    
    WORK_LOCATION['latitude'] = latitude
    WORK_LOCATION['longitude'] = longitude
    WORK_LOCATION['radius_meters'] = radius_meters
    
    logger.info(f"Work location updated: {latitude}, {longitude} - Radius: {radius_meters}m")

class LocationService:
    """
    Location Service Class
    Handles GPS location validation for check-in/out
    """
    
    def __init__(self):
        self.work_location = WORK_LOCATION
    
    def validate_location(self, user_id):
        """
        Validate if user location is within work area
        This is a simplified version that always returns True for testing
        
        Args:
            user_id: User ID (not used in this simplified version)
            
        Returns:
            bool: True if location is valid, False otherwise
        """
        # For testing purposes, always return True
        # In production, this would check actual GPS location
        logger.info(f"Location validation for user {user_id}: ALWAYS TRUE (testing mode)")
        return True
    
    def get_work_location(self):
        """
        Get work location information
        
        Returns:
            dict: Work location details
        """
        return get_work_location_info()
