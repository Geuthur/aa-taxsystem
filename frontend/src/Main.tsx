// React
import React from "react";
import ReactDOM from "react-dom/client";

// Third Party
import { initI18n } from "aa-geuthur-react";

// AA TaxSystem
import { AppName, ProjectName } from "@/constants";
import Routing from "@/Routing";

// Styles
import "@/Styles/index.css";

export { AppName, ProjectName };

// Language from Django's LANGUAGE_CODE (lang="..." on the root element), texts from /static/<project>/i18n/.
initI18n(ProjectName, `${AppName}-root`);

const container = document.getElementById(`${AppName}-root`);

if (!container) {
  throw new Error(`${AppName} React mount point was not found.`);
}

ReactDOM.createRoot(container).render(
  <React.StrictMode>
    <Routing />
  </React.StrictMode>,
);
