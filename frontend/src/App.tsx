// React
import React from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

// Third Party
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import i18n from "i18next";
import Backend from "i18next-http-backend";
import { NuqsAdapter } from "nuqs/adapters/react-router/v8";
import { initReactI18next } from "react-i18next";

// AA TaxSystem
import { AppName, ProjectName } from "../configuration";
import { ErrorPage } from "@/Pages/404";
import AccountOverviewPage from "@/Pages/Account/AccountOverviewPage";
import AdminPage from "@/Pages/Admin/AdminPage";
import AuthBase from "@/Pages/Base";
import OwnerManagePage from "@/Pages/Manage/OwnerManagePage";
import OverviewPage from "@/Pages/Overview/OverviewPage";
import MyPaymentsPage from "@/Pages/Payments/MyPaymentsPage";
import PaymentsPage from "@/Pages/Payments/PaymentsPage";
import SettingsPage from "@/Pages/SettingsPage";

export { AppName, ProjectName };

const queryClient = new QueryClient();

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

function App() {
  return (
    <React.StrictMode>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <NuqsAdapter>
            <Routes>
              <Route path={`/${ProjectName}/`} element={<AuthBase />}>
                <Route index element={<OverviewPage />} />
                <Route path="account/" element={<AccountOverviewPage />} />
                <Route path="account/:ownerId/" element={<AccountOverviewPage />} />
                <Route path="owner/:ownerId/" element={<OwnerManagePage />} />
                <Route path="payments/:ownerId/" element={<PaymentsPage />} />
                <Route path="my-payments/:ownerId/" element={<MyPaymentsPage />} />
                <Route path="admin/" element={<AdminPage />} />
                <Route path="settings/" element={<SettingsPage />} />
                <Route path="*" element={<ErrorPage />} />
              </Route>
              <Route path="*" element={<Navigate to={`/${ProjectName}/`} replace />} />
            </Routes>
          </NuqsAdapter>
        </BrowserRouter>
      </QueryClientProvider>
    </React.StrictMode>
  );
}

export default App;
