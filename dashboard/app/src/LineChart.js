import React, { useEffect, useRef } from 'react';
import Chart from 'chart.js/auto';

const LineChart = ({ data, label, color }) => {
    const chartRef = useRef(null);
    const chartInstance = useRef(null);

    useEffect(() => {
        if (chartInstance.current) chartInstance.current.destroy();

        const ctx = chartRef.current.getContext('2d');
        chartInstance.current = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.map((_, i) => i),
                datasets: [{
                    label, data,
                    borderColor: color,
                    backgroundColor: color + '20',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                animation: false,
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { x: { display: false }, y: { beginAtZero: false } }
            }
        });

        return () => chartInstance.current.destroy();
    }, [data, color, label]);

    return <div className="h-32"><canvas ref={chartRef}></canvas></div>;
};

export default LineChart;
