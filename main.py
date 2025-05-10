from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import swisseph as swe
import datetime
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    try:
        version = swe.version
        return {"Swiss Ephemeris Version": version}
    except Exception as e:
        return {"error": f"Error getting Swiss Ephemeris version: {str(e)}"}
    
class RetrogradeMotionResponse(BaseModel):
    planet: str
    is_retrograde: bool
    speed: float  # degrees/day
    date: str     # ISO format, e.g., '2025-05-10'

class RetrogradeMotionRequest(BaseModel):
    planet: str         # e.g., "Mercury"
    date: str           # ISO format: "2025-05-10"
# GET endpoint for planets
class SolarEclipseResponse(BaseModel):
    eclipse_type: str               # e.g., "Total", "Partial", "Annular"
    date: str                       # ISO format: "2025-10-14"
    time_utc: str                   # e.g., "17:22:00"
    magnitude: Optional[float]      # Fraction of the sun's diameter obscured
    central_duration: Optional[str]  # e.g., "00:03:25"
    visible_from: Optional[str]     # e.g., "North America"

class SolarEclipseRequest(BaseModel):
    date: str                   # e.g., "2025-10-14" (start search date)
    latitude: Optional[float]   # optional location to check visibility
    longitude: Optional[float]  # optional location to check visibility
    search_forward: Optional[bool] = True  # search direction (default forward)

class LunarEclipseResponse(BaseModel):
    eclipse_type: str               # "Total", "Partial", or "Penumbral"
    date: str                       # ISO format: "2025-03-14"
    time_utc: str                   # Time of greatest eclipse (e.g., "03:26:00")
    magnitude: Optional[float]      # Fraction of the Moon's diameter immersed
    duration: Optional[str]         # Duration of the eclipse (e.g., "03:42:00")
    visible_from: Optional[str]     # Description or region, e.g., "Asia, Europe"
    
class LunarEclipseRequest(BaseModel):
    date: str                   # Start date for the eclipse search, e.g., "2025-03-14"
    latitude: Optional[float]   # Optional: observer's latitude
    longitude: Optional[float]  # Optional: observer's longitude
    search_forward: Optional[bool] = True  # True to search forward in time

class SiderealTimeResponse(BaseModel):
    date: str                 # ISO format: "2025-05-10"
    time_utc: str             # e.g., "16:45:00"
    longitude: float          # In decimal degrees
    sidereal_time: str        # e.g., "10h 35m 28s"
    sidereal_time_deg: float  # Sidereal time in decimal degrees
    type: str                 # "GST" (Greenwich) or "LST" (Local)

class SiderealTimeRequest(BaseModel):
    date: str                   # Start date for the sidereal time calculation (e.g., "2025-05-10")
    time_utc: str               # Time in UTC (e.g., "16:45:00")
    longitude: Optional[float]  # Observer's longitude (optional for LST)
    type: str                   # "GST" for Greenwich Sidereal Time or "LST" for Local Sidereal Time


@app.get("/planets")
def get_planets(date: str, time: str = "00:00:00"):
    try:
        # Parse date and time
        year, month, day = map(int, date.split('-'))
        hour, minute, second = map(int, time.split(':'))
        
        # Calculate decimal hour
        decimal_hour = hour + minute/60.0 + second/3600.0
        
        # Calculate Julian Day
        jd_ut = swe.julday(year, month, day, decimal_hour)
        
        # Planet dictionary
        planet_dict = {
            "Sun": swe.SUN,
            "Moon": swe.MOON,
            "Mercury": swe.MERCURY,
            "Venus": swe.VENUS,
            "Mars": swe.MARS,
            "Jupiter": swe.JUPITER,
            "Saturn": swe.SATURN,
            "Uranus": swe.URANUS,
            "Neptune": swe.NEPTUNE,
            "Pluto": swe.PLUTO
        }
        
        result = {}
        
        # Calculate positions for all planets
        for planet_name, planet_id in planet_dict.items():
            try:
                ret, flags = swe.calc_ut(jd_ut, planet_id, swe.FLG_SPEED)
                result[planet_name] = {
                    "longitude": ret[0],
                    "latitude": ret[1],
                    "distance": ret[2],
                    "longitude_speed": ret[3],
                    "latitude_speed": ret[4],
                    "distance_speed": ret[5]
                }
            except Exception as e:
                result[planet_name] = {"error": str(e)}
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating planetary positions: {str(e)}")

