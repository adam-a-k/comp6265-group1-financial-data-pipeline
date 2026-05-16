import Keycloak from 'keycloak-js'

const keycloak = new Keycloak({
  url: 'https://keycloak-production-40e0.up.railway.app',
  realm: 'financial-data-pipeline',
  clientId: 'financial-dashboard'
})

export default keycloak