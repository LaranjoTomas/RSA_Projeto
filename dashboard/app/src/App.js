import React, { useState, useEffect } from 'react';
import Gauge from './Gauge';
import LineChart from './LineChart';
import Recommendation from './Recommendation';
import ConnectionStatus from './ConnectionStatus';
import ServerConfig from './ServerConfig';

export default function App() {
  const [serverUrl, setServerUrl] = useState('http://192.168.128.169:3000/data');
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [error, setError] = useState(null);
  const [intervalId, setIntervalId] = useState(null);
  const [temperature, setTemperature] = useState(null);
  const [humidity, setHumidity] = useState(null);
  const [pressure, setPressure] = useState(null);
  const [tempHistory, setTempHistory] = useState([]);
  const [humHistory, setHumHistory] = useState([]);
  const [presHistory, setPresHistory] = useState([]);

  const fetchData = async () => {
    try {
      const res = await fetch(serverUrl);
      if (!res.ok) throw new Error(`Status ${res.status}`);
      const data = await res.json();

      // setTemperature(+data.temperature.toFixed(1));
      // setHumidity(+data.humidity.toFixed(1));
      // setPressure(+data.pressure.toFixed(1));
      // setTempHistory(prev => [...prev.slice(-19), +data.temperature.toFixed(1)]);
      // setHumHistory(prev => [...prev.slice(-19), +data.humidity.toFixed(1)]);
      // setPresHistory(prev => [...prev.slice(-19), +data.pressure.toFixed(1)]);

      setTemperature(+data.bme_temperature.toFixed(1));
      setHumidity(+data.bme_humidity.toFixed(1));
      setPressure(+data.bme_pressure.toFixed(1));
      setTempHistory(prev => [...prev.slice(-19), +data.bme_temperature.toFixed(1)]);
      setHumHistory(prev => [...prev.slice(-19), +data.bme_humidity.toFixed(1)]);
      setPresHistory(prev => [...prev.slice(-19), +data.bme_pressure.toFixed(1)]);

      setLastUpdate(Date.now());
      setIsConnected(true);
      setError(null);
    } catch (e) {
      setIsConnected(false);
      setError(e.message);
    }
  };

  const connectToServer = () => {
    if (intervalId) clearInterval(intervalId);
    fetchData();
    const id = setInterval(fetchData, 200);
    setIntervalId(id);
  };

  useEffect(() => {
    return () => intervalId && clearInterval(intervalId);
  }, [intervalId]);

  // helpers de cor
  const getTempColor = t =>
    t === null
      ? '#9ca3af'
      : t > 28
        ? '#ef4444'
        : t > 25
          ? '#f97316'
          : t < 19
            ? '#3b82f6'
            : '#10b981';
  const getHumColor = h =>
    h === null ? '#9ca3af' : h > 70 ? '#3b82f6' : h < 30 ? '#f97316' : '#10b981';
  const getPresColor = p =>
    p === null ? '#9ca3af' : p < 1000 ? '#8b5cf6' : p > 1025 ? '#f97316' : '#10b981';

  // faz as recomendações
  const getRecommendations = () => {
    if (tempHistory.length === 0 || humHistory.length === 0 || presHistory.length === 0) {
      return [];
    }
    const recs = [];
    if (temperature > 26)
      recs.push({
        icon: '❄️',
        title: 'Ligar Ar Condicionado',
        description: 'Temperatura alta.',
        color: 'border-blue-500'
      });
    else if (temperature < 20)
      recs.push({
        icon: '🔥',
        title: 'Ligar Aquecedor',
        description: 'Temperatura baixa.',
        color: 'border-red-500'
      });

    if (humidity > 70)
      recs.push({
        icon: '💧',
        title: 'Ambiente Úmido',
        description: 'Umidade alta.',
        color: 'border-blue-400'
      });
    else if (humidity < 30)
      recs.push({
        icon: '🏜️',
        title: 'Ambiente Seco',
        description: 'Umidade baixa.',
        color: 'border-yellow-500'
      });

    if (pressure < 1000)
      recs.push({
        icon: '🌧️',
        title: 'Possibilidade de Chuva',
        description: 'Pressão baixa.',
        color: 'border-gray-500'
      });

    if (!recs.length)
      recs.push({
        icon: '✅',
        title: 'Condições Ideais',
        description: 'Tudo ok.',
        color: 'border-green-500'
      });

    return recs;
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <header className="mb-6">
        <h1 className="text-3xl font-bold text-gray-800">Dashboard</h1>
        <p className="text-gray-600">Monitoramento em tempo real</p>
        {error && <p className="text-red-600 mt-2">Erro: {error}</p>}
        <ConnectionStatus isConnected={isConnected} lastUpdate={lastUpdate} />
      </header>

      <ServerConfig
        serverUrl={serverUrl}
        onServerUrlChange={setServerUrl}
        onConnect={connectToServer}
      />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-xl shadow-md p-6">
          <Gauge
            value={temperature}
            min={15}
            max={35}
            unit="°C"
            title="Temperatura"
            color={getTempColor(temperature)}
          />
          <div className="mt-4">
            {tempHistory.length > 0 ? (
              <LineChart
                data={tempHistory}
                label="Temperatura"
                color={getTempColor(temperature)}
              />
            ) : (
              <div className="h-32 flex items-center justify-center text-gray-500">
                Sem dados históricos
              </div>
            )}
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-md p-6">
          <Gauge
            value={humidity}
            min={0}
            max={100}
            unit="%"
            title="Umidade"
            color={getHumColor(humidity)}
          />
          <div className="mt-4">
            {humHistory.length > 0 ? (
              <LineChart
                data={humHistory}
                label="Umidade"
                color={getHumColor(humidity)}
              />
            ) : (
              <div className="h-32 flex items-center justify-center text-gray-500">
                Sem dados históricos
              </div>
            )}
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-md p-6">
          <Gauge
            value={pressure}
            min={990}
            max={1030}
            unit="hPa"
            title="Pressão"
            color={getPresColor(pressure)}
          />
          <div className="mt-4">
            {presHistory.length > 0 ? (
              <LineChart
                data={presHistory}
                label="Pressão"
                color={getPresColor(pressure)}
              />
            ) : (
              <div className="h-32 flex items-center justify-center text-gray-500">
                Sem dados históricos
              </div>
            )}
          </div>
        </div>
      </div>

      <section className="mb-8">
        <h2 className="text-2xl font-semibold text-gray-800 mb-4">Recomendações</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {getRecommendations().map((rec, i) => (
            <Recommendation key={i} {...rec} />
          ))}
        </div>
      </section>

      <footer className="mt-8 text-center text-gray-500 text-sm">
        Dashboard - Conectado a um servidor local
      </footer>
    </div>
  );
}
