# VoicePilot — AI Receptionist for Health Clinics

A 24/7 voice AI platform that handles inbound/outbound calls, books appointments, and syncs with clinic CRMs.

## Stack
- **Voice Agent** — LiveKit Agents (Python)
- **STT** — Deepgram Nova-2
- **LLM** — Gemini 2.0 Flash
- **TTS** — Cartesia Sonic
- **Telephony** — Plivo (India)
- **Backend** — Django + Celery + Redis
- **Frontend** — React + Vite + TailwindCSS
- **Scheduling** — Google Calendar API
- **CRM** — Airtable
- **Storage** — AWS S3

## Quick Start

```bash
cd backend
cp .env.example .env   # fill in your API keys
bash setup.sh          # installs deps, runs migrations
```

Then run 4 terminals:
```bash
python manage.py runserver        # Django API
celery -A voicepilot worker       # Task queue
celery -A voicepilot beat         # Scheduled tasks
python -m agent.main dev          # LiveKit voice agent
```

## Project Structure
```
VoiceBot/
├── backend/          # Django API + LiveKit agent
│   ├── agent/        # Voice pipeline (Deepgram + Gemini + Cartesia)
│   ├── apps/
│   │   ├── clinics/       # Clinic model + provisioning
│   │   ├── calls/         # CallLog + MissedCallQueue
│   │   ├── appointments/  # Appointment booking
│   │   └── webhooks/      # Plivo + LiveKit webhook handlers
│   ├── apps/integrations/ # Plivo, LiveKit, Google Calendar, Airtable, S3
│   └── tasks/             # Celery async tasks
└── frontend/         # React dashboard (coming soon)
```
