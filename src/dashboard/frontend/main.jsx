import React from 'react'
import ReactDOM from 'react-dom/client'
import Keycloak from 'keycloak-js'
import App from './App.jsx'

const keycloak = new Keycloak({
  url: 'https://keycloak-production-40e0.up.railway.app',
  realm: 'financial-data-pipeline',
  clientId: 'financial-dashboard'
})

keycloak.init({ onLoad: 'login-required' }).then(() => {
  ReactDOM.createRoot(document.getElementById('root')).render(
    <React.StrictMode>
      <App keycloak={keycloak} />
    </React.StrictMode>
  )
})