import React from 'react';

const ServerConfig = ({ serverUrl, onServerUrlChange, onConnect }) => (
    <div className="bg-white rounded-xl shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">Configuração do Servidor</h2>
        <div className="flex flex-col md:flex-row gap-4">
            <input
                type="text"
                value={serverUrl}
                onChange={e => onServerUrlChange(e.target.value)}
                placeholder="URL do servidor (ex: http://192.168.128.169:3000/data)"
                className="flex-grow px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
                onClick={onConnect}
                className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
                Conectar
            </button>
        </div>
    </div>
);

export default ServerConfig;
