import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [healthStatus, setHealthStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkHealth();
  }, []);

  const checkHealth = async () => {
    try {
      if (window.electronAPI) {
        const status = await window.electronAPI.healthCheck();
        setHealthStatus(status);
      } else {
        // Fallback for web browser development
        const response = await fetch('http://localhost:5000/api/health');
        const status = await response.json();
        setHealthStatus(status);
      }
    } catch (error) {
      console.error('Health check failed:', error);
      setHealthStatus({ status: 'error', message: error.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <div className="min-h-screen bg-gray-100">
        {/* Header */}
        <header className="bg-white shadow">
          <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
            <h1 className="text-3xl font-bold text-gray-900">ReadMe</h1>
            <p className="text-sm text-gray-500">Local AI Reading Assistant</p>
          </div>
        </header>

        {/* Main Content */}
        <main>
          <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
            <div className="px-4 py-6 sm:px-0">
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-semibold mb-4">System Status</h2>

                {loading ? (
                  <div className="flex items-center">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500 mr-3"></div>
                    <span>Connecting to backend...</span>
                  </div>
                ) : (
                  <div>
                    <div className="flex items-center mb-2">
                      <span className="font-medium mr-2">Backend Status:</span>
                      <span className={`px-2 py-1 rounded text-sm ${
                        healthStatus?.status === 'healthy' || healthStatus?.status === 'ok'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {healthStatus?.status || 'Unknown'}
                      </span>
                    </div>

                    {healthStatus?.message && (
                      <p className="text-sm text-gray-600 mt-2">
                        {healthStatus.message}
                      </p>
                    )}

                    <button
                      onClick={checkHealth}
                      className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition"
                    >
                      Refresh Status
                    </button>
                  </div>
                )}
              </div>

              {/* Placeholder for future features */}
              <div className="mt-6 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold mb-2">Library</h3>
                  <p className="text-gray-600">Your books will appear here</p>
                </div>

                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold mb-2">Import</h3>
                  <p className="text-gray-600">Drag & drop files to import</p>
                </div>

                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold mb-2">Settings</h3>
                  <p className="text-gray-600">Configure voices and preferences</p>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
