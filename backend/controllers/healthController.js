// Health controller. It converts service results and failures into HTTP responses.
import { getDatabaseHealth } from '../services/healthService.js'

export async function checkDatabaseHealth(request, response) {
  try {
    const health = await getDatabaseHealth()
    return response.status(200).json(health)
  } catch (error) {
    console.error('Database health check failed:', error.message)
    return response.status(500).json({
      error: 'Database connection failed',
    })
  }
}