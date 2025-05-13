import React, { useEffect, useRef } from 'react';

const Gauge = ({ value, min, max, unit, title, color }) => {
    const percentage = ((value - min) / (max - min)) * 100;
    const gaugeRef = useRef(null);

    useEffect(() => {
        const ctx = gaugeRef.current.getContext('2d');
        const centerX = 75, centerY = 75, radius = 65;
        ctx.clearRect(0, 0, 150, 150);
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, Math.PI, 2 * Math.PI);
        ctx.lineWidth = 15;
        ctx.strokeStyle = '#e5e7eb';
        ctx.stroke();

        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, Math.PI, Math.PI + (percentage / 100) * Math.PI);
        ctx.lineWidth = 15;
        ctx.strokeStyle = color;
        ctx.stroke();
    }, [value, color, percentage]);

    return (
        <div className="flex flex-col items-center">
            <h3 className="text-lg font-medium text-gray-700 mb-2">{title}</h3>
            <div className="gauge w-[150px] h-[150px]">
                <canvas ref={gaugeRef} width="150" height="150"></canvas>
                <div className="gauge-value text-2xl">
                    {value !== null ? value : '--'}<span className="text-sm ml-1">{unit}</span>
                </div>
            </div>
        </div>
    );
};

export default Gauge;
