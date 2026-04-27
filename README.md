# SongGenAI

SongGenAI is a Django-based AI song generation platform.  
The system supports real song generation via the Suno API and a mock offline strategy for development and testing.

This implementation was developed for **Exercise 4: Apply Strategy Pattern for Song Generation**, building on the domain layer from Exercise 3.

---

## Project Overview

The system supports the following core flow:

1. A **Creator** registers and logs in via Google OAuth.
2. The creator submits a structured **Form** (title, occasion, genre, mood, tone, vocal style, length, background story).
3. The system generates a **Song** using the active strategy (mock or Suno API).
4. Generated songs appear in the creator's **Library** with live status tracking.
5. Songs can be organized into **Libraries**, shared via token links, downloaded, and toggled public/private.
6. Public songs appear on the **Browse** page for all authenticated users.
7. Credit usage is recorded through **CreditTransaction** on every generation; credits are automatically refunded on failure.
8. Creators can **edit** a song to generate a new version, then choose which version to keep.

---

## Main Features

- **Strategy Pattern** for song generation (mock vs Suno API, swappable via env var)
- **Mock strategy** — offline, deterministic, no API calls required
- **Suno API strategy** — real AI generation via SunoApi.org with webhook callback + background polling
- Google OAuth authentication (Creator and Listener roles)
- Full frontend UI (Django Templates, Tailwind CSS, Alpine.js)
- **Structured generation form** — title, occasion, genre, mood, tone, vocal style, length (2–6 min), background story
- **Review screen** — shows all values and credit cost before confirming generation
- **Real-time status** — history page polls in-progress songs and updates badge live
- **Auto-fail stale songs** — songs stuck generating for > 20 minutes are automatically marked FAILED and credits refunded
- **Content safety labeling** — multi-layer explicit detection: occasion/tone heuristic, text keyword scan, Suno response tags
- **Manual explicit toggle** — creator can override Clean/Explicit label per song
- **Version management** — edit a song, generate new version, side-by-side comparison, choose one to keep (max 2 versions at a time)
- **Delete song** with confirmation modal
- **Song profile page** — full player, song details, background story, tags, accessible by link
- **Share songs** via UUID token links (login required to access)
- **Favorites** — heart songs; dedicated Favourites view in library
- **Filter and sort** library — by status, title A–Z, newest/oldest, search
- **Timestamps** — generation date shown per song
- **Credit refund** — automatic on generation failure (polling timeout, Suno 5xx, callback FAILED)
- **Global audio player** — play/pause, seek, skip ±15s, prev/next queue, volume slider, mute toggle
- **Clickable song titles** — open song profile page with hover animation
- Browse page for public songs with search
- Django admin support

---

## Domain Entities

- **Creator**
- **Listener**
- **Form**
- **Song**
- **Library**
- **Share**
- **CreditTransaction**
- **UserProfile**

---

## Domain Relationships

- One **Creator** → many **Forms**
- One **Creator** → many **Songs**
- One **Creator** → many **Libraries**
- One **Creator** → many **CreditTransactions**
- One **Form** → one **Song**
- One **Song** → optional **parent Song** (version chain, max 2 active at once)
- One **Library** → many **Songs** (M2M)
- One **Song** → many **Shares**
- One **UserProfile** → many favourite **Songs** (M2M)

---

## Song Model Fields

| Field | Description |
|-------|-------------|
| `title` | Song title |
| `status` | PENDING / TEXT_SUCCESS / FIRST_SUCCESS / SUCCESS / FAILED |
| `audio_url` | Playback URL |
| `image_url` | Cover art URL |
| `duration_seconds` | Actual duration |
| `is_public` | Visible on Browse page |
| `is_explicit` | Content safety label (auto-detected + manual override) |
| `version` | Version number (1 = original) |
| `parent_song` | FK to previous version (null for originals) |
| `failure_reason` | Human-readable failure message |
| `task_id` | Suno task ID for polling |
| `created_at` | Generation timestamp |

## Form Model Fields

| Field | Description |
|-------|-------------|
| `requested_title` | Song title |
| `occasion` | Event context (Birthday, Wedding, Party/Nightclub, etc.) |
| `genre` | Music genre dropdown |
| `mood` | Mood dropdown |
| `tone` | Tone dropdown |
| `vocal_style` | Vocal style (Male, Female, Duet, Instrumental Only, etc.) |
| `requested_duration_seconds` | 120–360s (2–6 min) |
| `prompt` | Song description used as AI prompt |
| `background_story` | Stored for display only — not sent to AI |

---

## Project Structure

