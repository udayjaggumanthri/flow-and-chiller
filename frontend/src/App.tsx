import React from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { SettingsPage } from "./pages/SettingsPage";
import { DownloadPage } from "./pages/DownloadPage";
import { PresetsPage } from "./pages/PresetsPage";
import { DailyConsumptionPage } from "./pages/DailyConsumptionPage";
import { Layout } from "./components/Layout";

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Navigate to="/download" replace />} />
          <Route path="/download" element={<DownloadPage />} />
          <Route path="/daily" element={<DailyConsumptionPage />} />
          <Route path="/presets" element={<PresetsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
};

