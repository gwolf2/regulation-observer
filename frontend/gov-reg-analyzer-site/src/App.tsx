import { useState, useEffect } from "react";
import ChartSection from "./components/ChartSection";
import FilterBar from "./components/FilterBar";
import agenciesData from "./data/agencies.json";
import logo from "./assets/logo.png";

function App() {
  const [selectedAgencies, setSelectedAgencies] = useState<typeof agenciesData>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const agenciesPerPage = 5;

  const filteredAgenciesData = agenciesData.map((agency) => ({
    ...agency,
    data: agency.data.filter((d) => [2024, 2025].includes(d.year)),
  }));

  useEffect(() => {
    const top3 = [...filteredAgenciesData]
      .sort((a, b) => b.data[b.data.length - 1].wordCount - a.data[a.data.length - 1].wordCount)
      .slice(0, 3);
    setSelectedAgencies(top3);
  }, []);

  const agencyOptions = filteredAgenciesData.map((agency) => ({
    label: agency.agency,
    value: agency.agency,
  }));

  const handleFilter = (filterType: string, selected?: string[], metric?: string) => {
    let filtered = [...filteredAgenciesData];
    if (filterType === "top3" && metric) {
      filtered.sort((a, b) => {
        const aValue = a.data[a.data.length - 1][metric as keyof typeof a.data[0]];
        const bValue = b.data[b.data.length - 1][metric as keyof typeof b.data[0]];
        return bValue - aValue;
      });
      filtered = filtered.slice(0, 3);
    } else if (filterType === "bottom3" && metric) {
      filtered.sort((a, b) => {
        const aValue = a.data[a.data.length - 1][metric as keyof typeof a.data[0]];
        const bValue = b.data[b.data.length - 1][metric as keyof typeof b.data[0]];
        return aValue - bValue;
      });
      filtered = filtered.slice(0, 3);
    } else if (filterType === "specific" && selected) {
      filtered = filteredAgenciesData.filter((agency) => selected.includes(agency.agency));
    } else if (filterType === "search" && metric) {
      filtered = filteredAgenciesData.filter((agency) =>
        agency.agency.toLowerCase().includes(metric)
      );
    } else {
      filtered = filteredAgenciesData.slice(0, 3);
    }
    setSelectedAgencies(filtered);
    setCurrentPage(1);
  };

  const TableSection = () => {
    const [sortStates, setSortStates] = useState<{
      [key: string]: { column: string | null; direction: "asc" | "desc" | null };
    }>({
      wordCount: { column: null, direction: null },
      avgSentenceLength: { column: null, direction: null },
      restrictiveness: { column: null, direction: null },
      sentiment: { column: null, direction: null },
    });

    const handleSort = (metric: string, column: string) => {
      setSortStates((prev) => {
        const current = prev[metric];
        const newDirection =
          current.column === column && current.direction === "asc" ? "desc" : "asc";
        return { ...prev, [metric]: { column, direction: newDirection } };
      });
    };

    const getSortedAgencies = (metric: string) => {
      const sortState = sortStates[metric];
      if (!sortState.column || !sortState.direction) return [...filteredAgenciesData];

      const sorted = [...filteredAgenciesData].sort((a, b) => {
        if (sortState.column === "agency") {
          return sortState.direction === "asc"
            ? a.agency.localeCompare(b.agency)
            : b.agency.localeCompare(a.agency);
        }
        const aValue = a.data.find((d) => d.year === Number(sortState.column))?.[
          metric as keyof typeof a.data[0]
        ] || 0;
        const bValue = b.data.find((d) => d.year === Number(sortState.column))?.[
          metric as keyof typeof b.data[0]
        ] || 0;
        return sortState.direction === "asc" ? aValue - bValue : bValue - aValue;
      });
      return sorted;
    };

    const totalAgencies = filteredAgenciesData.length;
    const totalPages = Math.ceil(totalAgencies / agenciesPerPage);
    const startIndex = (currentPage - 1) * agenciesPerPage;
    const paginatedAgencies = getSortedAgencies("wordCount").slice(startIndex, startIndex + agenciesPerPage);

    return (
      <div className="w-full py-10">
        {["wordCount", "avgSentenceLength", "restrictiveness", "sentiment"].map((metric) => (
          <div key={metric} className="mb-10 bg-gray-800 p-6 rounded-md shadow-md">
            <h2 className="text-xl font-bold mb-2 text-gray-200 capitalize">
              {metric === "avgSentenceLength" ? "Average Sentence Length" : metric.replace(/([A-Z])/g, " $1").trim()}
            </h2>
            <p className="text-sm text-gray-400 mb-4">
              {metric === "wordCount" && "Total words in regulations, in millions."}
              {metric === "avgSentenceLength" && "Average number of words per sentence; longer sentences may indicate denser, less clear regulations."}
              {metric === "restrictiveness" && "An indicator of regulatory burden (0-1), based on the frequency of words suggesting more actions or obligations for those regulated."}
              {metric === "sentiment" && "Emotional tone of regulations (-1 to 1), where positive values indicate optimism and negative values indicate pessimism."}
            </p>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-gray-700">
                    <th
                      className="p-4 border-b border-gray-600 text-gray-300 font-medium cursor-pointer hover:bg-gray-600"
                      onClick={() => handleSort(metric, "agency")}
                    >
                      Agency {sortStates[metric].column === "agency" && (sortStates[metric].direction === "asc" ? "↑" : "↓")}
                    </th>
                    {[2024, 2025].map((year) => (
                      <th
                        key={year}
                        className="p-4 border-b border-gray-600 text-gray-300 font-medium cursor-pointer hover:bg-gray-600"
                        onClick={() => handleSort(metric, year.toString())}
                      >
                        {year} {sortStates[metric].column === year.toString() && (sortStates[metric].direction === "asc" ? "↑" : "↓")}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {paginatedAgencies.map((agency) => (
                    <tr key={agency.agency} className="hover:bg-gray-700">
                      <td className="p-4 border-b border-gray-600 text-gray-200">{agency.agency}</td>
                      {agency.data.map((d) => (
                        <td key={d.year} className="p-4 border-b border-gray-600 text-gray-200">
                          {metric === "wordCount"
                            ? (d[metric] / 1_000_000).toLocaleString(undefined, { maximumFractionDigits: 2 })
                            : d[metric as keyof typeof d].toLocaleString(undefined, {
                                minimumFractionDigits: metric === "wordCount" ? 0 : 2,
                                maximumFractionDigits: metric === "wordCount" ? 0 : 2,
                              })}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="flex justify-between mt-4">
              <button
                onClick={() => setCurrentPage((prev) => Math.max(prev - 1, 1))}
                disabled={currentPage === 1}
                className="px-4 py-2 bg-gray-700 text-gray-200 rounded-md disabled:opacity-50 hover:bg-gray-600"
              >
                Previous
              </button>
              <span className="text-gray-200">Page {currentPage} of {totalPages}</span>
              <button
                onClick={() => setCurrentPage((prev) => Math.min(prev + 1, totalPages))}
                disabled={currentPage === totalPages}
                className="px-4 py-2 bg-gray-700 text-gray-200 rounded-md disabled:opacity-50 hover:bg-gray-600"
              >
                Next
              </button>
            </div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-800 text-gray-200 w-full flex flex-col">
      <nav className="p-6 bg-gray-900 w-full shadow-md flex items-center">
        <div className="max-w-screen-2xl mx-auto flex items-center"> {/* Changed to max-w-screen-2xl */}
          <img src={logo} alt="DOGE Logo" className="h-8 w-8 mr-2" />
          <h1 className="text-2xl font-bold text-white">Government Regulation Analyzer</h1>
        </div>
      </nav>
      <main className="flex-1 w-full max-w-screen-2xl mx-auto px-6 py-6"> {/* Changed to max-w-screen-2xl */}
        <FilterBar onFilter={handleFilter} agencies={agencyOptions} />
        <ChartSection agencies={selectedAgencies} />
        <TableSection />
        <footer className="text-sm text-gray-400 mt-6">
          Data sourced from the{" "}
          <a
            href="https://www.ecfr.gov/developers/documentation/api/v1"
            target="_blank"
            rel="noopener noreferrer"
            className="text-gray-300 underline hover:text-gray-100"
          >
            Code of Federal Regulations (eCFR)
          </a>
          .
        </footer>
      </main>
    </div>
  );
}

export default App;