```text
project_root/
├── app/
│   ├── controllers/
│   │   ├── browse_controller.py
│   │   ├── generation_controller.py
│   │   ├── playback_controller.py
│   │   ├── song_manager_controller.py
│   │   └── user_controller.py
│   │
│   ├── models/
│   │   ├── creator.py
│   │   ├── credit_transaction.py
│   │   ├── form.py
│   │   ├── library.py
│   │   ├── listener.py
│   │   ├── share.py
│   │   ├── song.py
│   │   └── user_profile.py
│   │
│   ├── routes/
│   │   ├── browse_urls.py
│   │   ├── generation_urls.py
│   │   ├── manager_urls.py
│   │   ├── playback_urls.py
│   │   └── user_urls.py
│   │
│   ├── services/
│   │   ├── generation_service.py
│   │   ├── playback_service.py
│   │   ├── song_manager_service.py
│   │   └── user_service.py
│   │
│   ├── strategies/                   ← Strategy Pattern
│   │   ├── base.py                   ← Abstract interface
│   │   ├── factory.py                ← Centralized strategy selection
│   │   ├── mock_strategy.py          ← Offline mock + content classification
│   │   ├── suno_strategy.py          ← Suno API implementation
│   │   └── exceptions.py
│   │
│   ├── templates/
│   │   ├── base.html                 ← Global player, nav, volume control
│   │   ├── home.html
│   │   ├── browse/
│   │   ├── generation/
│   │   ├── manager/
│   │   │   ├── index.html            ← Library, history, edit/delete/compare
│   │   │   └── share.html            ← Song profile / shared link page
│   │   ├── user/
│   │   ├── account/
│   │   └── errors/
│   │
│   ├── migrations/
│   └── ...
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── .gitignore
├── manage.py
└── README.md
```

---

## Class Diagram

![SongGenAI Class Diagram](diagrams/SongGenAI%20Class%20diagram.png)

---

## Sequence Diagrams

### Onboarding
![Onboarding](diagrams/seq_onboarding.png)

### Song Generation — Request
![Generation Request](diagrams/seq_generation_request.png)

### Song Generation — Async Completion
![Generation Async](diagrams/seq_generation_async.png)

### Song Manager — Core
![Song Manager](diagrams/seq_manager.png)

### Song Manager — Share
![Song Manager Share](diagrams/seq_manager_share.png)

### Song Manager — Favourites
![Song Manager Favourites](diagrams/seq_manager_favourite.png)

### Browse & Playback
![Browse Playback](diagrams/seq_browse_playback.png)

---

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/Lemonef/SongGenAI.git
cd SongGenAI
```

### 2. Create and activate a virtual environment

#### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

#### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create a `.env` file

Copy the provided template and fill in your values:

```bash
cp .env.example .env
```

```env
GENERATOR_STRATEGY=mock
SUNO_API_KEY=your_api_key_here
SUNO_CALLBACK_URL=https://your-ngrok-url/generation/suno/callback/
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

Never commit `.env` — it contains secrets. Only `.env.example` is committed.

### 4a. Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project → **APIs & Services** → **Credentials**
3. Click **Create Credentials** → **OAuth 2.0 Client ID**
4. Application type: **Web application**
5. Add to **Authorized redirect URIs**:
   ```
   http://127.0.0.1:8000/accounts/google/login/callback/
   ```
6. Copy the **Client ID** and **Client Secret** into your `.env`
7. After running the server, go to `http://127.0.0.1:8000/admin/` → **Sites** → change `example.com` to `127.0.0.1:8000`

### 5. Apply migrations

```bash
python manage.py migrate
```

### 6. Create a superuser

```bash
python manage.py createsuperuser
```

### 7. Run the application

```bash
python manage.py runserver
```

### 8. Open the application

* Main page: `http://127.0.0.1:8000/`
* Admin page: `http://127.0.0.1:8000/admin/`

---

## Strategy Pattern: Song Generation

This project implements the **Strategy design pattern** to allow swappable song generation behavior without modifying controllers or services.

### Strategy Interface

Defined in `app/strategies/base.py`:

```python
class SongGeneratorStrategy(ABC):
    @abstractmethod
    def generate(self, form) -> Song:
        ...
```

Both strategies implement this same interface.

---

### Running in Mock Mode (Offline)

Set in your `.env` file:

```env
GENERATOR_STRATEGY=mock
```

Then restart the server. Mock mode produces a deterministic song with a fixed placeholder audio URL and classifies `is_explicit` from form fields. No API key or internet connection required.

**Example output:**

