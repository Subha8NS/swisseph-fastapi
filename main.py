from fastapi import FastAPI
from pydantic import BaseModel
import swisseph as swe
import datetime
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Model for requests and responses
class PlanetPositionRequest(BaseModel):
    planet_name: str
    jd_ut: float

class PlanetPositionResponse(BaseModel):
    longitude: float
    latitude: float
    distance: float

class HouseCuspsRequest(BaseModel):
    jd_ut: float
    latitude: float
    longitude: float
    house_system: str = "P"  # Default to Placidus

class HouseCuspsResponse(BaseModel):
    cusps: list

class AyanamsaRequest(BaseModel):
    jd_ut: float

class AyanamsaResponse(BaseModel):
    ayanamsa: float

class JulianDayRequest(BaseModel):
    year: int
    month: int
    day: int
    hour: float

class JulianDayResponse(BaseModel):
    jd_ut: float

class RetrogradeMotionRequest(BaseModel):
    planet_name: str
    jd_ut: float

class RetrogradeMotionResponse(BaseModel):
    is_retrograde: bool

class SolarEclipseRequest(BaseModel):
    jd_ut: float

class SolarEclipseResponse(BaseModel):
    is_eclipse: bool

class LunarEclipseRequest(BaseModel):
    jd_ut: float

class LunarEclipseResponse(BaseModel):
    is_eclipse: bool

class SiderealTimeRequest(BaseModel):
    jd_ut: float

class SiderealTimeResponse(BaseModel):
    sidereal_time: float


# Planet position endpoint
@app.post("/planet_position", response_model=PlanetPositionResponse)
def get_planet_position(request: PlanetPositionRequest):
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
    return PlanetPositionResponse(longitude=ret[0], latitude=ret[1], distance=ret[2])


# House cusps endpoint
@app.post("/house_cusps", response_model=HouseCuspsResponse)
def get_house_cusps(request: HouseCuspsRequest):
    cusps, _ = swe.houses(request.jd_ut, request.latitude, request.longitude, request.house_system)
    return HouseCuspsResponse(cusps=cusps)


# Ayanamsa endpoint
@app.post("/ayanamsa", response_model=AyanamsaResponse)
def get_ayanamsa(request: AyanamsaRequest):
    ayanamsa = swe.get_ayanamsa(request.jd_ut)
    return AyanamsaResponse(ayanamsa=ayanamsa)


# Julian Day endpoint
@app.post("/julian_day", response_model=JulianDayResponse)
def get_julian_day(request: JulianDayRequest):
    jd_ut = swe.julday(request.year, request.month, request.day, request.hour)
    return JulianDayResponse(jd_ut=jd_ut)


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
