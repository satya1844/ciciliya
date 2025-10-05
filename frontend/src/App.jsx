<link href="/src/styles/global.css" rel="stylesheet"></link>
import ChatInterface from './components/ChatInterface';
import { DarkModeProvider, useDarkMode } from './contexts/DarkModeContext';

function AppContent() {
  const { isDarkMode } = useDarkMode();
  
  return (
    <div className={`min-h-screen transition-colors duration-300 ${
      isDarkMode ? 'bg-[#131314]' : 'bg-white'
    }`}>
      <ChatInterface />
    </div>
  );
}

function App() {
  return (
    <DarkModeProvider>
      <AppContent />
    </DarkModeProvider>
  );
}

export default App;