```json
{
  "message": "Song created successfully",
  "song_title": "My Song",
  "status": "SUCCESS",
  "audio_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
  "duration_seconds": 372
}
```

---

### Running in Suno Mode (Live API)

Set in your `.env` file:

```env
GENERATOR_STRATEGY=suno
SUNO_API_KEY=your_api_key_here
SUNO_CALLBACK_URL=https://your-ngrok-url/generation/suno/callback/
```

Then restart the server. Suno mode calls `POST https://api.sunoapi.org/api/v1/generate`, stores the returned `taskId`, and updates the song when the callback fires or polling detects completion.

Songs stuck generating for > 20 minutes are automatically marked FAILED and credits refunded.

**Example output (initial response):**

```json
{
  "message": "Song created successfully",
  "song_title": "Fire Run",
  "status": "PENDING",
  "task_id": "abc123xyz",
  "audio_url": null
}
```

Once generation completes, song status updates to `SUCCESS` with a real `audio_url`.

#### Ngrok Setup (required for Suno callbacks on localhost)

1. Download and install [ngrok](https://ngrok.com/download)
2. Run: `ngrok http 8000`
3. Copy the generated HTTPS URL (e.g. `https://abc123.ngrok-free.app`)
4. Set in `.env`: `SUNO_CALLBACK_URL=https://abc123.ngrok-free.app/generation/suno/callback/`
5. Restart the Django server

> Note: ngrok URL changes every session unless you have a paid static domain.

---

### API Key Setup

The Suno API key must **never be committed** to the repository.

1. Create a `.env` file in the project root (already listed in `.gitignore`)
2. Add your key: `SUNO_API_KEY=your_key_here`
3. Obtain a key from [sunoapi.org](https://sunoapi.org)

Settings reads it via:

```python
SUNO_API_KEY = os.environ.get("SUNO_API_KEY", "")
```

---

### Strategy Selection

Selection is centralized in `app/strategies/factory.py`:

```python
def get_generator_strategy() -> SongGeneratorStrategy:
    strategy_name = getattr(settings, "GENERATOR_STRATEGY", "mock").lower()
    if strategy_name == "suno":
        return SunoSongGeneratorStrategy()
    return MockSongGeneratorStrategy()
```

No `if/else` logic is scattered through controllers or services.

---

## Content Safety

Explicit content detection uses multiple layers (applied in order):

| Layer | Rule |
|-------|------|
| Clean occasion | Birthday, Wedding, Children's Party, etc. → always Clean (overrides all below) |
| Explicit occasion | Party / Nightclub → Explicit |
| Explicit tone | Sensual, Aggressive → Explicit |
| Text scan | Keywords in `prompt` or `background_story` → Explicit |
| Suno tags | Response `tags` field scanned for explicit keywords |
| Manual override | Creator can toggle Clean/Explicit on any song |

---

## Version Management

Creators can edit any song to generate a new version:

1. Click **Edit** on a song → pre-filled edit form
2. Modify any field → **Generate New Version**
3. Full-screen generating overlay shows progress
4. On success → side-by-side comparison (changed fields highlighted)
5. Click **Keep this version** on either side → other is deleted, kept song reset to v1
6. Maximum 2 versions exist at any time

---

## Credit Logic

Credits are tracked using **CreditTransaction** rather than a simple balance field.

Supported transaction types:

* `ADD`
* `DEDUCT` — on generation start
* `REFUND` — automatic on failure (polling timeout, Suno 5xx × 3, callback FAILED, stale timeout)

---

## Route Structure

| Prefix | Key endpoints |
|--------|--------------|
| `/` | Home page |
| `/browse/` | Public song browse with search |
| `/generation/` | Form, status polling, Suno callback |
| `/manager/` | History, libraries, shares, delete, edit, version, explicit toggle, song profile |
| `/manager/song/<id>/` | Song profile page |
| `/manager/share/<token>/` | Shared song page (login required) |
| `/playback/` | Global player song data |
| `/user/` | Onboarding, credit balance |
| `/accounts/` | Google OAuth login/logout |

---

## Notes

* Authentication implemented via Google OAuth (django-allauth)
* Real AI generation implemented via Suno API strategy
* Frontend UI implemented with Django Templates, Tailwind CSS, and Alpine.js
* Strategy selection controlled entirely by `GENERATOR_STRATEGY` env var
* `.env` file must never be committed — it contains secrets
* Background polling thread is daemon — auto-fail catches any songs orphaned by server restart

---

## Author

Name: `Sudha Sutaschuto`  
Course: Software Engineering  
Exercise: **Exercise 4 – Apply Strategy Pattern for Song Generation**
