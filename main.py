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

# GET endpoint for planets
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

# Keep your existing POST endpoints below
# ... existing code ...
