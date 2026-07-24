// Application entry point: middleware, health endpoints, route mounting, and error responses.
import 'dotenv/config'
import cors from 'cors'
import express from 'express'
import healthRoutes from './routes/healthRoutes.js'

const app = express()
const port = Number(process.env.PORT) || 3000

app.use(cors())
app.use(express.json())

// Basic service health endpoint that does not require a database connection.
app.get('/', (request, response) => {
  response.status(200).json({
    status: 'running',
    service: 'SupplyPrescript Backend',
  })
})

app.use('/api/health', healthRoutes)

// Return JSON for unknown API paths instead of an HTML response.
app.use((request, response) => {
  response.status(404).json({ error: 'Route not found' })
})

// Final error boundary for unexpected Express errors.
app.use((error, request, response, next) => {
  console.error('Unhandled request error:', error.message)
  response.status(500).json({ error: 'Internal server error' })
})

const server = app.listen(port, () => {
  console.log(`SupplyPrescript backend listening on port ${port}`)
})

// Handle server-level failures, such as a port already being in use, without an uncaught error.
server.on('error', (error) => {
  console.error('Server failed to start:', error.message)
})