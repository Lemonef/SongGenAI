import time
import requests
import threading
from django.conf import settings

from .base import SongGeneratorStrategy
from app.models.song import Song
from app.models.credit_transaction import CreditTransaction


class SunoSongGeneratorStrategy(SongGeneratorStrategy):
    BASE_URL = "https://api.sunoapi.org/api/v1"
    POLL_INTERVAL_SECONDS = 5
    MAX_POLLS = 60  # up to 5 minutes of polling

    def _headers(self):
        return {
            "Authorization": f"Bearer {settings.SUNO_API_KEY}",
            "Content-Type": "application/json",
        }

    def generate(self, form) -> Song:
        if hasattr(form, "song"):
            return form.song

        task_id = self._create_task(form)

        song = Song.objects.create(
            creator=form.creator,
            form=form,
            title=form.requested_title or f"Generated Song {form.id}",
            duration_seconds=form.requested_duration_seconds or 30,
            task_id=task_id,
            status="PENDING",
        )

        CreditTransaction.objects.create(
            creator=form.creator,
            form=form,
            song=song,
            transaction_type="DEDUCT",
            amount=1,
            note="Suno song generation",
        )

        # Poll in background thread to avoid blocking the request
        thread = threading.Thread(target=self._poll_until_done, args=(song,), daemon=True)
        thread.start()
        
        return song

    def _create_task(self, form) -> str:
        callback_url = getattr(settings, "SUNO_CALLBACK_URL", "")
        if not callback_url:
            raise ValueError(
                "SUNO_CALLBACK_URL is not configured. Please set settings.SUNO_CALLBACK_URL or environment variable SUNO_CALLBACK_URL."
            )

        payload = {
            "prompt": form.prompt,
            "style": f"{form.genre} {form.mood}",
            "title": form.requested_title or "Untitled Song",
            "model": "V4_5ALL",
            "customMode": True,
            "instrumental": True,
            "callBackUrl": callback_url,
            "negativeTags": "Heavy Metal, Upbeat Drums",
            "vocalGender": "m",
            "styleWeight": 0.65,
            "weirdnessConstraint": 0.65,
            "audioWeight": 0.65,
        }
        response = None
        try:
            response = requests.post(
                f"{self.BASE_URL}/generate",
                json=payload,
                headers=self._headers(),
                timeout=30,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise ValueError(
                f"Suno API request failed: {e}. Status: {getattr(response, 'status_code', 'unknown')}"
            )
        
        data = response.json()
        task_id = (data.get("data") or {}).get("taskId") or data.get("taskId")
        if not task_id:
            raise ValueError(f"No taskId in Suno response: {data}")
        return task_id

    def _poll_until_done(self, song: Song):
        for _ in range(self.MAX_POLLS):
            try:
                time.sleep(self.POLL_INTERVAL_SECONDS)
                status, audio_url = self._fetch_status(song.task_id)
                song.status = status
                if audio_url:
                    song.audio_url = audio_url
                song.save()
                if status in ("SUCCESS", "FAILED"):
                    return
            except Exception as e:
                # Catch exception inside the loop so we don't prematurely marking the song as FAILED
                print(f"[Warning] Error polling Suno API for task {song.task_id}: {e}")
        
        # If polling loop finishes and it's still not successful/failed, mark as failed
        song.status = "FAILED"
        song.save()
        print(f"Max polling reached for task {song.task_id}. Marked as FAILED.")

    def _fetch_status(self, task_id: str):
        response = requests.get(
            f"{self.BASE_URL}/generate/record-info",
            params={"taskId": task_id},
            headers=self._headers(),
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        records = (data.get("data") or {})
        record = records[0] if isinstance(records, list) and records else records

        status = record.get("status", "PENDING") if isinstance(record, dict) else "PENDING"

        audio_url = None
        
        # Extract audio_url handling both old (clips/songs) and new (response.sunoData) formats
        if isinstance(record, dict):
            # Check for the modern sunoData format
            resp_obj = record.get("response")
            if isinstance(resp_obj, dict):
                suno_data = resp_obj.get("sunoData") or []
                if isinstance(suno_data, list) and suno_data:
                    audio_url = suno_data[0].get("audioUrl") or suno_data[0].get("audio_url")
            
            # Fallback to old format
            if not audio_url:
                clips = record.get("clips") or record.get("songs") or []
                if isinstance(clips, list) and clips:
                    audio_url = clips[0].get("audioUrl") or clips[0].get("audio_url")

        return status, audio_url

