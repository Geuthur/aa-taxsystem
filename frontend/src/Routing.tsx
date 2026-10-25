// React
import React from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

// Third Party
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { NuqsAdapter } from "nuqs/adapters/react-router/v8";

// AA TaxSystem
import { ProjectName } from "@/constants";
import { ErrorPage } from "@/Pages/404";
import AccountOverviewPage from "@/Pages/AccountOverviewPage";
import AdministrationPage from "@/Pages/AdministrationPage";
import AuthBase from "@/Pages/Base";
import MyPaymentsPage from "@/Pages/MyPaymentsPage";
import OverviewPage from "@/Pages/OverviewPage";
import OwnerManagePage from "@/Pages/OwnerManagePage";
import PaymentsPage from "@/Pages/PaymentsPage";
import SettingsPage from "@/Pages/SettingsPage";

const queryClient = new QueryClient();

function Routing() {
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
                <Route path="administration/" element={<AdministrationPage />} />
                <Route path="superuser/" element={<Navigate to={`/${ProjectName}/administration/`} replace />} />
                <Route path="admin/" element={<Navigate to={`/${ProjectName}/administration/`} replace />} />
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

export default Routing;
