import { Routes, Route, BrowserRouter } from 'react-router-dom'
import Home from './pages/Home'
import Chatbot from './pages/Chatbot'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/chatbot" element={<Chatbot />} />
      </Routes>
    </BrowserRouter>
  )
}
