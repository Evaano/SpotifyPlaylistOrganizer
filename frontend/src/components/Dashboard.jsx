import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { PlayCircle, Loader2, Disc, Trash2, AlertCircle } from "lucide-react";
import api from "../config";

export default function Dashboard() {
  const [playlists, setPlaylists] = useState([]);
  const [selectedPlaylists, setSelectedPlaylists] = useState(new Set());
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const [deleteModal, setDeleteModal] = useState({
    isOpen: false,
    playlist: null,
    isDeleting: false,
  });

  useEffect(() => {
    const fetchPlaylists = async () => {
      try {
        const response = await api.get("/api/playlists");
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

  const openDeleteModal = (e, playlist) => {
    e.stopPropagation(); // Prevent card selection
    setDeleteModal({ isOpen: true, playlist, isDeleting: false });
  };

  const closeDeleteModal = () => {
    setDeleteModal({ isOpen: false, playlist: null, isDeleting: false });
  };

  const confirmDelete = async () => {
    if (!deleteModal.playlist) return;

    setDeleteModal((prev) => ({ ...prev, isDeleting: true }));

    try {
      await api.delete(`/api/delete_playlist/${deleteModal.playlist.id}`);
      // Remove from local state
      setPlaylists((prev) => prev.filter((p) => p.id !== deleteModal.playlist.id));
      // Remove from selection if selected
      setSelectedPlaylists((prev) => {
        const newSet = new Set(prev);
        newSet.delete(deleteModal.playlist.id);
        return newSet;
      });
      closeDeleteModal();
    } catch (error) {
      console.error("Error deleting playlist:", error);
      setDeleteModal((prev) => ({ ...prev, isDeleting: false }));
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto pb-24 relative">
      {/* Delete Confirmation Modal */}
      {deleteModal.isOpen && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div className="bg-neutral-800 border border-white/10 rounded-2xl p-8 max-w-md w-full shadow-2xl">
            <div className="flex justify-center mb-6">
              <AlertCircle size={48} className="text-red-500" />
            </div>
            <h3 className="text-2xl font-bold text-center text-white mb-2">Delete Playlist?</h3>
            <p className="text-neutral-400 text-center mb-2">Are you sure you want to remove</p>
            <p className="text-white font-semibold text-center mb-6">
              "{deleteModal.playlist?.name}"
            </p>
            <p className="text-neutral-500 text-sm text-center mb-8">
              This will unfollow the playlist from your Spotify library.
            </p>

            <div className="flex gap-3 justify-center">
              <button
                onClick={closeDeleteModal}
                disabled={deleteModal.isDeleting}
                className="px-6 py-2 rounded-full font-medium text-white hover:bg-white/10 transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={confirmDelete}
                disabled={deleteModal.isDeleting}
                className="px-6 py-2 rounded-full font-bold bg-red-500 text-white hover:bg-red-400 transition-colors shadow-lg hover:shadow-red-500/25 disabled:opacity-50 flex items-center gap-2"
              >
                {deleteModal.isDeleting ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    Deleting...
                  </>
                ) : (
                  <>
                    <Trash2 size={16} />
                    Delete
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      <header className="mb-12 flex items-center justify-between sticky top-0 bg-neutral-900/95 backdrop-blur z-20 py-4 border-b border-white/5">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2 ml-1">My Playlists</h1>
          <p className="text-neutral-400 ml-1">Select playlists to analyze and sort</p>
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
            const isLikedSongs = playlist.id === "liked";
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
                {/* Delete Button (not for Liked Songs) */}
                {!isLikedSongs && (
                  <button
                    onClick={(e) => openDeleteModal(e, playlist)}
                    className="absolute top-4 right-12 w-6 h-6 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity text-neutral-400 hover:text-red-500 hover:bg-red-500/10"
                    title="Delete playlist"
                  >
                    <Trash2 size={14} />
                  </button>
                )}

                {/* Visual Selection Indicator */}
                <div
                  className={`absolute top-4 right-4 w-6 h-6 rounded-full border-2 flex items-center justify-center transition-colors
                    ${
                      isSelected
                        ? "bg-green-500 border-green-500"
                        : "border-neutral-500 group-hover:border-white"
                    }`}
                >
                  {isSelected && <div className="w-2.5 h-2.5 bg-black rounded-full" />}
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
                  <p className="text-neutral-400 text-sm">{playlist.tracks.total} tracks</p>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
