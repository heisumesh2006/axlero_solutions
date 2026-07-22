import 'dotenv/config'
import cors from 'cors'
import express from 'express'

const app = express()
const port = Number(process.env.PORT) || 3000

app.use(cors())
app.use(express.json())

app.listen(port, () => {
  console.log(`SupplyPrescript backend listening on port ${port}`)
})