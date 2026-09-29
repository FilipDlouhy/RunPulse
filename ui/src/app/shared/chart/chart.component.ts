import { Component, ElementRef, OnDestroy, effect, input, viewChild } from '@angular/core';
import {
  BarController,
  BarElement,
  CategoryScale,
  Chart,
  ChartConfiguration,
  Legend,
  LineController,
  LineElement,
  LinearScale,
  PointElement,
  Tooltip,
} from 'chart.js';

Chart.register(
  BarController,
  BarElement,
  CategoryScale,
  Legend,
  LineController,
  LineElement,
  LinearScale,
  PointElement,
  Tooltip,
);

@Component({
  selector: 'app-chart',
  template: '<canvas #canvas></canvas>',
  styles: `
    :host {
      position: relative;
      display: block;
      width: 100%;
      height: 100%;
    }

    canvas {
      width: 100%;
      height: 100%;
    }
  `,
})
export class ChartComponent implements OnDestroy {
  private readonly canvasRef = viewChild.required<ElementRef<HTMLCanvasElement>>('canvas');

  readonly config = input.required<ChartConfiguration>();

  private chart?: Chart;

  constructor() {
    effect(() => {
      const config = this.config();
      const canvas = this.canvasRef().nativeElement;
      if (this.chart) {
        this.chart.data = config.data;
        this.chart.options = config.options ?? {};
        this.chart.update();
      } else {
        this.chart = new Chart(canvas, config);
      }
    });
  }

  ngOnDestroy(): void {
    this.chart?.destroy();
  }
}
