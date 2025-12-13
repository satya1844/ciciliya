<link href="/src/styles/global.css" rel="stylesheet"></link>
import ChatInterface from './components/ChatInterface';
import { DarkModeProvider } from './contexts/DarkModeContext';

function App() {
  return (
    <DarkModeProvider>
      <ChatInterface />
    </DarkModeProvider>
  );
}

export default App;
