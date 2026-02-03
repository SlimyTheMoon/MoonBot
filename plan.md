MoonBot Design Document

1. Architecture Overview

The application consists of three logical components running within a Docker container environment:

The Discord Bot (Consumer):

Connects to Discord Gateway.

Listens for Slash Commands (/setup, /status).

Sends alerts to configured channels.

The Poller (Worker):

Runs in a background loop (asyncio task).

Fetches https://darkstat.dd84ai.com/api/pob_goods.

Compares new data vs. old data.

Triggers alerts if thresholds are met.

The Web UI (Configuration):

A lightweight web server (FastAPI or Quart).

Provides a dashboard for selecting channels and setting thresholds.

Note: For this starter, we will integrate a basic API endpoint, but the primary config will be via Slash Commands to keep the complexity manageable initially.

2. Data Flow

External: darkstat API -> JSON Data.

Internal: Poller checks JSON -> Detects Health Drop -> Looks up Database for subscribed Channels -> Calls Bot to send Message.

3. Database Schema (SQLite/Postgres)

We need to store "Subscriptions"—links between a Discord Channel and a specific Base or generic alerts.

Table: Subscriptions

Type

Description

id

Integer

PK

guild_id

Integer

Discord Server ID

channel_id

Integer

Discord Channel ID

alert_type

String

'health_low', 'item_found', 'all'

threshold

Float

e.g., 50.0 (Notify if health < 50%)

4. API Handling Strategy

The pob_goods endpoint likely returns a list of bases.

State Tracking: We must cache the last known state of every base in memory or DB.

Logic:

if new_base.health < old_base.health and new_base.health < threshold:
    send_alert()


5. Security & Discord

Intents: You need Message Content intent if you read messages (not needed for Slash Commands) and Guilds intent.

Permissions: The bot needs View Channel and Send Messages in the target channels.

6. Development Roadmap

Phase 1 (The Core): Get the Bot running and fetching the API. Print diffs to console.

Phase 2 (The Link): Implement /watch command to save channel IDs to DB. Make the Bot send alerts to those channels.

Phase 3 (The Web): Build the FastAPI dashboard that reads the same DB to show a visual list of tracked bases.