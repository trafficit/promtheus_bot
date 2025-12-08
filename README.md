# Promtheus_bot

DevOps Telegram Bot
his project is a production‑ready Telegram bot for managing Docker containers and monitoring server metrics. It is built with Python and the aiogram library.

Features
Access restricted to a single Telegram user ID

Main menu with two sections:

Server menu: view CPU, memory, disk, swap, uptime, and a summary

Containers menu: list allowed containers and perform Start, Stop, Restart, and view Logs

Safe implementation:

White‑list of allowed containers

No shell injection risks

Log output trimmed to a safe length

Requirements
Python 3.9 or higher

Installed packages:

bash
pip install aiogram psutil
Docker installed on the server

Access to the Docker socket (/var/run/docker.sock) if running inside a container

Configuration
The bot uses hardcoded values in the script:

API_TOKEN: your Telegram bot token from BotFather

ALLOWED_USER_ID: your Telegram user ID

ALLOWED_SERVICES: list of container names you want to manage

API_TOKEN = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
ALLOWED_USER_ID = XXXXXXXXXXX
ALLOWED_SERVICES = ["prometheus", "alertmanager", "grafana", "node_exporter"]
Running the Bot
Save the script as bot.py.

Install dependencies:

pip install aiogram psutil
Run the bot:

prometeus_bot.py
Usage
Start the bot in Telegram with /start.

You will see the main menu with two options: Server and Containers.

In the Server menu you can check CPU, memory, disk, swap, uptime, or get a full summary.

In the Containers menu you can select one of the allowed containers and perform actions:

Start ,  Stop, Restart

View last 60 lines of logs

Security Notes
Only the specified user ID can interact with the bot. All other users will see "Access denied".

Only containers listed in ALLOWED_SERVICES can be controlled.

p.s. Keep your bot token private. Do not share it publicly!

If running inside Docker, mount the Docker socket carefully, as it grants full control over containers.
