import aiohttp


OPENWEATHERMAP_API_KEY = "8990572e93b45ea63a0a28b157a9f027"
OPENWEATHERMAP_REVERSE_GEOCODING_URL = "http://api.openweathermap.org/geo/1.0/reverse"

async def get_city_by_coordinates(lat: float, lon: float) -> dict:
    """Получает полные данные о городе по координатам"""
    url = "http://api.openweathermap.org/geo/1.0/reverse"
    params = {
        "lat": lat,
        "lon": lon,
        "limit": 1,
        "appid": OPENWEATHERMAP_API_KEY
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return data[0] if data else None
    return None


async def get_city_data(city_name: str) -> dict:
    """Получает данные города через API"""
    url = "http://api.openweathermap.org/geo/1.0/direct"
    params = {
        "q": f"{city_name},RU",  # Ищем только в России
        "limit": 5,
        "appid": OPENWEATHERMAP_API_KEY,
        "lang": "ru"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return data[0] if data else None
    return None
