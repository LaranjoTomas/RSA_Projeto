import React from 'react';

const ConnectionStatus = ({ isConnected, lastUpdate }) => (
    <div className={`connection-status flex items-center ${isConnected ? 'text-green-600' : 'text-red-600'}`}>
        <div className={`w-3 h-3 rounded-full mr-2 ${isConnected ? 'bg-green-600' : 'bg-red-600'}`}></div>
        <span className="text-sm">
            {isConnected ? 'Conectado ao servidor' : 'Desconectado do servidor'}
            {lastUpdate && isConnected && (
                <span className="text-gray-500 ml-2">({new Date(lastUpdate).toLocaleTimeString()})</span>
            )}
        </span>
    </div>
);

export default ConnectionStatus;
