import React, { useEffect, useState } from "react";
import axios from "axios";
import "../styles/WeatherWidget.css";

import buenosAiresImg from '../imagenes/Buenos-Aires.jpg';
import newYorkImg from '../imagenes/New-York.jpg';
import londonImg from '../imagenes/London.jpg';
import tokioImg from '../imagenes/tokio.jpg';


const HourlyForecastChart = ({ hourlyData }) => {
  if (!hourlyData || hourlyData.length === 0) return null;

  const width = 700;
  const height = 100;
  const padding = 15;

  const temps = hourlyData.map(h => h.main.temp);
  const minTemp = Math.min(...temps) - 2;
  const maxTemp = Math.max(...temps) + 2;

  const scale = (value, domain, range) => {
    return range[0] + (range[1] - range[0]) * ((value - domain[0]) / (domain[1] - domain[0]));
  };

  const points = hourlyData.map((hour, index) => {
    const x = scale(index, [0, hourlyData.length - 1], [padding, width - padding]);
    const y = scale(hour.main.temp, [minTemp, maxTemp], [height - padding, padding]);
    return { 
      x, 
      y, 
      temp: Math.round(hour.main.temp), 
      time: new Date(hour.dt * 1000).getHours() + ":00",
      icon: hour.weather[0].icon
    };
  });

  const createPath = (points) => {
    let path = `M ${points[0].x},${points[0].y}`;
    for (let i = 0; i < points.length - 1; i++) {
      const x_mid = (points[i].x + points[i + 1].x) / 2;
      const y_mid = (points[i].y + points[i + 1].y) / 2;
      path += ` Q ${points[i].x},${points[i].y} ${x_mid},${y_mid}`;
    }
    path += ` L ${points[points.length-1].x},${points[points.length-1].y}`;
    return path;
  };

  const pathData = createPath(points);

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="hourly-chart-svg">
      <defs>
        <linearGradient id="temperatureGradient" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#ff6b6b" />
          <stop offset="50%" stopColor="#4ecdc4" />
          <stop offset="100%" stopColor="#45b7d1" />
        </linearGradient>
      </defs>
      
      <path d={pathData} className="graph-line" />
      
      {/* Área bajo la curva */}
      <path d={`${pathData} L ${points[points.length-1].x} ${height - padding} L ${points[0].x} ${height - padding} Z`} 
            className="graph-area" />
      
      {points.map((point, index) => (
        <g key={index} className="data-point-group">
          <circle cx={point.x} cy={point.y} r="4" className="graph-point-marker" />
          <text x={point.x} y={point.y - 8} className="graph-temp-text">
            {point.temp}°
          </text>
          <foreignObject x={point.x - 15} y={height - 20} width="30" height="15">
            <div className="hour-time">{point.time}</div>
          </foreignObject>
        </g>
      ))}
    </svg>
  );
};


const StaticCityCard = ({ cityData, bgImage }) => {
  if (!cityData) return null;

  const temp = Math.round(cityData.main.temp);
  const icon = cityData.weather[0].icon;
  const description = cityData.weather[0].description;
  const { humidity, pressure } = cityData.main;
  const windSpeed = Math.round(cityData.wind.speed * 3.6);

  const getOverlayStyle = (temperature) => {
    let background;
    if (temperature > 28) {
      background = 'linear-gradient(135deg, rgba(179, 0, 12, 0.85), rgba(220, 50, 40, 0.7))';
    } else if (temperature > 20) {
      background = 'linear-gradient(135deg, rgba(238, 128, 40, 0.85), rgba(245, 160, 60, 0.7))';
    } else if (temperature > 10) {
      background = 'linear-gradient(135deg, rgba(40, 178, 99, 0.85), rgba(80, 200, 120, 0.7))';
    } else {
      background = 'linear-gradient(135deg, rgba(40, 138, 238, 0.85), rgba(80, 160, 250, 0.7))';
    }
    return { background };
  };

  const cardStyle = {
    backgroundImage: `linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.3)), url(${bgImage})`,
  };
  const overlayStyle = getOverlayStyle(temp);

  return (
    <div className="static-city-card" style={cardStyle}>
      <div className="static-city-overlay" style={overlayStyle}>
        <div className="static-city-header">
          <h3 className="static-city-name">{cityData.name}</h3>
          <p className="static-city-description">{description}</p>
        </div>
        <div className="static-city-body">
          <div className="weather-icon-container">
            <img
              src={`https://openweathermap.org/img/wn/${icon}@2x.png`}
              alt={description}
              className="weather-icon"
              onError={(e) => {
                e.target.style.display = 'none';
                e.target.nextSibling.style.display = 'block';
              }}
              style={{ 
                filter: 'brightness(1.3) saturate(1.4) hue-rotate(-10deg)' 
              }}
            />
            <div className="weather-icon-fallback" style={{display: 'none'}}>
              {icon.includes('01') ? '☀️' : 
               icon.includes('02') ? '⛅' :
               icon.includes('03') || icon.includes('04') ? '☁️' :
               icon.includes('09') || icon.includes('10') ? '🌧️' :
               icon.includes('11') ? '⛈️' :
               icon.includes('13') ? '❄️' :
               icon.includes('50') ? '🌫️' : '🌈'}
            </div>
          </div>
          <span className="static-city-temp">{temp}°C</span>
        </div>
        <div className="static-city-footer">
          <div className="weather-stat">
            <span className="stat-label">💧 Humedad</span>
            <span className="stat-value">{humidity}%</span>
          </div>
          <div className="weather-stat">
            <span className="stat-label">🌬️ Viento</span>
            <span className="stat-value">{windSpeed} km/h</span>
          </div>
        </div>
      </div>
    </div>
  );
};


