# Recommendations
To connect the API to a domain securely, use **Cloudflare Tunnels** to reverse-proxy whatever port to your domain. :)

# Notes
- While you can change the bot's name through the `system_config.toml`, please do not attempt to modify any names hardcoded into the code. It's there to communicate with `pm2` or similar.
- Docker support is experimental and not tested at all. Please stick to the `update_and_run.sh` (or manual pm2 commands) for the best result.
- You must create a `.env` file. You must edit `system_config.toml`, if you don't, some parts will automatically exit.

# Add your .env
- `IMGBB_API_KEY = "dummy_imgbb_api_key"`
- `VIDEO_API_SECRET = "dummy_video_api_secret"`
- `VIDEO_API_CLOUD_NAME = "dummy_cloud_name"`
- `VIDEO_API_KEY = "dummy_video_api_key"`
- `TOKEN="dummy_token_value"`

# Install
- `python3 -m venv ./.venv`
- `source ./.venv/bin/activate`
- `pip install -r requirements.txt`

# Run
```
cd ./backend
pm2 start ./backend/main.py --name backend --namespace scambanner
```
```
cd ./frontend
pm2 start ./frontend/main.py --name frontend --namespace scambanner
```

# Maintain
- `pm2 logs scambanner`
- `pm2 restart scambanner`

# Access
-  `https://ip:port/docs`