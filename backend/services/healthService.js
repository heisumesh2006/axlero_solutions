// Database health-check service. It owns the database access for this feature.
import pool from '../config/db.js'

export async function getDatabaseHealth() {
  const result = await pool.query('SELECT NOW() AS time')

  return {
    database: 'connected',
    time: result.rows[0].time,
  }
}