import time
import requests
import threading
from django.conf import settings

from .base import SongGeneratorStrategy
from .exceptions import SunoOfflineError, SunoInsufficientCreditsError
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

        print(f"[Suno] Task created — task_id={task_id}, song_id={song.id}, title='{song.title}', status={song.status}")

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

        vocal_style = getattr(form, "vocal_style", "Any")
        instrumental = (vocal_style == "Instrumental Only")
        vocal_gender_map = {"Male": "m", "Female": "f", "Duet": "m", "Rap": "m"}
        vocal_gender = vocal_gender_map.get(vocal_style, "m")

        tone = getattr(form, "tone", "")
        occasion = getattr(form, "occasion", "")
        style_parts = [form.genre, form.mood]
        if tone and tone not in ("Neutral", "Any"):
            style_parts.append(tone)
        if occasion and occasion not in ("General", "Any"):
            style_parts.append(occasion)
        style_str = ", ".join(style_parts)

        payload = {
            "prompt": form.prompt,
            "style": style_str,
            "title": form.requested_title or "Untitled Song",
            "model": "V4_5ALL",
            "customMode": True,
            "instrumental": instrumental,
            "callBackUrl": callback_url,
            "negativeTags": "Heavy Metal, Upbeat Drums",
            "vocalGender": vocal_gender,
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
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            raise SunoOfflineError("Cannot reach Suno API — check your internet connection.")
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Suno API request failed: {e}")

        if response.status_code == 402:
            raise SunoInsufficientCreditsError("Suno API credits are exhausted.")

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise ValueError(f"Suno API request failed: {e}. Status: {response.status_code}")

        data = response.json()

        credit_keywords = ("credit", "insufficient", "balance", "quota")
        combined_msg = " ".join(
            str(data.get(k) or "") for k in ("msg", "message", "error")
        ).lower()
        if data.get("code") == 429 or any(k in combined_msg for k in credit_keywords):
            raise SunoInsufficientCreditsError("Suno API credits are exhausted.")

        inner = data.get("data") or {}
        task_id = (
            inner.get("taskId") or inner.get("task_id")
            or data.get("taskId") or data.get("task_id")
        )
        if not task_id:
            raise ValueError(f"No taskId in Suno response: {data}")
        return task_id

    def _poll_until_done(self, song: Song):
        for _ in range(self.MAX_POLLS):
            try:
                time.sleep(self.POLL_INTERVAL_SECONDS)
                status, audio_url, image_url, duration = self._fetch_status(song.task_id)
                song.status = status
                if audio_url:
                    song.audio_url = audio_url
                if image_url:
                    song.image_url = image_url
                if duration:
                    song.duration_seconds = int(float(duration))
                song.save()
                print(f"[Suno] Poll update — task_id={song.task_id}, status={status}, audio_url={audio_url or 'pending'}")
                if status in ("SUCCESS", "FAILED"):
                    return
            except Exception as e:
                # Catch exception inside the loop so we don't prematurely marking the song as FAILED
                print(f"[Warning] Error polling Suno API for task {song.task_id}: {e}")
        
        # Polling timeout — mark as failed
        song.status = "FAILED"
        song.failure_reason = "Generation timed out after 15 minutes."
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
        image_url = None
        duration = None

        if isinstance(record, dict):
            # Modern sunoData format
            resp_obj = record.get("response")
            if isinstance(resp_obj, dict):
                suno_data = resp_obj.get("sunoData") or []
                if isinstance(suno_data, list) and suno_data:
                    audio_url = suno_data[0].get("audioUrl") or suno_data[0].get("audio_url")
                    image_url = suno_data[0].get("imageUrl") or suno_data[0].get("image_url")
                    duration = suno_data[0].get("duration") or suno_data[0].get("audio_duration")

            # clips/songs format
            if not audio_url:
                clips = record.get("clips") or record.get("songs") or []
                if isinstance(clips, list) and clips:
                    audio_url = clips[0].get("audioUrl") or clips[0].get("audio_url")
                    image_url = image_url or clips[0].get("imageUrl") or clips[0].get("image_url")
                    duration = duration or clips[0].get("duration") or clips[0].get("audio_duration")

            # Callback-style: record has nested data[] array
            if not audio_url:
                nested = record.get("data") or []
                if isinstance(nested, list) and nested:
                    audio_url = nested[0].get("audio_url") or nested[0].get("audioUrl")
                    image_url = image_url or nested[0].get("image_url") or nested[0].get("imageUrl")
                    duration = duration or nested[0].get("duration")
                if audio_url:
                    status = "SUCCESS"

        return status, audio_url, image_url, duration

