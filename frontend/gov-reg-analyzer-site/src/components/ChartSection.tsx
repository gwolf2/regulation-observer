import { Bar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ChartOptions,
  Scale,
  CoreScaleOptions,
} from "chart.js";

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

interface AgencyData {
  year: number;
  wordCount: number;
  avgSentenceLength: number;
  restrictiveness: number;
  sentiment: number;
}

interface Agency {
  agency: string;
  data: AgencyData[];
}

interface ChartSectionProps {
  agencies: Agency[];
}

function ChartSection({ agencies }: ChartSectionProps) {
  const years = [2024, 2025];
  const colors = ["#FFD700", "#A9A9A9", "#808080", "#DAA520", "#696969"];

  const createChartData = (metric: keyof AgencyData) => ({
    labels: years,
    datasets: agencies.map((agency, index) => ({
      label: agency.agency,
      data: agency.data
        .filter((d) => years.includes(d.year))
        .map((d) => (metric === "wordCount" ? d[metric] / 1_000_000 : d[metric])),
      backgroundColor: colors[index % colors.length],
      borderColor: colors[index % colors.length],
      borderWidth: 1,
    })),
  });

  const options: ChartOptions<"bar"> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: "bottom",
        align: "center",
        labels: {
          boxWidth: 12,
          boxHeight: 12,
          padding: 20,
          font: {
            size: 12,
            family: "'Roboto', sans-serif",
            weight: "bold",
          },
          color: "#d1d5db",
          usePointStyle: true,
          pointStyle: "rect",
        },
        onHover: (event: any) => {
          event.native.target.style.cursor = "pointer";
        },
        onLeave: (event: any) => {
          event.native.target.style.cursor = "default";
        },
      },
      tooltip: {
        mode: "nearest",
        intersect: true,
        backgroundColor: "rgba(31, 41, 55, 0.9)",
        titleFont: { family: "'Roboto', sans-serif", size: 12 },
        bodyFont: { family: "'Roboto', sans-serif", size: 12 },
        padding: 8,
        callbacks: {
          label: (context) => {
            const value = context.raw as number;
            const metric = context.dataset.label === "Word Count" ? " million words" : "";
            return `${context.dataset.label}: ${value.toLocaleString(undefined, {
              minimumFractionDigits: metric === "" ? 2 : 0,
              maximumFractionDigits: metric === "" ? 2 : 0,
            })}${metric}`;
          },
        },
      },
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: {
          font: { family: "'Roboto', sans-serif", size: 12 },
          color: "#9ca3af",
        },
      },
      y: {
        grid: { color: "rgba(255, 255, 255, 0.05)" },
        ticks: {
          font: {
            family: "'Roboto', sans-serif",
            size: 12,
            weight: "normal",
          },
          color: "#9ca3af",
          callback: function (
            this: Scale<CoreScaleOptions>,
            tickValue: string | number
          ): string {
            return Number(tickValue).toLocaleString();
          },
        },
      },
    },
  };

  return (
    <div className="w-full grid grid-cols-1 xl:grid-cols-2 gap-8 py-10">
      <div className="h-[600px] bg-gray-900 p-10 pb-24 rounded-md shadow-md"> {/* Increased h-[550px] to h-[600px], pb-20 to pb-24 */}
        <h2 className="text-base font-semibold mb-2 text-gray-200">Word Count (millions)</h2>
        <p className="text-sm text-gray-400 mb-4">Total words in regulations, in millions.</p>
        <Bar data={createChartData("wordCount")} options={options} />
      </div>
      <div className="h-[600px] bg-gray-900 p-10 pb-24 rounded-md shadow-md">
        <h2 className="text-base font-semibold mb-2 text-gray-200">Average Sentence Length</h2>
        <p className="text-sm text-gray-400 mb-4">Average number of words per sentence; longer sentences may indicate denser, less clear regulations.</p>
        <Bar data={createChartData("avgSentenceLength")} options={options} />
      </div>
      <div className="h-[600px] bg-gray-900 p-10 pb-24 rounded-md shadow-md">
        <h2 className="text-base font-semibold mb-2 text-gray-200">Restrictiveness</h2>
        <p className="text-sm text-gray-400 mb-4">An indicator of regulatory burden (0-1), based on the frequency of words suggesting more actions or obligations for those regulated.</p>
        <Bar data={createChartData("restrictiveness")} options={options} />
      </div>
      <div className="h-[600px] bg-gray-900 p-10 pb-24 rounded-md shadow-md">
        <h2 className="text-base font-semibold mb-2 text-gray-200">Sentiment</h2>
        <p className="text-sm text-gray-400 mb-4">Emotional tone of regulations (-1 to 1), where positive values indicate optimism and negative values indicate pessimism.</p>
        <Bar data={createChartData("sentiment")} options={options} />
      </div>
    </div>
  );
}

export default ChartSection;