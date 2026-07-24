// Health routes only. Request handling remains in the controller layer.
import { Router } from 'express'
import { checkDatabaseHealth } from '../controllers/healthController.js'

const router = Router()

router.get('/database', checkDatabaseHealth)

export default router