import { useState, useMemo } from "react";
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
} from "chart.js";

// Register Chart.js components
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

// Define data interfaces
interface AgencyData {
  year: number;
  wordCount: number;
  avgSentenceLength: number;
  restrictiveness: number;
  sentiment: number;
  fileCount?: number;
}

interface Agency {
  agency: string;
  data: AgencyData[];
}

interface ChartSectionProps {
  agencies: Agency[];
}

// ChartHeader component (moved up before ChartSection)
const ChartHeader = ({
  title,
  description,
  sortDirection,
  setSortDirection,
}: {
  title: string;
  description: string;
  sortDirection: "asc" | "desc";
  setSortDirection: (direction: "asc" | "desc") => void;
}) => (
  <div className="flex flex-col">
    <div className="flex items-center justify-between w-full mb-2">
      <h2
        className="text-base font-semibold text-gray-200 cursor-pointer"
        onClick={() => setSortDirection(sortDirection === "desc" ? "asc" : "desc")}
      >
        {title}
      </h2>
      <span className="text-gray-400 w-4 text-center">
        {sortDirection === "desc" ? "↓" : "↑"}
      </span>
    </div>
    <p className="text-sm text-gray-400">{description}</p>
  </div>
);

function ChartSection({ agencies }: ChartSectionProps) {
  const years: number[] = [2024, 2025];
  const colors = ["#FFD700", "#A9A9A9", "#808080", "#DAA520", "#696969"];

  // Sort states
  const [wordCountSort, setWordCountSort] = useState<"asc" | "desc">("desc");
  const [sentenceLengthSort, setSentenceLengthSort] = useState<"asc" | "desc">("desc");
  const [restrictivenessSort, setRestrictivenessSort] = useState<"asc" | "desc">("desc");
  const [sentimentSort, setSentimentSort] = useState<"asc" | "desc">("desc");

  // Generate chart data with sorting
  const createChartData = (
    metric: keyof Omit<AgencyData, "year" | "fileCount">,
    direction: "asc" | "desc"
  ) => {
    const sortedAgencies = [...agencies].sort((a, b) => {
      const aValue = a.data
        .filter((d) => years.includes(d.year))
        .reduce((sum, d) => sum + (d[metric] || 0), 0);
      const bValue = b.data
        .filter((d) => years.includes(d.year))
        .reduce((sum, d) => sum + (d[metric] || 0), 0);
      return direction === "desc" ? bValue - aValue : aValue - bValue;
    });

    return {
      labels: years.map(String),
      datasets: sortedAgencies.map((agency, index) => ({
        label: agency.agency,
        data: agency.data
          .filter((d) => years.includes(d.year))
          .sort((a, b) => a.year - b.year)
          .map((d) => (metric === "wordCount" ? d[metric] / 1_000_000 : d[metric])),
        backgroundColor: colors[index % colors.length],
        borderColor: colors[index % colors.length],
        borderWidth: 1,
      })),
    };
  };

  // Chart configuration
  const chartOptions: ChartOptions<"bar"> = {
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
          font: { size: 12, family: "'Roboto', sans-serif", weight: "bold" },
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
            const metricUnit = context.dataset.label === "Word Count" ? " million words" : "";
            return `${context.dataset.label}: ${value.toLocaleString(undefined, {
              minimumFractionDigits: metricUnit === "" ? 2 : 0,
              maximumFractionDigits: metricUnit === "" ? 2 : 0,
            })}${metricUnit}`;
          },
        },
      },
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: { font: { family: "'Roboto', sans-serif", size: 12 }, color: "#9ca3af" },
      },
      y: {
        grid: { color: "rgba(255, 255, 255, 0.05)" },
        ticks: {
          font: { family: "'Roboto', sans-serif", size: 12, weight: "normal" },
          color: "#9ca3af",
          callback: (tickValue: string | number) => Number(tickValue).toLocaleString(),
        },
      },
    },
  };

  // Memoized chart data
  const wordCountData = useMemo(
    () => createChartData("wordCount", wordCountSort),
    [wordCountSort, agencies]
  );
  const avgSentenceLengthData = useMemo(
    () => createChartData("avgSentenceLength", sentenceLengthSort),
    [sentenceLengthSort, agencies]
  );
  const restrictivenessData = useMemo(
    () => createChartData("restrictiveness", restrictivenessSort),
    [restrictivenessSort, agencies]
  );
  const sentimentData = useMemo(
    () => createChartData("sentiment", sentimentSort),
    [sentimentSort, agencies]
  );

  return (
    <div className="w-full grid grid-cols-1 xl:grid-cols-2 gap-8 py-10">
      <div className="h-[600px] bg-gray-900 p-10 pb-24 rounded-md shadow-md">
        <ChartHeader
          title="Word Count (millions)"
          description="Total words in regulations, in millions."
          sortDirection={wordCountSort}
          setSortDirection={setWordCountSort}
        />
        <Bar data={wordCountData} options={chartOptions} />
      </div>
      <div className="h-[600px] bg-gray-900 p-10 pb-24 rounded-md shadow-md">
        <ChartHeader
          title="Average Sentence Length"
          description="Average number of words per sentence; longer sentences may indicate denser regulations."
          sortDirection={sentenceLengthSort}
          setSortDirection={setSentenceLengthSort}
        />
        <Bar data={avgSentenceLengthData} options={chartOptions} />
      </div>
      <div className="h-[600px] bg-gray-900 p-10 pb-24 rounded-md shadow-md">
        <ChartHeader
          title="Restrictiveness"
          description="An indicator of regulatory burden (0-1), based on the frequency of words suggesting more obligations."
          sortDirection={restrictivenessSort}
          setSortDirection={setRestrictivenessSort}
        />
        <Bar data={restrictivenessData} options={chartOptions} />
      </div>
      <div className="h-[600px] bg-gray-900 p-10 pb-24 rounded-md shadow-md">
        <ChartHeader
          title="Sentiment"
          description="Emotional tone of regulations (-1 to 1), where positive values indicate optimism and negative values indicate pessimism."
          sortDirection={sentimentSort}
          setSortDirection={setSentimentSort}
        />
        <Bar data={sentimentData} options={chartOptions} />
      </div>
    </div>
  );
}

export default ChartSection;