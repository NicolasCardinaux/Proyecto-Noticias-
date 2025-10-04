import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import '../styles/MundoInversion.css';
import InversionFondo from '../imagenes/inversion.jpg';

// ... (Mapas y configuraciones no cambian) ...
const STOCK_MAP = {
  '^GSPC': { name: 'S&P 500' },
  '^DJI': { name: 'Dow Jones Industrial Average' },
  '^IXIC': { name: 'NASDAQ Composite' },
  'AAPL': { name: 'Apple Inc.' },
  'GOOGL': { name: 'Alphabet Inc. (Google)' },
  'MSFT': { name: 'Microsoft Corporation' },
  'AMZN': { name: 'Amazon.com, Inc.' },
  'TSLA': { name: 'Tesla, Inc.' },
  'NVDA': { name: 'NVIDIA Corp.' },
  'META': { name: 'Meta Platforms Inc.' },
  'TSM': { name: 'Taiwan Semiconductor' },
  'BRK-A': { name: 'Berkshire Hathaway Inc.' },
  'V': { name: 'Visa Inc.' },
  'JPM': { name: 'JPMorgan Chase & Co.' },
};

const CURRENCY_MAP = {
  'USD': { name: 'Dólar Estadounidense', symbol: '$' },
  'EUR': { name: 'Euro', symbol: '€' },
  'BRL': { name: 'Real Brasileño', symbol: 'R$' },
  'GBP': { name: 'Libra Esterlina', symbol: '£' },
  'JPY': { name: 'Yen Japonés', symbol: '¥' },
  'AUD': { name: 'Dólar Australiano', symbol: 'A$' },
  'CAD': { name: 'Dólar Canadiense', symbol: 'C$' },
  'CHF': { name: 'Franco Suizo', symbol: 'CHF' },
  'CNY': { name: 'Yuan Chino', symbol: '¥' },
  'INR': { name: 'Rupia India', symbol: '₹' },
  'NZD': { name: 'Dólar Neozelandés', symbol: 'NZ$' },
  'SEK': { name: 'Corona Sueca', symbol: 'kr' },
  'MXN': { name: 'Peso Mexicano', symbol: '$' },
  'ARS': { name: 'Peso Argentino', symbol: '$' },
  'CLP': { name: 'Peso Chileno', symbol: '$' },
  'COP': { name: 'Peso Colombiano', symbol: '$' },
  'KRW': { name: 'Won Surcoreano', symbol: '₩' },
  'ZAR': { name: 'Rand Sudafricano', symbol: 'R' },
};

const SECTIONS = ['Divisas', 'Acciones', 'Criptomonedas'];
const DISPLAY_CURRENCIES = Object.keys(CURRENCY_MAP);
const STOCK_SYMBOLS = Object.keys(STOCK_MAP);
const CRYPTO_COUNT = 25;

