import { ReactNode, useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useStore } from "./store/useStore";
import { loadLanguage } from "./i18n";
import Nav from "./components/Nav";

// Pages
import Login from "./pages/Login";
import Register from "./pages/Register";
import Home from "./pages/Home";
import Scan from "./pages/Scan";
import Send from "./pages/Send";
import History from "./pages/History";
import Learn from "./pages/Learn";
import USSDSimulator from "./pages/USSDSimulator";
import SMSSimulator from "./pages/SMSSimulator";
import Demo from "./pages/Demo";
import LoginGuard from "./pages/LoginGuard";

function ProtectedRoute({ children }: { children: ReactNode }) {
  const token = useStore((s) => s.token);
  return token ? <>{children}</> : <Navigate to="/login" replace />;
}

function RootRedirect() {
  const token = useStore((s) => s.token);
  return token ? <Navigate to="/home" replace /> : <Navigate to="/login" replace />;
}

export default function App() {
  const language = useStore((s) => s.language);

  useEffect(() => {
    loadLanguage(language);
  }, [language]);

  return (
    <BrowserRouter>
      <Nav />
      <main className="md:pl-56 md:pt-14 pb-16 md:pb-0 min-h-screen bg-gray-50">
        <Routes>
          <Route path="/" element={<RootRedirect />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route
            path="/home"
            element={
              <ProtectedRoute>
                <Home />
              </ProtectedRoute>
            }
          />
          <Route
            path="/scan"
            element={
              <ProtectedRoute>
                <Scan />
              </ProtectedRoute>
            }
          />
          <Route
            path="/send"
            element={
              <ProtectedRoute>
                <Send />
              </ProtectedRoute>
            }
          />
          <Route
            path="/history"
            element={
              <ProtectedRoute>
                <History />
              </ProtectedRoute>
            }
          />
          <Route path="/learn" element={<Learn />} />
          <Route path="/ussd" element={<USSDSimulator />} />
          <Route
            path="/sms"
            element={
              <ProtectedRoute>
                <SMSSimulator />
              </ProtectedRoute>
            }
          />
          <Route path="/demo" element={<Demo />} />
          <Route
            path="/login-guard"
            element={
              <ProtectedRoute>
                <LoginGuard />
              </ProtectedRoute>
            }
          />
        </Routes>
      </main>
    </BrowserRouter>
  );
}
