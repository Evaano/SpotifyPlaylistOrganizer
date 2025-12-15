import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import {
  ArrowLeft,
  Loader2,
  Music2,
  BarChart3,
  Disc,
  X,
  Check,
  AlertCircle,
  Info,
} from "lucide-react";
import API_BASE_URL from "../config";

export default function Analysis() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedGenre, setSelectedGenre] = useState(null);
  const [showGuide, setShowGuide] = useState(true);

  // Modal State for confirmations and feedback
  const [modal, setModal] = useState({
    isOpen: false,
    type: "confirm", // 'confirm', 'success', 'error', 'loading'
    title: "",
    message: "",
    onConfirm: null,
  });

  useEffect(() => {
    const fetchAnalysis = async () => {
      try {
        const response = await axios.get(
          `${API_BASE_URL}/api/analyze?playlist_ids=${id}`
        );
        setData(response.data);
        setLoading(false);
      } catch (error) {
        console.error("Error analyzing playlist:", error);
        setLoading(false);
      }
    };

    fetchAnalysis();
  }, [id]);

  const getGenreColor = (index) => {
    const colors = [
      "bg-green-500",
      "bg-blue-500",
      "bg-purple-500",
      "bg-pink-500",
      "bg-yellow-500",
      "bg-red-500",
    ];
    return colors[index % colors.length];
  };

  const closeModal = () => {
    setModal((prev) => ({ ...prev, isOpen: false }));
  };

  const handleCreatePlaylist = (genre) => {
    const tracksToAdd = data.tracks
      .filter((t) => t.genres.includes(genre))
      .map((t) => t.uri);

    if (tracksToAdd.length === 0) return;

    // Capitalize genre for display
    const genreName = genre.charAt(0).toUpperCase() + genre.slice(1);

    // Open Confirmation Modal
    setModal({
      isOpen: true,
      type: "confirm",
      title: `Create ${genreName} Mix?`,
      message: `This will create a new playlist with ${tracksToAdd.length} tracks. Duplicate checks will be performed automatically.`,
      onConfirm: () => performCreate(genreName, tracksToAdd),
    });
  };

  const performCreate = async (genre, tracksToAdd) => {
    try {
      // Show Loading Modal
      setModal({
        isOpen: true,
        type: "loading",
        title: "Creating Playlist",
        message: "Talking to Spotify...",
        onConfirm: null,
      });

      const response = await axios.post(`${API_BASE_URL}/api/create_playlist`, {
        name: `${genre} Mix`,
        track_uris: tracksToAdd,
      });

      // Show Success Modal
      setModal({
        isOpen: true,
        type: "success",
        title: "Playlist Created!",
        message: response.data.message,
        onConfirm: null,
      });
    } catch (error) {
      console.error("Failed to create playlist", error);
      // Show Error Modal
      setModal({
        isOpen: true,
        type: "error",
        title: "Creation Failed",
        message:
          "Something went wrong while creating the playlist. Please try again.",
        onConfirm: null,
      });
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-screen bg-neutral-900 text-white">
        <Loader2 className="animate-spin text-green-500 mb-4" size={48} />
        <p className="text-xl font-light animate-pulse">Analyzing "vibes"...</p>
        <p className="text-sm text-neutral-500 mt-2">
          Fetching artists & genres (this might take a moment)
        </p>
      </div>
    );
  }

  if (!data)
    return <div className="text-white p-8">Failed to load analysis.</div>;

  // Filter tracks matches the selected genre if one is active
  const visibleTracks = selectedGenre
    ? data.tracks.filter((t) => t.genres.includes(selectedGenre))
    : data.tracks;

  return (
    <div className="h-screen bg-neutral-900 text-white p-6 max-w-7xl mx-auto flex flex-col overflow-hidden relative">
      {/* Modal Overlay */}
      {modal.isOpen && (
        <div className="absolute inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div className="bg-neutral-800 border border-white/10 rounded-2xl p-8 max-w-md w-full shadow-2xl scale-100 animate-in zoom-in-95 duration-200">
            <div className="flex justify-center mb-6">
              {modal.type === "confirm" && (
                <Disc size={48} className="text-blue-500" />
              )}
              {modal.type === "loading" && (
                <Loader2 size={48} className="text-green-500 animate-spin" />
              )}
              {modal.type === "success" && (
                <Check size={48} className="text-green-500" />
              )}
              {modal.type === "error" && (
                <AlertCircle size={48} className="text-red-500" />
              )}
            </div>

            <h3 className="text-2xl font-bold text-center mb-2">
              {modal.title}
            </h3>
            <p className="text-neutral-400 text-center mb-8">{modal.message}</p>

            <div className="flex gap-3 justify-center">
              {modal.type === "confirm" && (
                <>
                  <button
                    onClick={closeModal}
                    className="px-6 py-2 rounded-full font-medium text-white hover:bg-white/10 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={modal.onConfirm}
                    className="px-6 py-2 rounded-full font-bold bg-green-500 text-black hover:bg-green-400 transition-colors shadow-lg hover:shadow-green-500/25"
                  >
                    Create It via Magic
                  </button>
                </>
              )}
              {(modal.type === "success" || modal.type === "error") && (
                <button
                  onClick={closeModal}
                  className="px-8 py-2 rounded-full font-bold bg-white text-black hover:bg-neutral-200 transition-colors"
                >
                  Got it
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Header Section */}
      <div className="flex-shrink-0">
        <div className="flex justify-between items-start mb-6">
          <button
            onClick={() => navigate("/dashboard")}
            className="flex items-center text-neutral-400 hover:text-white transition-colors"
          >
            <ArrowLeft size={20} className="mr-2" /> Back to Dashboard
          </button>

          {showGuide && (
            <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-3 text-sm text-blue-200 flex items-start gap-3 max-w-md animate-in slide-in-from-top-4">
              <Info size={20} className="flex-shrink-0 mt-0.5 text-blue-400" />
              <div>
                <p className="font-semibold mb-1">How it works:</p>
                <p>
                  1. Click a <strong>Genre</strong> on the left to filter the
                  tracks.
                </p>
                <p>
                  2. Once filtered, click the <strong>Create Playlist</strong>{" "}
                  button to save it to Spotify.
                </p>
              </div>
              <button
                onClick={() => setShowGuide(false)}
                className="text-blue-400 hover:text-white ml-2"
              >
                <X size={16} />
              </button>
            </div>
          )}
        </div>

        <div className="flex flex-col lg:flex-row gap-8 mb-6">
          <div className="flex-1">
            <h1 className="text-4xl font-bold mb-2">Playlist Analysis</h1>
            <div className="flex gap-4 text-neutral-400 mt-4">
              <div className="bg-neutral-800 px-4 py-2 rounded-lg flex items-center gap-2">
                <Music2 size={18} />
                <span className="text-white font-bold">
                  {data.metrics.total_tracks}
                </span>{" "}
                Tracks
              </div>
              <div className="bg-neutral-800 px-4 py-2 rounded-lg flex items-center gap-2">
                <Disc size={18} />
                <span className="text-white font-bold">
                  {data.metrics.unique_artists}
                </span>{" "}
                Artists
              </div>
              <div className="bg-neutral-800 px-4 py-2 rounded-lg flex items-center gap-2">
                <BarChart3 size={18} />
                <span className="text-white font-bold">
                  {data.metrics.total_genres}
                </span>{" "}
                Genres
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content: Genre list and Track list side-by-side */}
      <div className="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Col: Interactive Genre List */}
        <div className="bg-neutral-800/50 rounded-2xl p-6 border border-white/5 flex flex-col overflow-hidden">
          <h2 className="text-2xl font-bold mb-4 flex-shrink-0">
            {selectedGenre ? `Genre: ${selectedGenre}` : "Top Genres"}
          </h2>

          {selectedGenre && (
            <button
              onClick={() => setSelectedGenre(null)}
              className="mb-4 text-sm text-neutral-400 hover:text-white flex items-center"
            >
              <ArrowLeft size={14} className="mr-1" /> Back to all genres
            </button>
          )}

          <div className="space-y-4 overflow-y-auto custom-scrollbar flex-1 pr-2">
            {Object.entries(data.genre_counts)
              .slice(0, 50)
              .map(([genre, count], index) => {
                const percentage = (
                  (count / data.metrics.total_tracks) *
                  100
                ).toFixed(1);
                const isSelected = selectedGenre === genre;

                return (
                  <div
                    key={genre}
                    onClick={() => setSelectedGenre(isSelected ? null : genre)}
                    className={`group p-3 rounded-lg transition-all cursor-pointer border ${
                      isSelected
                        ? "bg-neutral-800 border-green-500 shadow-[0_0_10px_rgba(34,197,94,0.2)]"
                        : "hover:bg-white/5 border-transparent"
                    }`}
                  >
                    <div className="flex justify-between items-center mb-1">
                      <span
                        className={`capitalize font-medium ${
                          isSelected ? "text-green-500" : ""
                        }`}
                      >
                        {genre}
                      </span>
                      {isSelected && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleCreatePlaylist(genre);
                          }}
                          className="text-xs bg-green-500 text-black font-bold px-3 py-1 rounded-full hover:scale-105 transition-transform"
                        >
                          Create Playlist
                        </button>
                      )}
                    </div>

                    <div className="flex justify-between text-xs text-neutral-400 mb-1">
                      <span>{count} tracks</span>
                      <span>{percentage}%</span>
                    </div>

                    <div className="h-1.5 bg-neutral-700 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${getGenreColor(
                          index
                        )} transform origin-left transition-all duration-1000 ease-out`}
                        style={{ width: `${percentage}%` }}
                      ></div>
                    </div>
                  </div>
                );
              })}
          </div>
        </div>

        {/* Right Col: Track List (Dynamic) */}
        <div className="lg:col-span-2 bg-neutral-800/50 rounded-2xl p-6 border border-white/5 flex flex-col overflow-hidden">
          <h2 className="text-2xl font-bold mb-4 flex-shrink-0">
            Tracks{" "}
            {selectedGenre && (
              <span className="text-neutral-400 text-lg font-normal">
                ({visibleTracks.length})
              </span>
            )}
          </h2>
          <div className="overflow-y-auto pr-2 space-y-2 custom-scrollbar flex-1">
            {visibleTracks.map((track) => (
              <div
                key={track.id}
                className="flex items-center gap-4 p-3 hover:bg-white/5 rounded-lg transition-colors group"
              >
                <div className="w-12 h-12 bg-neutral-700 rounded overflow-hidden flex-shrink-0">
                  {track.image && (
                    <img
                      src={track.image}
                      alt={track.name}
                      className="w-full h-full object-cover"
                    />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-medium truncate">{track.name}</div>
                  <div className="text-sm text-neutral-400 truncate">
                    {track.artists.join(", ")}
                  </div>
                </div>
                <div className="flex gap-2 justify-end flex-wrap max-w-[40%]">
                  {track.genres.slice(0, 3).map((g, i) => (
                    <span
                      key={i}
                      className="text-xs bg-white/10 px-2 py-1 rounded-full text-neutral-300 capitalize truncate max-w-[100px]"
                    >
                      {g}
                    </span>
                  ))}
                  {track.genres.length === 0 && (
                    <span className="text-xs text-neutral-600 italic">
                      Unknown Genre
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
