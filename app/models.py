from datetime import datetime
from enum import Enum
from sqlalchemy import (
    Column, Integer, String, Text, DECIMAL, TIMESTAMP, ForeignKey, 
    CheckConstraint, Enum as SQLEnum, func, Index, Boolean, Float
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from geoalchemy2 import Geometry
from . import db
import math
import logging
from typing import List, Optional, Dict, Any

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
    created_at = Column(TIMESTAMP, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(TIMESTAMP)
    is_active = Column(Boolean, default=True, server_default='1')
    
    preferences = relationship("Preference", back_populates="user", cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="user", cascade="all, delete-orphan")
    routes = relationship("Route", secondary="feedback", back_populates="users")

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'is_active': self.is_active,
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
    location = Column(Geometry(geometry_type='POINT', srid=4326))
    distance = Column(DECIMAL(6, 2), nullable=False)
    elevation_gain = Column(DECIMAL(6, 2))
    surface_type = Column(
        SQLEnum(SurfacePreference),
        nullable=False,
        default=SurfacePreference.ASPHALT,
        server_default=SurfacePreference.ASPHALT.value
    )
    has_sidewalks = Column(Boolean, default=False, server_default='0')
    is_lit = Column(Boolean, default=False, server_default='0')
    difficulty_score = Column(Float, nullable=True)
    popularity_score = Column(Float, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    feedback = relationship("Feedback", back_populates="route", cascade="all, delete-orphan")
    users = relationship("User", secondary="feedback", back_populates="routes")

    __table_args__ = (
        Index('idx_route_location', 'latitude', 'longitude'),
        Index('idx_route_distance', 'distance'),
        Index('idx_route_surface', 'surface_type'),
        Index('idx_route_difficulty', 'difficulty_score'),
        Index('idx_route_popularity', 'popularity_score'),
        Index('idx_route_spatial', 'location', postgresql_using='gist'),
    )

    @hybrid_property
    def average_rating(self) -> Optional[float]:
        """Calculate the average rating for the route."""
        if not self.feedback:
            return None
        ratings = [f.rating for f in self.feedback]
        return round(sum(ratings) / len(ratings), 2)

    @property
    def recent_feedback(self) -> List[Dict[str, Any]]:
        """Get the 5 most recent feedback entries."""
        return [f.to_dict() for f in sorted(
            self.feedback, 
            key=lambda x: x.created_at, 
            reverse=True
        )[:5]]

    def calculate_difficulty_score(self) -> float:
        """Calculate route difficulty based on distance and elevation."""
        try:
            distance_score = min(float(self.distance) / 10, 1.0)
            elevation_score = min(float(self.elevation_gain or 0) / 500, 1.0)
            return round((elevation_score * 0.6) + (distance_score * 0.4), 2)
        except Exception as e:
            logger.error(f"Error calculating difficulty score: {e}")
            return 0.5

    def update_popularity_score(self):
        """Update route popularity based on feedback and views."""
        try:
            feedback_count = len(self.feedback)
            avg_rating = self.average_rating or 0
            self.popularity_score = round(
                (avg_rating * 0.7) + (min(feedback_count / 10, 1) * 0.3), 
                2
            )
        except Exception as e:
            logger.error(f"Error updating popularity score: {e}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'latitude': float(self.latitude),
            'longitude': float(self.longitude),
            'distance': float(self.distance),
            'elevation_gain': float(self.elevation_gain) if self.elevation_gain else None,
            'surface_type': self.surface_type.value,
            'has_sidewalks': self.has_sidewalks,
            'is_lit': self.is_lit,
            'difficulty_score': self.difficulty_score,
            'popularity_score': self.popularity_score,
            'average_rating': self.average_rating,
            'recent_feedback': self.recent_feedback,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'feedback_count': len(self.feedback)
        }

    def __repr__(self):
        return f"<Route(name={self.name}, distance={self.distance}km)>"

class Preference(db.Model):
    __tablename__ = 'preferences'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    route_type = Column(
        SQLEnum(RouteType),
        nullable=False,
        default=RouteType.MIXED,
        server_default=RouteType.MIXED.value
    )
    elevation_preference = Column(
        SQLEnum(ElevationPreference),
        nullable=False,
        default=ElevationPreference.MODERATE,
        server_default=ElevationPreference.MODERATE.value
    )
    surface_preference = Column(
        SQLEnum(SurfacePreference),
        nullable=False,
        default=SurfacePreference.ASPHALT,
        server_default=SurfacePreference.ASPHALT.value
    )
    traffic_preference = Column(
        SQLEnum(TrafficPreference),
        nullable=False,
        default=TrafficPreference.NEUTRAL,
        server_default=TrafficPreference.NEUTRAL.value
    )
    crowd_preference = Column(
        SQLEnum(CrowdPreference),
        nullable=False,
        default=CrowdPreference.QUIET,
        server_default=CrowdPreference.QUIET.value
    )
    created_at = Column(TIMESTAMP, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="preferences")

    __table_args__ = (
        Index('idx_preference_user', 'user_id'),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'route_type': self.route_type.value,
            'elevation_preference': self.elevation_preference.value,
            'surface_preference': self.surface_preference.value,
            'traffic_preference': self.traffic_preference.value,
            'crowd_preference': self.crowd_preference.value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
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
    created_at = Column(TIMESTAMP, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    route = relationship("Route", back_populates="feedback")
    user = relationship("User", back_populates="feedback")

    __table_args__ = (
        Index('idx_feedback_route', 'route_id'),
        Index('idx_feedback_user', 'user_id'),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'route_id': self.route_id,
            'user_id': self.user_id,
            'rating': self.rating,
            'comment': self.comment,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f"<Feedback(route_id={self.route_id}, rating={self.rating})>"

# Register an event listener to validate coordinates and set the spatial location.
from sqlalchemy import event
@event.listens_for(Route, 'before_insert')
@event.listens_for(Route, 'before_update')
def validate_coordinates(mapper, connection, target):
    if not (-90 <= float(target.latitude) <= 90):
        raise ValueError("Latitude must be between -90 and 90")
    if not (-180 <= float(target.longitude) <= 180):
        raise ValueError("Longitude must be between -180 and 180")
    target.location = func.ST_SetSRID(
        func.ST_MakePoint(float(target.longitude), float(target.latitude)),
        4326
    )

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the Haversine distance between two points on Earth."""
    try:
        R = 6371  # Earth's radius in kilometers
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        return R * c
    except Exception as e:
        logger.error(f"Error calculating distance: {e}")
        return float('inf')

def search_routes(
    latitude: float,
    longitude: float,
    max_distance: float,
    elevation_preference: Optional[ElevationPreference] = None,
    surface_type: Optional[SurfacePreference] = None,
    min_rating: Optional[float] = None,
    page: int = 1,
    per_page: int = 20
) -> List[Route]:
    """Search routes using a spatial query with optional filters and pagination."""
    try:
        point = func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326)
        query = Route.query.filter(
            func.ST_DWithin(
                Route.location,
                point,
                max_distance * 1000  # Convert km to meters
            )
        )
        
        # Apply elevation filter.
        if elevation_preference:
            if elevation_preference == ElevationPreference.FLAT:
                query = query.filter(Route.elevation_gain <= 100)
            elif elevation_preference == ElevationPreference.MODERATE:
                query = query.filter(Route.elevation_gain.between(100, 300))
            else:
                query = query.filter(Route.elevation_gain > 300)
                
        # Apply surface type filter.
        if surface_type:
            query = query.filter(Route.surface_type == surface_type)
            
        # If filtering by minimum rating, join with feedback, group by Route ID, and apply HAVING.
        if min_rating is not None:
            query = query.outerjoin(Route.feedback).group_by(Route.id).having(func.avg(Feedback.rating) >= min_rating)
        
        query = query.order_by(
            func.ST_Distance(Route.location, point),
            Route.popularity_score.desc()
        )
        
        return query.paginate(page=page, per_page=per_page, error_out=False).items
        
    except Exception as e:
        logger.error(f"Error searching routes: {e}")
        db.session.rollback()
        raise

def save_preferences(
    user_id: int,
    route_type: RouteType,
    elevation_preference: ElevationPreference,
    surface_preference: SurfacePreference,
    traffic_preference: TrafficPreference,
    crowd_preference: CrowdPreference
) -> bool:
    """Save or update user preferences."""
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
    """Submit or update route feedback."""
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
    """Retrieve detailed route information."""
    try:
        route = Route.query.get_or_404(route_id)
        return route.to_dict()
    except Exception as e:
        logger.error(f"Error getting route details: {e}")
        db.session.rollback()
        raise