function MundoInversion() {
  const [data, setData] = useState({ forex: null, stocks: null, crypto: null });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const scrollRef = useRef(null);

  const [localCurrencyCode, setLocalCurrencyCode] = useState('USD');
  const [usdToLocalRate, setUsdToLocalRate] = useState(1);

  useEffect(() => {
    const fetchAllData = async () => {
      setLoading(true);
      setError(null);

      const CACHE_KEY = "investmentData";
      const CACHE_DURATION = 2 * 60 * 60 * 1000; // 2 horas en milisegundos

      const cachedData = localStorage.getItem(CACHE_KEY);
      if (cachedData) {
        const { data: cached, timestamp } = JSON.parse(cachedData);
        if (Date.now() - timestamp < CACHE_DURATION) {
          setData(cached);
          // Restaurar la moneda local del caché
          setLocalCurrencyCode(cached.forex.base);
          const localRateFromCache = cached.forex.rates.find(r => r.code === cached.forex.base)?.rate || 1;
          setUsdToLocalRate(localRateFromCache);
          setLoading(false);
          return;
        }
      }

      try {
        let localCurrency = 'USD';
        let localRate = 1;

        const cachedLocation = localStorage.getItem("userLocation");
        if (cachedLocation) {
          const { currency, timestamp } = JSON.parse(cachedLocation);
          const now = Date.now();
          if (now - timestamp < 30 * 24 * 60 * 60 * 1000 && currency) {
            localCurrency = currency;
          } else {
            const ipRes = await axios.get("https://ipwho.is/");
            localCurrency = ipRes.data.currency?.code || 'USD';
            localStorage.setItem("userLocation", JSON.stringify({ ...ipRes.data, currency: localCurrency, timestamp: Date.now() }));
          }
        } else {
          const ipRes = await axios.get("https://ipwho.is/");
          localCurrency = ipRes.data.currency?.code || 'USD';
          localStorage.setItem("userLocation", JSON.stringify({ ...ipRes.data, currency: localCurrency, timestamp: Date.now() }));
        }

        setLocalCurrencyCode(localCurrency);

        const [forexRes, cryptoRes] = await Promise.all([
          axios.get(`https://api.exchangerate-api.com/v4/latest/USD`),
          axios.get(`https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=${CRYPTO_COUNT}&page=1&sparkline=false`),
        ]);

        localRate = forexRes.data.rates[localCurrency] || 1;
        setUsdToLocalRate(localRate);

        const processedForex = DISPLAY_CURRENCIES
          .filter((currency) => forexRes.data.rates[currency])
          .map((currency) => ({
            code: currency,
            rate: forexRes.data.rates[localCurrency] / forexRes.data.rates[currency],
            ...CURRENCY_MAP[currency],
          }));

        const mockStocks = STOCK_SYMBOLS.map((symbol) => ({
          symbol,
          name: STOCK_MAP[symbol].name,
          price: Math.random() * (symbol.startsWith('^') ? 4000 : 300) + 100,
          change: Math.random() * 20 - 10,
          changePercent: Math.random() * 2 - 1,
        }));

        const newData = {
          forex: { base: localCurrency, rates: processedForex },
          stocks: mockStocks,
          crypto: cryptoRes.data,
        };

        setData(newData);
        localStorage.setItem(CACHE_KEY, JSON.stringify({ data: newData, timestamp: Date.now() }));

      } catch (err) {
        console.error("Error fetching investment data:", err);
        setError("No se pudieron cargar los datos de inversión.");
      } finally {
        setLoading(false);
      }
    };

    fetchAllData();
  }, []);

  // ... (El resto del código no cambia) ...
  useEffect(() => {
    const handleScroll = () => {
      if (scrollRef.current) {
        const { scrollLeft, clientWidth } = scrollRef.current;
        const index = Math.round(scrollLeft / clientWidth);
        if (index !== currentIndex) setCurrentIndex(index);
      }
    };
    const scrollContainer = scrollRef.current;
    scrollContainer?.addEventListener('scroll', handleScroll, { passive: true });
    return () => scrollContainer?.removeEventListener('scroll', handleScroll);
  }, [currentIndex]);

  const scroll = (direction) => {
    if (scrollRef.current) {
      const { clientWidth } = scrollRef.current;
      const newIndex =
        direction === 'left'
          ? Math.max(currentIndex - 1, 0)
          : Math.min(currentIndex + 1, SECTIONS.length - 1);

      scrollRef.current.scrollTo({ left: newIndex * clientWidth, behavior: 'smooth' });
      setCurrentIndex(newIndex);
    }
  };

  const formatCurrency = (value, currency = 'USD', decimals = 2) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency,
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    }).format(value);
  };

  const formatLocalNumber = (value, decimals = 4) => {
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    }).format(value);
  };

  return (
    <div className="mi-widget-container">
      <div className="mi-background" style={{ backgroundImage: `url(${InversionFondo})` }}></div>
      <div className="container mx-auto px-4 py-8 relative z-10">
        <div className="mi-header">
          <h2 className="mi-title">Mundo Inversión</h2>
          <div className="mi-title-underline"></div>
          <div className="mi-nav-buttons">
            <button onClick={() => scroll('left')} className="mi-nav-button">&lt;</button>
            <button onClick={() => scroll('right')} className="mi-nav-button">&gt;</button>
          </div>
        </div>

        {!loading && !error && (
          <h3 className="mi-section-title">{SECTIONS[currentIndex]}</h3>
        )}

        {loading && <p className="mi-message">Cargando datos de mercados...</p>}
        {error && <p className="mi-message error">{error}</p>}

        {!loading && !error && (
          <div className="mi-carousel-container" ref={scrollRef}>
            {/* --- SECCIÓN DIVISAS --- */}
            <div className="mi-slide">
              <div className="mi-card">
                <h3 className="mi-card-title">Tasas de Cambio de Referencia</h3>
                <div className="mi-card-list">
                  {data.forex?.rates.map((c) => (
                    <div key={c.code} className="mi-list-item">
                      <div className="mi-item-name">
                        <span className="mi-item-symbol currency">{c.symbol}</span>
                        <span>{c.name}</span>
                      </div>
                      <span className="mi-item-value">
                        1 {c.code} → {formatLocalNumber(c.rate, 4)} {localCurrencyCode}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* --- SECCIÓN ACCIONES --- */}
            <div className="mi-slide">
              <div className="mi-card">
                <h3 className="mi-card-title">Principales Índices y Acciones</h3>
                <div className="mi-card-list">
                  {data.stocks?.map((stock) => (
                    <div key={stock.symbol} className="mi-list-item">
                      <div className="mi-item-name">
                        <span className="mi-item-symbol stock">{stock.symbol}</span>
                        <span>{stock.name}</span>
                      </div>
                      <div className="mi-item-details">
                        <span className="mi-item-value">{formatCurrency(stock.price)}</span>
                        <span className={stock.change >= 0 ? 'price-up' : 'price-down'}>
                          {stock.change >= 0 ? '+' : ''}{stock.change.toFixed(2)} ({stock.changePercent.toFixed(2)}%)
                        </span>
                        {localCurrencyCode !== 'USD' && usdToLocalRate !== 1 && (
                          <span className="mi-local-conversion">
                            ({formatLocalNumber(stock.price * usdToLocalRate, 2)} {localCurrencyCode})
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* --- SECCIÓN CRIPTOMONEDAS --- */}
            <div className="mi-slide">
              <div className="mi-card">
                <h3 className="mi-card-title">Top Criptomonedas</h3>
                <div className="mi-card-list">
                  {data.crypto?.map((c) => (
                    <div key={c.id} className="mi-list-item">
                      <div className="mi-item-name">
                        <img src={c.image} alt={c.name} className="mi-crypto-icon" />
                        <span>{c.name} ({c.symbol.toUpperCase()})</span>
                      </div>
                      <div className="mi-item-details">
                        <span className="mi-item-value">{formatCurrency(c.current_price)}</span>
                        <span className={c.price_change_percentage_24h >= 0 ? 'price-up' : 'price-down'}>
                          {c.price_change_percentage_24h.toFixed(2)}%
                        </span>
                        {localCurrencyCode !== 'USD' && usdToLocalRate !== 1 && (
                          <span className="mi-local-conversion">
                            ({formatLocalNumber(c.current_price * usdToLocalRate, 2)} {localCurrencyCode})
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default MundoInversion;