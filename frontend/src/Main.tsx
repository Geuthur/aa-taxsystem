// React
import React from "react";
import ReactDOM from "react-dom/client";

// Third Party
import i18n from "i18next";
import Backend from "i18next-http-backend";
import { initReactI18next } from "react-i18next";

// AA TaxSystem
import { AppName, ProjectName } from "@/constants";
import Routing from "@/Routing";
import "@/Styles/index.css";
import "@/Styles/table.css";

export { AppName, ProjectName };

// Read language directly from Django's LANGUAGE_CODE (set as lang="..." on root div)
const djangoLanguage =
  typeof document !== "undefined"
    ? document.getElementById(`${AppName}-root`)?.getAttribute("lang") ?? "en"
    : "en";

i18n
  .use(Backend)
  .use(initReactI18next)
  .init({
    lng: djangoLanguage,
    fallbackLng: "en",
    keySeparator: false,
    nsSeparator: false,
    interpolation: {
      escapeValue: false,
    },
    react: {
      useSuspense: false,
    },
    backend: {
      loadPath: `/static/${ProjectName}/i18n/{{lng}}/{{ns}}.json`,
    },
  });

const container = document.getElementById(`${AppName}-root`);

if (!container) {
  throw new Error(`${AppName} React mount point was not found.`);
}

ReactDOM.createRoot(container).render(
  <React.StrictMode>
    <Routing />
  </React.StrictMode>,
);
