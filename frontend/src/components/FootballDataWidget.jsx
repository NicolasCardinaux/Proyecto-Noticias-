import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import '../styles/FootballDataWidget.css';
import FutbolFondo from '../imagenes/futbol.jpg';

const leagues = [
  { name: 'Premier League', id: '4328' },
  { name: 'La Liga', id: '4335' },
  { name: 'Champions League', id: '4480' },
  { name: 'Serie A', id: '4332' },
];

const getLocalDateTime = (dateStr, timeStr) => {
  if (!dateStr || !timeStr) return null;
  const utcDate = new Date(`${dateStr}T${timeStr}Z`);
  return utcDate;
};

function FootballDataWidget() {
  const [leaguesData, setLeaguesData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentLeagueIndex, setCurrentLeagueIndex] = useState(0);
  const scrollRef = useRef(null);

  useEffect(() => {
    const fetchAllLeaguesDataSequentially = async () => {
      setLoading(true);
      setError(null);
      const CACHE_KEY = "footballData";
      const CACHE_DURATION = 2 * 60 * 60 * 1000; 

      const cachedData = localStorage.getItem(CACHE_KEY);
      if (cachedData) {
        const { data: cached, timestamp } = JSON.parse(cachedData);
        if (Date.now() - timestamp < CACHE_DURATION) {
          setLeaguesData(cached);
          setLoading(false);
          return; 
        }
      }

      const API_KEY = '3';
      const allData = [];

      try {
        for (const league of leagues) {
          const seasonScheduleEndpoint = `https://www.thesportsdb.com/api/v1/json/${API_KEY}/eventsseason.php?id=${league.id}&s=2025-2026`;
          const scheduleRes = await axios.get(seasonScheduleEndpoint);
          const allEvents = scheduleRes.data.events || [];

          const today = new Date();

          const nextMatches = allEvents
            .filter((e) => new Date(e.dateEvent) >= today)
            .sort((a, b) => new Date(a.dateEvent) - new Date(b.dateEvent))
            .slice(0, 10);

          const lastResults = allEvents
            .filter((e) => new Date(e.dateEvent) < today && e.intHomeScore !== null && e.intAwayScore !== null)
            .sort((a, b) => new Date(b.dateEvent) - new Date(a.dateEvent))
            .slice(0, 10);

          allData.push({
            leagueName: league.name,
            nextMatches,
            lastResults,
            seasonSchedule: allEvents,
          });
        }

        setLeaguesData(allData);

        localStorage.setItem(CACHE_KEY, JSON.stringify({ data: allData, timestamp: Date.now() }));

      } catch (err) {
        console.error(`Failed to fetch data:`, err);
        setError("No se pudieron cargar los datos de fútbol.");
      } finally {
        setLoading(false);
      }
    };

    fetchAllLeaguesDataSequentially();
  }, []);



  useEffect(() => {
    const handleScroll = () => {
      if (scrollRef.current) {
        const { scrollLeft, clientWidth } = scrollRef.current;
        const index = Math.round(scrollLeft / clientWidth);
        if (index !== currentLeagueIndex) {
          setCurrentLeagueIndex(index);
        }
      }
    };

    const scrollContainer = scrollRef.current;
    if (scrollContainer) {
      scrollContainer.addEventListener('scroll', handleScroll, { passive: true });
    }

    return () => {
      if (scrollContainer) {
        scrollContainer.removeEventListener('scroll', handleScroll);
      }
    };
  }, [currentLeagueIndex]);

  const scroll = (direction) => {
    if (scrollRef.current) {
      const { clientWidth } = scrollRef.current;
      const newIndex = direction === 'left'
        ? Math.max(currentLeagueIndex - 1, 0)
        : Math.min(currentLeagueIndex + 1, leaguesData.length - 1);

      scrollRef.current.scrollTo({
        left: newIndex * clientWidth,
        behavior: 'smooth',
      });

      setCurrentLeagueIndex(newIndex);
    }
  };

  const renderEventName = (eventName) => {
    const parts = eventName.split(/ vs /i);
    if (parts.length === 2) {
      return (
        <span className="event-name">
          {parts[0]} <strong className="versus-text">vs</strong> {parts[1]}
        </span>
      );
    }
    return <span className="event-name">{eventName}</span>;
  };

  return (
    <div className="football-widget-container">
      <div className="football-background" style={{ backgroundImage: `url(${FutbolFondo})` }}></div>
      <div className="container mx-auto px-4 py-8 relative z-10">
        <div className="flex flex-col items-center mb-8 relative">
          <h2 className="relative z-10 text-3xl md:text-4xl font-bold text-white uppercase tracking-widest text-3d-football">
            Mundo Fútbol
          </h2>
          <div className="mt-3 h-1 w-32 bg-gradient-to-r from-transparent via-[#b3000c] to-transparent"></div>
          <div className="football-nav-buttons">
            <button onClick={() => scroll('left')} className="football-nav-button">&lt;</button>
            <button onClick={() => scroll('right')} className="football-nav-button">&gt;</button>
          </div>
        </div>

        {!loading && !error && leaguesData[currentLeagueIndex] && (
          <h3 className="current-league-title">
            {leaguesData[currentLeagueIndex].leagueName}
          </h3>
        )}

        {loading && <p className="text-center text-white text-xl p-10">Cargando datos de ligas...</p>}
        {error && <p className="text-center text-[#b3000c] text-xl font-bold p-10">{error}</p>}

        {!loading && !error && (
          <div className="widget-carousel-container" ref={scrollRef}>
            {leaguesData.map((league, index) => (
              <div key={league.leagueName} className="league-slide">
                <div className="widget-card">
                  <h3 className="card-title">Próximos Partidos</h3>
                  <div className="card-list-wrapper">
                    {league.nextMatches.length > 0 ? (
                      league.nextMatches.map((m) => (
                        <div key={m.idEvent} className="list-item match-item">
                          <div className="match-teams-container">
                            <span className="team-name home">{m.strHomeTeam}</span>
                            <strong className="versus-text">vs</strong>
                            <span className="team-name away">{m.strAwayTeam}</span>
                          </div>
                          <div className="item-details-box">
                            {(() => {
                              const localDate = getLocalDateTime(m.dateEvent, m.strTime);
                              return localDate
                                ? `${localDate.toLocaleDateString('es-ES', { day: '2-digit', month: 'short' })} - ${localDate.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })}hs`
                                : 'Horario no disponible';
                            })()}
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="list-item-empty">No hay próximos partidos</div>
                    )}
                  </div>
                </div>

                <div className="widget-card">
                  <h3 className="card-title">Resultados Recientes</h3>
                  <div className="card-list-wrapper">
                    {league.lastResults.length > 0 ? (
                      league.lastResults.map((r) => (
                        <div key={r.idEvent} className="list-item result-item">
                          <span className="team-name home">{r.strHomeTeam}</span>
                          <span className="score">{r.intHomeScore} - {r.intAwayScore}</span>
                          <span className="team-name away">{r.strAwayTeam}</span>
                        </div>
                      ))
                    ) : (
                      <div className="list-item-empty">No hay resultados recientes</div>
                    )}
                  </div>
                </div>

                <div className="widget-card">
                  <h3 className="card-title">Calendario {league.leagueName}</h3>
                  <div className="card-list-wrapper">
                    {league.seasonSchedule.length > 0 ? (
                      league.seasonSchedule.map((e) => (
                        <div key={e.idEvent} className="list-item calendar-item">
                          {renderEventName(e.strEvent)}
                          <span className="item-details-box small">
                            {(() => {
                              const localDate = getLocalDateTime(e.dateEvent, e.strTime);
                              return localDate
                                ? localDate.toLocaleDateString('es-ES', {
                                    day: '2-digit',
                                    month: 'short',
                                    year: '2-digit',
                                  })
                                : 'Fecha no disponible';
                            })()}
                          </span>
                        </div>
                      ))
                    ) : (
                      <div className="list-item-empty">No hay datos para la temporada 2025/26</div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default FootballDataWidget;