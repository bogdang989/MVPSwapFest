import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./Layout";
import Home from "./pages/Home";
import Swapfest from "./pages/Swapfest";
import Vote from "./pages/Vote";
import "./flow/config";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="swapfest" element={<Swapfest />} />
          <Route path="vote" element={<Vote />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
