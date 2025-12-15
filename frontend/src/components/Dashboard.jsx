import { useEffect, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { PlayCircle, ArrowRight, Loader2, Disc } from "lucide-react";
import API_BASE_URL from "../config";

export default function Dashboard() {
  const [playlists, setPlaylists] = useState([]);
  const [selectedPlaylists, setSelectedPlaylists] = useState(new Set());
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchPlaylists = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/playlists`);
        setPlaylists(response.data.playlists);
        setLoading(false);
      } catch (error) {
        console.error("Error fetching playlists:", error);
        setLoading(false);
      }
    };

    fetchPlaylists();
  }, []);

  const toggleSelection = (id) => {
    const newSelection = new Set(selectedPlaylists);
    if (newSelection.has(id)) {
      newSelection.delete(id);
    } else {
      newSelection.add(id);
    }
    setSelectedPlaylists(newSelection);
  };

  const handleAnalyze = () => {
    if (selectedPlaylists.size === 0) return;
    const ids = Array.from(selectedPlaylists).join(",");
    navigate(`/analyze/${ids}`);
  };

  return (
    <div className="p-8 max-w-7xl mx-auto pb-24">
      <header className="mb-12 flex items-center justify-between sticky top-0 bg-neutral-900/95 backdrop-blur z-20 py-4 border-b border-white/5">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2 ml-1">
            My Playlists
          </h1>
          <p className="text-neutral-400 ml-1">
            Select playlists to analyze and sort
          </p>
        </div>

        {selectedPlaylists.size > 0 && (
          <button
            onClick={handleAnalyze}
            className="bg-green-500 hover:bg-green-400 text-black font-bold py-3 px-8 rounded-full shadow-lg hover:shadow-green-500/40 transition-all flex items-center gap-2 animate-in fade-in slide-in-from-right-10"
          >
            <PlayCircle size={20} className="fill-current" />
            Analyze {selectedPlaylists.size} Playlists
          </button>
        )}
      </header>

      {loading ? (
        <div className="flex justify-center items-center h-64">
          <Loader2 className="animate-spin text-green-500" size={48} />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {playlists.map((playlist) => {
            const isSelected = selectedPlaylists.has(playlist.id);
            return (
              <div
                key={playlist.id}
                onClick={() => toggleSelection(playlist.id)}
                className={`group relative rounded-xl p-4 transition-all duration-300 cursor-pointer flex items-center gap-4 border 
                    ${
                      isSelected
                        ? "bg-neutral-800 border-green-500 shadow-[0_0_15px_rgba(34,197,94,0.3)]"
                        : "bg-neutral-800/40 hover:bg-neutral-800 border-white/5 hover:border-white/10"
                    }`}
              >
                {/* Visual Selection Indicator */}
                <div
                  className={`absolute top-4 right-4 w-6 h-6 rounded-full border-2 flex items-center justify-center transition-colors
                    ${
                      isSelected
                        ? "bg-green-500 border-green-500"
                        : "border-neutral-500 group-hover:border-white"
                    }`}
                >
                  {isSelected && (
                    <div className="w-2.5 h-2.5 bg-black rounded-full" />
                  )}
                </div>

                <div className="relative w-20 h-20 flex-shrink-0 bg-neutral-700 rounded-lg overflow-hidden shadow-lg">
                  {playlist.images && playlist.images[0] ? (
                    <img
                      src={playlist.images[0].url}
                      alt={playlist.name}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-neutral-500">
                      <Disc size={24} />
                    </div>
                  )}
                </div>

                <div className="flex-1 min-w-0 pr-8">
                  <h3
                    className={`font-semibold text-lg truncate transition-colors ${
                      isSelected ? "text-green-500" : "text-white"
                    }`}
                  >
                    {playlist.name}
                  </h3>
                  <p className="text-neutral-400 text-sm">
                    {playlist.tracks.total} tracks
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
