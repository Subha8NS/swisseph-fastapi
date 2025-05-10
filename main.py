from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import swisseph as swe
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import os
import uvicorn

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
        # Basic Swiss Ephemeris operation as a health check
        jd = swe.julday(2025, 5, 10)
        return {
            "message": "Swiss Ephemeris API is up and running.",
            "sample_julian_day": jd
        }
    except Exception as e:
        return {"error": f"Swiss Ephemeris not responding: {str(e)}"}

# --- Models ---

class RetrogradeMotionRequest(BaseModel):
    planet: str         # e.g., "Mercury"
    date: str           # ISO format: "2025-05-10"

class RetrogradeMotionResponse(BaseModel):
    planet: str
    is_retrograde: bool
    speed: float  # degrees/day
    date: str     # ISO format

class SolarEclipseRequest(BaseModel):
    date: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    search_forward: Optional[bool] = True

class SolarEclipseResponse(BaseModel):
    eclipse_type: str
    date: str
    time_utc: str
    magnitude: Optional[float] = None
    central_duration: Optional[str] = None
    visible_from: Optional[str] = None

class LunarEclipseRequest(BaseModel):
    date: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    search_forward: Optional[bool] = True

class LunarEclipseResponse(BaseModel):
    eclipse_type: str
    date: str
    time_utc: str
    magnitude: Optional[float] = None
    duration: Optional[str] = None
    visible_from: Optional[str] = None

class SiderealTimeRequest(BaseModel):
    date: str
    time_utc: str
    longitude: Optional[float] = None
    type: str  # "GST" or "LST"

class SiderealTimeResponse(BaseModel):
    date: str
    time_utc: str
    longitude: float
    sidereal_time: str
    sidereal_time_deg: float
    type: str

# --- Endpoints ---

@app.get("/planets")
def get_planets(date: str, time: str = "00:00:00"):
    try:
        year, month, day = map(int, date.split('-'))
        hour, minute, second = map(int, time.split(':'))
        decimal_hour = hour + minute/60.0 + second/3600.0
        jd_ut = swe.julday(year, month, day, decimal_hour)
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

@app.get("/houses")
def get_houses(date: str, time: str = "00:00:00", lat: float = 0.0, lon: float = 0.0, system: str = "P"):
    try:
        year, month, day = map(int, date.split('-'))
        hour, minute, second = map(int, time.split(':'))
        decimal_hour = hour + minute/60.0 + second/3600.0
        jd_ut = swe.julday(year, month, day, decimal_hour)
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

@app.get("/ayanamsa")
def get_ayanamsa(date: str, time: str = "00:00:00"):
    try:
        year, month, day = map(int, date.split('-'))
        hour, minute, second = map(int, time.split(':'))
        decimal_hour = hour + minute/60.0 + second/3600.0
        jd_ut = swe.julday(year, month, day, decimal_hour)
        ayanamsa = swe.get_ayanamsa(jd_ut)
        return {"ayanamsa": ayanamsa}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating ayanamsa: {str(e)}")

@app.get("/julian_day")
def get_julian_day(date: str, time: str = "00:00:00"):
    try:
        year, month, day = map(int, date.split('-'))
        hour, minute, second = map(int, time.split(':'))
        decimal_hour = hour + minute/60.0 + second/3600.0
        jd_ut = swe.julday(year, month, day, decimal_hour)
        return {"jd_ut": jd_ut}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating Julian Day: {str(e)}")

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
    planet_id = planet_dict.get(request.planet.lower())
    if not planet_id:
        raise HTTPException(status_code=400, detail="Invalid planet name")
    year, month, day = map(int, request.date.split('-'))
    jd_ut = swe.julday(year, month, day)
    ret, _ = swe.calc_ut(jd_ut, planet_id, swe.FLG_SPEED)
    speed = ret[3]  # longitude speed
    is_retrograde = speed < 0
    return RetrogradeMotionResponse(
        planet=request.planet,
        is_retrograde=is_retrograde,
        speed=speed,
        date=request.date
    )

@app.post("/solar_eclipse", response_model=SolarEclipseResponse)
def get_solar_eclipse(request: SolarEclipseRequest):
    # Placeholder logic
    return SolarEclipseResponse(
        eclipse_type="None",
        date=request.date,
        time_utc="00:00:00"
    )

@app.post("/lunar_eclipse", response_model=LunarEclipseResponse)
def get_lunar_eclipse(request: LunarEclipseRequest):
    # Placeholder logic
    return LunarEclipseResponse(
        eclipse_type="None",
        date=request.date,
        time_utc="00:00:00"
    )

@app.post("/sidereal_time", response_model=SiderealTimeResponse)
def get_sidereal_time(request: SiderealTimeRequest):
    year, month, day = map(int, request.date.split('-'))
    hour, minute, second = map(int, request.time_utc.split(':'))
    decimal_hour = hour + minute/60.0 + second/3600.0
    jd_ut = swe.julday(year, month, day, decimal_hour)
    sidereal_time_deg = swe.sidtime(jd_ut)
    hours = int(sidereal_time_deg // 15)
    minutes = int((sidereal_time_deg % 15) * 4)
    seconds = int((((sidereal_time_deg % 15) * 4) % 1) * 60)
    sidereal_time_str = f"{hours}h {minutes}m {seconds}s"
    longitude = request.longitude if request.longitude else 0.0
    return SiderealTimeResponse(
        date=request.date,
        time_utc=request.time_utc,
        longitude=longitude,
        sidereal_time=sidereal_time_str,
        sidereal_time_deg=sidereal_time_deg,
        type=request.type
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
