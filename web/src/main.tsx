import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import { I18nProvider } from "./i18n";
import Landing from "./pages/Landing";
import "./styles.css";

// The landing page lives at /, the app at /app (nginx and Vite serve index.html for both).
const isApp = window.location.pathname.startsWith("/app");

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <I18nProvider>{isApp ? <App /> : <Landing />}</I18nProvider>
  </StrictMode>,
);
