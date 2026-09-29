import { ChartConfiguration } from 'chart.js';

import { formatDuration } from '../format';

export interface HrSpeedPoint {
  t: number;
  hr: number | null;
  speed_kmh: number;
}

export function hrSpeedChart(points: HrSpeedPoint[]): ChartConfiguration {
  return {
    type: 'line',
    data: {
      labels: points.map((point) => formatDuration(point.t)),
      datasets: [
        {
          label: 'HR',
          data: points.map((point) => point.hr),
          borderColor: '#f43f5e',
          yAxisID: 'hr',
          tension: 0.25,
          pointRadius: 0,
        },
        {
          label: 'Speed',
          data: points.map((point) => point.speed_kmh),
          borderColor: '#4f46e5',
          yAxisID: 'speed',
          tension: 0.25,
          pointRadius: 0,
        },
      ],
    },
    options: {
      animation: false,
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      scales: {
        hr: { position: 'left', title: { display: true, text: 'HR' } },
        speed: { position: 'right', title: { display: true, text: 'km/h' }, grid: { drawOnChartArea: false } },
      },
    },
  };
}
