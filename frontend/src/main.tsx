// React
import React from 'react'
import ReactDOM from "react-dom/client";

// AA TaxSystem
// Configuration
import { AppName } from "../configuration.js"
// App
import App from '@/App.tsx';
import '@/index.css';

const container = document.getElementById(`${AppName}-root`)

if (!container) {
  throw new Error(`${AppName} React mount point was not found.`)
}

ReactDOM.createRoot(container).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
