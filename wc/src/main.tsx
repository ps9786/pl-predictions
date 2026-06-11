import {StrictMode} from 'react';
import {createRoot} from 'react-dom/client';
import App from '/wc/src/App.tsx';
import '/wc/src/index.css';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