# GET endpoint for houses
@app.get("/houses")
def get_houses(date: str, time: str = "00:00:00", lat: float = 0.0, lon: float = 0.0, system: str = "P"):
    try:
        # Parse date and time
        year, month, day = map(int, date.split('-'))
        hour, minute, second = map(int, time.split(':'))
        
        # Calculate decimal hour
        decimal_hour = hour + minute/60.0 + second/3600.0
        
        # Calculate Julian Day
        jd_ut = swe.julday(year, month, day, decimal_hour)
        
        # Calculate houses
        cusps, ascmc = swe.houses(jd_ut, lat, lon, system)
        
        return {
            "cusps": list(cusps),
            "ascendant": ascmc[0],
            "midheaven": ascmc[1],
            "armc": ascmc[2],
            "vertex": ascmc[3]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating houses: {str(e)}")

# GET endpoint for ayanamsa
@app.get("/ayanamsa")
def get_ayanamsa(date: str, time: str = "00:00:00"):
    try:
        # Parse date and time
        year, month, day = map(int, date.split('-'))
        hour, minute, second = map(int, time.split(':'))
        
        # Calculate decimal hour
        decimal_hour = hour + minute/60.0 + second/3600.0
        
        # Calculate Julian Day
        jd_ut = swe.julday(year, month, day, decimal_hour)
        
        # Get ayanamsa
        ayanamsa = swe.get_ayanamsa(jd_ut)
        
        return {"ayanamsa": ayanamsa}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating ayanamsa: {str(e)}")

# GET endpoint for Julian Day
@app.get("/julian_day")
def get_julian_day(date: str, time: str = "00:00:00"):
    try:
        # Parse date and time
        year, month, day = map(int, date.split('-'))
        hour, minute, second = map(int, time.split(':'))
        
        # Calculate decimal hour
        decimal_hour = hour + minute/60.0 + second/3600.0
        
        # Calculate Julian Day
        jd_ut = swe.julday(year, month, day, decimal_hour)
        
        return {"jd_ut": jd_ut}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating Julian Day: {str(e)}")

# Retrograde motion endpoint
@app.post("/retrograde_motion", response_model=RetrogradeMotionResponse)
def get_retrograde_motion(request: RetrogradeMotionRequest):
    planet_dict = {
        "sun": swe.SUN,
        "moon": swe.MOON,
        "mercury": swe.MERCURY,
        "venus": swe.VENUS,
        "mars": swe.MARS,
        "jupiter": swe.JUPITER,
        "saturn": swe.SATURN,
        "uranus": swe.URANUS,
        "neptune": swe.NEPTUNE,
        "pluto": swe.PLUTO
    }
    planet_id = planet_dict.get(request.planet_name.lower())
    if not planet_id:
        return {"error": "Invalid planet name"}
    
    ret, _ = swe.calc(request.jd_ut, planet_id)
    retrograde = ret[0] < 180  # Simple retrograde check based on longitude (simplified)
    return RetrogradeMotionResponse(is_retrograde=retrograde)


# Solar eclipse endpoint
@app.post("/solar_eclipse", response_model=SolarEclipseResponse)
def get_solar_eclipse(request: SolarEclipseRequest):
    # Solar eclipse detection (simplified)
    is_eclipse = False
    # You would need to calculate the solar eclipse based on the position of the sun and moon
    return SolarEclipseResponse(is_eclipse=is_eclipse)


# Lunar eclipse endpoint
@app.post("/lunar_eclipse", response_model=LunarEclipseResponse)
def get_lunar_eclipse(request: LunarEclipseRequest):
    # Lunar eclipse detection (simplified)
    is_eclipse = False
    # You would need to calculate the lunar eclipse based on the positions of the sun, earth, and moon
    return LunarEclipseResponse(is_eclipse=is_eclipse)


# Sidereal time endpoint
@app.post("/sidereal_time", response_model=SiderealTimeResponse)
def get_sidereal_time(request: SiderealTimeRequest):
    sidereal_time = swe.sidtime(request.jd_ut)
    return SiderealTimeResponse(sidereal_time=sidereal_time)
