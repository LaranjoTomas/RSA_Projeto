import React from 'react';

const Recommendation = ({ icon, title, description, color }) => (
    <div className={`recommendation-card bg-white p-4 rounded-lg shadow-md border-l-4 ${color}`}>
        <div className="flex items-center mb-2">
            <div className={`text-2xl mr-3 ${color.replace('border-', 'text-')}`}>{icon}</div>
            <h3 className="font-medium">{title}</h3>
        </div>
        <p className="text-gray-600 text-sm">{description}</p>
    </div>
);

export default Recommendation;