const WeatherWidget = () => {
  const [mainWeather, setMainWeather] = useState(null);
  const [hourlyForecast, setHourlyForecast] = useState([]);
  const [dailyForecast, setDailyForecast] = useState([]);
  const [staticCities, setStaticCities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const API_KEY = import.meta.env.VITE_CLIMA_API_KEY;
  
  const staticCityConfig = [
    { name: "Buenos Aires", image: buenosAiresImg },
    { name: "New York", image: newYorkImg },
    { name: "London", image: londonImg },
    { name: "Tokyo", image: tokioImg },
  ];


  const getMostFrequentIcon = (weatherArray) => {
    const iconCounts = {};
    weatherArray.forEach(w => {
      iconCounts[w.icon] = (iconCounts[w.icon] || 0) + 1;
    });
    return Object.keys(iconCounts).reduce((a, b) => 
      iconCounts[a] > iconCounts[b] ? a : b
    );
  };


  const getCurrentLocation = () => {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(new Error("Geolocation no está soportado"));
        return;
      }

 
      navigator.geolocation.getCurrentPosition(
        (position) => {
          resolve({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude
          });
        },
        (error) => {
          console.warn("Error obteniendo ubicación GPS:", error);
          reject(error);
        }

      );
    });
  };


  const getCityFromCoordinates = async (lat, lon) => {
    try {
      const response = await axios.get(
        `https://api.openweathermap.org/geo/1.0/reverse?lat=${lat}&lon=${lon}&limit=1&appid=${API_KEY}`
      );
      
      if (response.data && response.data.length > 0) {
        return response.data[0].name;
      }
      return "Ubicación Actual";
    } catch (error) {
      console.warn("Error en reverse geocoding:", error);
      return "Ubicación Actual";
    }
  };


  const fetchAllData = async (lat, lon, cityName = "Ubicación Actual") => {
    setLoading(true);
    setError(null);

    const CACHE_KEY = "weatherData";
    const CACHE_DURATION = 30 * 60 * 1000; 
    const cachedData = localStorage.getItem(CACHE_KEY);
    if (cachedData) {
      try {
        const { data, timestamp, location } = JSON.parse(cachedData);
        const isSameLocation = location.lat === lat && location.lon === lon;
        
        if (Date.now() - timestamp < CACHE_DURATION && isSameLocation) {
          setMainWeather(data.mainWeather);
          setHourlyForecast(data.hourlyForecast);
          setDailyForecast(data.dailyForecast);
          setStaticCities(data.staticCities);
          setLoading(false);
          return;
        }
      } catch (cacheError) {
        console.warn("Error leyendo caché:", cacheError);
        localStorage.removeItem(CACHE_KEY);
      }
    }

    try {
      const weatherPromise = axios.get(
        `https://api.openweathermap.org/data/2.5/weather?lat=${lat}&lon=${lon}&appid=${API_KEY}&units=metric&lang=es`
      );
      
      const forecastPromise = axios.get(
        `https://api.openweathermap.org/data/2.5/forecast?lat=${lat}&lon=${lon}&appid=${API_KEY}&units=metric&lang=es`
      );
      
      const staticCitiesPromises = staticCityConfig.map(city =>
        axios.get(
          `https://api.openweathermap.org/data/2.5/weather?q=${city.name}&appid=${API_KEY}&units=metric&lang=es`
        ).catch(err => {
          console.warn(`No se pudo cargar datos para ${city.name}:`, err);
          return null;
        })
      );

      const [weatherRes, forecastRes, ...staticCitiesRes] = await Promise.all([
        weatherPromise,
        forecastPromise,
        ...staticCitiesPromises
      ]);

 
      const newMainWeather = {
        ...weatherRes.data,
        name: cityName
      };


      const newHourlyForecast = forecastRes.data.list.slice(0, 8);

      const dailyData = {};
      forecastRes.data.list.forEach(reading => {
        const date = new Date(reading.dt * 1000).toLocaleDateString('es-ES');
        if (!dailyData[date]) {
          dailyData[date] = {
            temps: [],
            weather: [],
            dt: reading.dt
          };
        }
        dailyData[date].temps.push(reading.main.temp);
        dailyData[date].weather.push(reading.weather[0]);
      });


      const processedDaily = Object.values(dailyData)
        .slice(0, 5) 
        .map(day => {
          const mostFrequentIcon = getMostFrequentIcon(day.weather);
          return {
            dt: day.dt,
            temp_max: Math.round(Math.max(...day.temps)),
            temp_min: Math.round(Math.min(...day.temps)),
            weather: [{ icon: mostFrequentIcon, description: day.weather[0].description }]
          };
        });


      const newStaticCities = staticCitiesRes
        .filter(res => res !== null && res.data)
        .map(res => res.data);

      const newData = {
        mainWeather: newMainWeather,
        hourlyForecast: newHourlyForecast,
        dailyForecast: processedDaily,
        staticCities: newStaticCities,
      };

      setMainWeather(newMainWeather);
      setHourlyForecast(newHourlyForecast);
      setDailyForecast(processedDaily);
      setStaticCities(newStaticCities);


      localStorage.setItem(CACHE_KEY, JSON.stringify({ 
        data: newData, 
        timestamp: Date.now(),
        location: { lat, lon, city: cityName }
      }));
      
    } catch (err) {
      console.error("Error fetching weather data:", err);
      setError("No se pudo cargar la información del clima. Intenta recargar la página.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const initializeWeather = async () => {
      try {
        setLoading(true);
        

        try {
          const location = await getCurrentLocation();
          const cityName = await getCityFromCoordinates(location.latitude, location.longitude);
          await fetchAllData(location.latitude, location.longitude, cityName);
          return;
        } catch (gpsError) {
          console.warn("GPS falló, intentando por IP:", gpsError);
        }


        try {
          const ipRes = await axios.get("https://ipapi.co/json/", { timeout: 5000 });
          const { latitude, longitude, city } = ipRes.data;
          
          if (latitude && longitude) {
            await fetchAllData(latitude, longitude, city || "Ubicación Actual");
            return;
          }
          throw new Error("Datos de IP incompletos");
        } catch (ipError) {
          console.warn("Geolocalización por IP falló:", ipError);
        }


        console.log("Usando ubicación por defecto: Buenos Aires");
        await fetchAllData(-34.61, -58.38, "Buenos Aires");

      } catch (error) {
        console.error("Error inicializando clima:", error);
        setError("No se pudo determinar tu ubicación. Mostrando clima de Buenos Aires.");
        

        try {
          await fetchAllData(-34.61, -58.38, "Buenos Aires");
        } catch (finalError) {
          setError("Error crítico cargando datos del clima.");
        }
      }
    };

    initializeWeather();
  }, [API_KEY]);

  if (loading) {
    return (
      <div className="weather-loading">
        <div className="loading-spinner"></div>
        <p>Cargando información del clima...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="weather-error">
        <div className="error-icon">⚠️</div>
        <p>{error}</p>
        <button 
          onClick={() => window.location.reload()} 
          className="retry-button"
        >
          Reintentar
        </button>
      </div>
    );
  }

  if (!mainWeather) {
    return (
      <div className="weather-error">
        <div className="error-icon">❌</div>
        <p>No se pudieron cargar los datos del clima</p>
        <button 
          onClick={() => window.location.reload()} 
          className="retry-button"
        >
          Reintentar
        </button>
      </div>
    );
  }

  return (
    <div className="weather-grid-container">
      {}
      <div className="main-weather-card">
        <div className="main-header">
          <div className="main-header-left">
            <div className="weather-icon-container">
              <img
                src={`https://openweathermap.org/img/wn/${mainWeather.weather[0].icon}@2x.png`}
                alt={mainWeather.weather[0].description}
                className="weather-icon"
                onError={(e) => {
                  e.target.style.display = 'none';
                  e.target.nextSibling.style.display = 'block';
                }}
                style={{ 
                  filter: 'brightness(1.3) saturate(1.4) hue-rotate(-10deg)'
                }}
              />
              <div className="weather-icon-fallback" style={{display: 'none'}}>
                {mainWeather.weather[0].icon.includes('01') ? '☀️' : 
                 mainWeather.weather[0].icon.includes('02') ? '⛅' :
                 mainWeather.weather[0].icon.includes('03') || mainWeather.weather[0].icon.includes('04') ? '☁️' :
                 mainWeather.weather[0].icon.includes('09') || mainWeather.weather[0].icon.includes('10') ? '🌧️' :
                 mainWeather.weather[0].icon.includes('11') ? '⛈️' :
                 mainWeather.weather[0].icon.includes('13') ? '❄️' :
                 mainWeather.weather[0].icon.includes('50') ? '🌫️' : '🌈'}
              </div>
            </div>
            <div className="temperature-section">
              <span className="main-temp">{Math.round(mainWeather.main.temp)}°C</span>
              <div className="feels-like">
                Sensación: {Math.round(mainWeather.main.feels_like)}°C
              </div>
            </div>
          </div>
          <div className="main-header-right">
            <h2 className="main-city">{mainWeather.name}</h2>
            <p className="main-date">
              {new Date().toLocaleDateString('es-ES', { 
                weekday: 'long', 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric',
                hour: '2-digit', 
                minute: '2-digit' 
              })}
            </p>
            <p className="weather-description">
              {mainWeather.weather[0].description}
            </p>
          </div>
        </div>

        {}
        <div className="weather-stats-grid">
          <div className="weather-stat-card">
            <span className="stat-icon">💧</span>
            <div className="stat-info">
              <span className="stat-value">{mainWeather.main.humidity}%</span>
              <span className="stat-label">Humedad</span>
            </div>
          </div>
          <div className="weather-stat-card">
            <span className="stat-icon">🌬️</span>
            <div className="stat-info">
              <span className="stat-value">{Math.round(mainWeather.wind.speed * 3.6)} km/h</span>
              <span className="stat-label">Viento</span>
            </div>
          </div>
        </div>

        <div className="hourly-forecast-graph">
          <h3 className="section-title">Pronóstico por Hora</h3>
          <HourlyForecastChart hourlyData={hourlyForecast} />
        </div>

        <div className="weekly-forecast">
          <h3 className="section-title">Pronóstico Extendido</h3>
          <div className="days-container">
            {dailyForecast.map((day, index) => (
              <div key={index} className="day-card">
                <p className="day-name">
                  {index === 0 ? 'Hoy' : new Date(day.dt * 1000).toLocaleDateString('es-ES', { weekday: 'short' })}
                </p>
                <div className="weather-icon-container small">
                  <img
                    src={`https://openweathermap.org/img/wn/${day.weather[0].icon}.png`}
                    alt={day.weather[0].description}
                    className="weather-icon"
                    onError={(e) => {
                      e.target.style.display = 'none';
                      e.target.nextSibling.style.display = 'block';
                    }}
                    style={{ 
                      filter: 'brightness(1.3) saturate(1.4) hue-rotate(-10deg)' 
                    }}
                  />
                  <div className="weather-icon-fallback" style={{display: 'none'}}>
                    {day.weather[0].icon.includes('01') ? '☀️' : '🌈'}
                  </div>
                </div>
                <div className="temperature-range">
                  <span className="temp-max">{Math.round(day.temp_max)}°</span>
                  <span className="temp-min">{Math.round(day.temp_min)}°</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {}
      <div className="static-cities-section">
        <h3 className="section-title">Ciudades del Mundo</h3>
        <div className="static-cities-grid">
          {staticCities.map((city, index) => (
            <StaticCityCard
              key={city.id}
              cityData={city}
              bgImage={staticCityConfig[index].image}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

export default WeatherWidget;