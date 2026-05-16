import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import keycloak from './keycloak'
import App from './App'
import './App.css'

keycloak.init({ onLoad: 'login-required', pkceMethod: 'S256' }).then((authenticated) => {
  if (authenticated) {
    createRoot(document.getElementById('root')).render(
      <StrictMode>
        <App keycloak={keycloak} />
      </StrictMode>
    )
  }
})