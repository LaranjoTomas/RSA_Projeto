import React from 'react';
import TrafficMap from './components/TrafficMap';
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>Traffic Control System</h1>
        <p>Integrated System for Traffic Control with Robots and Smart Signaling</p>
      </header>
      <main>
        <TrafficMap />
      </main>
      <footer>
        <p>© 2025 Traffic Control System</p>
      </footer>
    </div>
  );
}

export default App;