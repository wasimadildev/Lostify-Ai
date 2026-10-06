import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import Footer from './components/Footer';
import SearchPage from './pages/SearchPage';
import NewReportPage from './pages/NewReportPage';
import ReportsPage from './pages/ReportsPage';

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen flex flex-col">
        <Header />
        <main className="flex-1 px-4 py-8">
          <Routes>
            <Route path="/" element={<SearchPage />} />
            <Route path="/new-report" element={<NewReportPage />} />
            <Route path="/reports" element={<ReportsPage />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </BrowserRouter>
  );
}