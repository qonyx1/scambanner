[![Python Version](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Nextcord Version](https://img.shields.io/badge/nextcord-v3.1.0-blue?logo=discord&logoColor=white)](https://github.com/nextcord/nextcord)
[![MongoDB](https://img.shields.io/badge/Database-MongoDB-47A248?logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

# Scambanner
FastAPI (B) & Nextcord (F) project that lets you create a database of known scammers and take action using it.
## Features

- MongoDB Database (Local, modify to change)
- Multi-party system (Quality assurance, trusted guilds)
- Granular API Key & Generation/Revoking from bot
- Security & Privacy measures
- External media upload capability
- Ticket system (tbd)


## Important

- By default, both systems will assume that you are running a local MongoDB instance with no authentication (please don't port forward...), in order to modify the entire database logic, you should access the `data.py` files in both `frontend` and `backend`. You must change these to use an external database (`mongodb://database.com:27071`).

- This project has a two-party system, meaning that once a trusted/whitelisted guild member fills out a template, and clicks confirm, their case will be sent to another party -- the main guild (Quality Assurance), where you can then confirm it yourself and submit it to the backend.

- This is a hobby project and may not be suitable for production environments. It should be though.
## Deployment

The project contains two different parts, the frontend (Nextcord) and backend (FastAPI). In order to start these two at the same time, and maintain their uptime, you can use [PM2](https://pm2.keymetrics.io/) or use our **experimental Docker container**. 


### Create a virtual environment
**Linux**
```bash
python -m venv ./.venv
source ./.venv/bin/activate
pip install -r ./requirements.txt
```
**Windows (PowerShell)**
```bash
python -m venv .\.venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### Start both programs
**Linux**
```bash
cd ./backend/
pm2 start main.py --name backend --namespace sb
cd ..
cd ./frontend/
pm2 start main.py --name frontend --namespace sb
```
**Windows (PowerShell)**
Same thing, you might be required to change the signs to backslashes.

## Environment Variables

To run this project, you will need to add the following environment variables to your .env file

- `IMGBB_API_KEY = "dummy_imgbb_api_key"`
- `VIDEO_API_SECRET = "dummy_video_api_secret"`
- `VIDEO_API_CLOUD_NAME = "dummy_cloud_name"`
- `VIDEO_API_KEY = "dummy_video_api_key"`
- `TOKEN = "dummy_token_value"`
- `WEBHOOK_URL = "https://discord.com/api/webhooks"`
