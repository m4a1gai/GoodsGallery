import { NavLink, Route, Routes } from "react-router-dom";
import CandidateDetail from "./pages/CandidateDetail";
import CatalogHome from "./pages/CatalogHome";
import ItemDetail from "./pages/ItemDetail";
import MyCollection from "./pages/MyCollection";
import ReviewQueue from "./pages/ReviewQueue";
import Sources from "./pages/Sources";

function App() {
  return (
    <div className="app-shell">
      <header className="top-nav">
        <NavLink to="/" className="brand">
          Poppin'Party 谷子図鑑
        </NavLink>
        <nav>
          <NavLink to="/" end>
            Catalog
          </NavLink>
          <NavLink to="/collection">My Collection</NavLink>
          <NavLink to="/review">Review Queue</NavLink>
          <NavLink to="/sources">Sources</NavLink>
        </nav>
      </header>
      <main className="page">
        <Routes>
          <Route path="/" element={<CatalogHome />} />
          <Route path="/items/:id" element={<ItemDetail />} />
          <Route path="/collection" element={<MyCollection />} />
          <Route path="/review" element={<ReviewQueue />} />
          <Route path="/review/:id" element={<CandidateDetail />} />
          <Route path="/sources" element={<Sources />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
