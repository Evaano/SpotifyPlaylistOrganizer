import React, { useEffect } from "react";
import { Music } from "lucide-react";
import { useNavigate } from "react-router-dom";
import api, { API_BASE_URL } from "../config";

export default function Login() {
  const navigate = useNavigate();

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const response = await api.get("/api/status");
        if (response.data.authenticated) {
          navigate("/dashboard");
        }
      } catch (error) {
        console.error("Auth check failed", error);
      }
    };
    checkAuth();
  }, [navigate]);

  const handleLogin = () => {
    window.location.href = `${API_BASE_URL}/login`;
  };

  return (
    <div className="flex flex-col items-center justify-center h-screen bg-gradient-to-br from-neutral-900 to-black p-4">
      <div className="bg-neutral-800/50 p-8 rounded-2xl shadow-2xl border border-white/10 backdrop-blur-md max-w-md w-full text-center">
        <div className="flex justify-center mb-6">
          <div className="p-4 bg-green-500 rounded-full shadow-lg shadow-green-500/20">
            <Music size={48} className="text-black" />
          </div>
        </div>

        <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-neutral-400 mb-2">
          Spotify Sorter
        </h1>
        <p className="text-neutral-400 mb-8 text-lg">
          Organize your playlists by genre automatically.
        </p>

        <button
          onClick={handleLogin}
          className="w-full bg-[#1DB954] hover:bg-[#1ed760] text-black font-bold py-4 px-8 rounded-full transition-all duration-300 transform hover:scale-105 shadow-lg hover:shadow-green-500/40 text-lg flex items-center justify-center gap-2"
        >
          <span>Connect with Spotify</span>
        </button>

        <p className="mt-6 text-xs text-neutral-500">Powered by Python & React</p>
      </div>
    </div>
  );
}
