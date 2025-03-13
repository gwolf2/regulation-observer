import { useState } from "react";
import Select, { MultiValue } from "react-select";

interface FilterBarProps {
  onFilter: (filterType: string, selectedAgencies?: string[], metric?: string) => void;
  agencies: { label: string; value: string }[];
}

function FilterBar({ onFilter, agencies }: FilterBarProps) {
  const [selectedAgencies, setSelectedAgencies] = useState<MultiValue<{ label: string; value: string }>>([]);
  const [searchQuery, setSearchQuery] = useState("");

  const handleAgencyChange = (selected: MultiValue<{ label: string; value: string }>) => {
    setSelectedAgencies(selected);
    onFilter("specific", selected.map((option) => option.value));
  };

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
    onFilter("search", undefined, e.target.value.toLowerCase());
  };

  return (
    <div className="p-4 bg-gray-900 rounded-md shadow-md mb-6">
      <div className="flex flex-col gap-4">
        <div className="flex gap-2 flex-wrap">
          <button
            onClick={() => onFilter("all")}
            className="px-3 py-1 bg-gray-700 text-gray-200 rounded-md hover:bg-gray-600 transition font-medium text-sm"
          >
            All Agencies
          </button>
          <button
            onClick={() => onFilter("top3", undefined, "wordCount")}
            className="px-3 py-1 bg-gray-700 text-gray-200 rounded-md hover:bg-gray-600 transition font-medium text-sm"
          >
            Top 3 by Word Count
          </button>
          <button
            onClick={() => onFilter("top3", undefined, "restrictiveness")}
            className="px-3 py-1 bg-gray-700 text-gray-200 rounded-md hover:bg-gray-600 transition font-medium text-sm"
          >
            Top 3 by Restrictiveness
          </button>
          <button
            onClick={() => onFilter("bottom3", undefined, "sentiment")}
            className="px-3 py-1 bg-gray-700 text-gray-200 rounded-md hover:bg-gray-600 transition font-medium text-sm"
          >
            Bottom 3 by Sentiment
          </button>
        </div>
        <div className="flex gap-4 flex-col md:flex-row">
          <Select
            isMulti
            options={agencies}
            value={selectedAgencies}
            onChange={handleAgencyChange}
            className="flex-1 text-gray-800"
            placeholder="Select agencies..."
            styles={{
              control: (base) => ({
                ...base,
                backgroundColor: "#374151",
                borderColor: "#4b5563",
                color: "#e5e7eb",
                borderRadius: "0.375rem",
                padding: "0.25rem",
              }),
              singleValue: (base) => ({ ...base, color: "#e5e7eb" }),
              menu: (base) => ({ ...base, backgroundColor: "#374151" }),
              option: (base, { isFocused }) => ({
                ...base,
                backgroundColor: isFocused ? "#4b5563" : "#374151",
                color: "#e5e7eb",
              }),
              multiValue: (base) => ({ ...base, backgroundColor: "#4b5563" }),
              multiValueLabel: (base) => ({ ...base, color: "#e5e7eb" }),
            }}
          />
          <input
            type="text"
            value={searchQuery}
            onChange={handleSearch}
            placeholder="Search agencies..."
            className="flex-1 px-4 py-2 rounded-md bg-gray-700 text-gray-200 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-500"
          />
        </div>
      </div>
    </div>
  );
}

export default FilterBar;