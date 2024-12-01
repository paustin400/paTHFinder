# app/models.py
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Text, DECIMAL, TIMESTAMP, ForeignKey, CheckConstraint, Enum as SQLEnum, func, Index
from sqlalchemy.orm import relationship
from . import db
import math
import logging

logger = logging.getLogger(__name__)

class RouteType(str, Enum):
    ROAD = 'road'
    TRAIL = 'trail'
    MIXED = 'mixed'

class ElevationPreference(str, Enum):
    FLAT = 'flat'
    MODERATE = 'moderate'
    CHALLENGING = 'challenging'

class SurfacePreference(str, Enum):
    ASPHALT = 'asphalt'
    DIRT = 'dirt'
    GRASS = 'grass'

class TrafficPreference(str, Enum):
    AVOID = 'avoid'
    NEUTRAL = 'neutral'

class CrowdPreference(str, Enum):
    QUIET = 'quiet'
    SOCIAL = 'social'

class User(db.Model):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    preferences = relationship("Preference", back_populates="user", cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="user", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            'preferences': [pref.to_dict() for pref in self.preferences]
        }

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"

class Route(db.Model):
    __tablename__ = 'routes'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    latitude = Column(DECIMAL(10, 8), nullable=False)
    longitude = Column(DECIMAL(11, 8), nullable=False)
    distance = Column(DECIMAL(6, 2), nullable=False)
    elevation_gain = Column(DECIMAL(6, 2))
    surface_type = Column(SQLEnum(SurfacePreference), nullable=False, default=SurfacePreference.ASPHALT)
    has_sidewalks = Column(Integer, default=0)
    is_lit = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    feedback = relationship("Feedback", back_populates="route", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_route_location', 'latitude', 'longitude'),
        Index('idx_route_distance', 'distance'),
        Index('idx_route_surface', 'surface_type'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'latitude': float(self.latitude),
            'longitude': float(self.longitude),
            'distance': float(self.distance),
            'elevation_gain': float(self.elevation_gain) if self.elevation_gain else None,
            'surface_type': self.surface_type.value,
            'has_sidewalks': bool(self.has_sidewalks),
            'is_lit': bool(self.is_lit),
            'average_rating': self.average_rating,
            'created_at': self.created_at.isoformat(),
            'feedback_count': len(self.feedback)
        }

    @property
    def average_rating(self):
        if not self.feedback:
            return None
        ratings = [f.rating for f in self.feedback]
        return round(sum(ratings) / len(ratings), 2)

    def __repr__(self):
        return f"<Route(name={self.name}, distance={self.distance}km)>"

class Preference(db.Model):
    __tablename__ = 'preferences'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    route_type = Column(SQLEnum(RouteType), nullable=False)
    elevation_preference = Column(SQLEnum(ElevationPreference), nullable=False)
    surface_preference = Column(SQLEnum(SurfacePreference), nullable=False)
    traffic_preference = Column(SQLEnum(TrafficPreference), nullable=False)
    crowd_preference = Column(SQLEnum(CrowdPreference), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    user = relationship("User", back_populates="preferences")

    __table_args__ = (
        Index('idx_preference_user', 'user_id'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'route_type': self.route_type.value,
            'elevation_preference': self.elevation_preference.value,
            'surface_preference': self.surface_preference.value,
            'traffic_preference': self.traffic_preference.value,
            'crowd_preference': self.crowd_preference.value,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f"<Preference(user_id={self.user_id}, route_type={self.route_type})>"

class Feedback(db.Model):
    __tablename__ = 'feedback'
    
    id = Column(Integer, primary_key=True)
    route_id = Column(Integer, ForeignKey('routes.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    rating = Column(Integer, CheckConstraint('rating >= 1 AND rating <= 5'), nullable=False)
    comment = Column(Text)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    route = relationship("Route", back_populates="feedback")
    user = relationship("User", back_populates="feedback")

    __table_args__ = (
        Index('idx_feedback_route', 'route_id'),
        Index('idx_feedback_user', 'user_id'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'route_id': self.route_id,
            'user_id': self.user_id,
            'rating': self.rating,
            'comment': self.comment,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f"<Feedback(route_id={self.route_id}, rating={self.rating})>"

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate the Haversine distance between two points on Earth"""
    try:
        R = 6371  # Earth's radius in kilometers
        
        lat1, lon1, lat2, lon2 = map(math.radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        return R * c
    except Exception as e:
        logger.error(f"Error calculating distance: {e}")
        return float('inf')

def search_routes(latitude, longitude, max_distance, route_type=None, elevation_preference=None):
    """Search routes with pagination and optimized query"""
    try:
        query = Route.query

        # Calculate bounding box for initial filtering
        lat_range = max_distance / 111.0  # Approximate degrees per km
        lon_range = max_distance / (111.0 * math.cos(math.radians(float(latitude))))
        
        # Apply spatial filter first for query optimization
        query = query.filter(
            Route.latitude.between(float(latitude) - lat_range, float(latitude) + lat_range),
            Route.longitude.between(float(longitude) - lon_range, float(longitude) + lon_range)
        )

        # Apply additional filters
        if route_type:
            preferences = Preference.query.filter_by(route_type=route_type).all()
            route_ids = [p.route_id for p in preferences]
            if route_ids:
                query = query.filter(Route.id.in_(route_ids))
            
        if elevation_preference:
            if elevation_preference == ElevationPreference.FLAT:
                query = query.filter(Route.elevation_gain <= 100)
            elif elevation_preference == ElevationPreference.MODERATE:
                query = query.filter(Route.elevation_gain.between(100, 300))
            else:
                query = query.filter(Route.elevation_gain > 300)
        
        # Execute query
        routes = query.all()
        
        # Filter by exact distance
        filtered_routes = [
            route for route in routes
            if calculate_distance(latitude, longitude, route.latitude, route.longitude) <= max_distance
        ]
        
        return filtered_routes

    except Exception as e:
        logger.error(f"Error searching routes: {e}")
        db.session.rollback()
        raise

def save_preferences(user_id, route_type, elevation_preference, surface_preference, 
                    traffic_preference, crowd_preference):
    """Save or update user preferences"""
    try:
        existing = Preference.query.filter_by(user_id=user_id).first()
        if existing:
            existing.route_type = route_type
            existing.elevation_preference = elevation_preference
            existing.surface_preference = surface_preference
            existing.traffic_preference = traffic_preference
            existing.crowd_preference = crowd_preference
        else:
            new_pref = Preference(
                user_id=user_id,
                route_type=route_type,
                elevation_preference=elevation_preference,
                surface_preference=surface_preference,
                traffic_preference=traffic_preference,
                crowd_preference=crowd_preference
            )
            db.session.add(new_pref)
        
        db.session.commit()
        return True

    except Exception as e:
        logger.error(f"Error saving preferences: {e}")
        db.session.rollback()
        raise

def submit_feedback(route_id, user_id, rating, comment=None):
    """Submit or update route feedback"""
    try:
        existing = Feedback.query.filter_by(route_id=route_id, user_id=user_id).first()
        if existing:
            existing.rating = rating
            existing.comment = comment
        else:
            feedback = Feedback(
                route_id=route_id,
                user_id=user_id,
                rating=rating,
                comment=comment
            )
            db.session.add(feedback)
            
        db.session.commit()
        return True

    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        db.session.rollback()
        raise

def get_route_details(route_id):
    """Get detailed route information"""
    try:
        route = Route.query.get_or_404(route_id)
        return route.to_dict()

    except Exception as e:
        logger.error(f"Error getting route details: {e}")
        db.session.rollback()
        raise