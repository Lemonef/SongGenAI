import time
import requests
import threading
from django.conf import settings

from .base import SongGeneratorStrategy
from .exceptions import SunoOfflineError, SunoInsufficientCreditsError
from app.models.song import Song
from app.models.credit_transaction import CreditTransaction
from app.services.song_manager_service import refund_credits_if_deducted
from app.strategies.mock_strategy import classify_explicit, CLEAN_OCCASIONS

EXPLICIT_SUNO_TAGS = {
    "explicit", "adult", "nsfw", "sexual", "erotic", "dirty", "profanity",
}
CLEAN_NEGATIVE_TAGS = "explicit lyrics, profanity, adult content, sexual content"


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

        # Pre-classify explicit from user input — refined later by Suno tags on SUCCESS
        from app.strategies.mock_strategy import classify_explicit
        pre_explicit = classify_explicit(form)

        song = Song.objects.create(
            creator=form.creator,
            form=form,
            title=form.requested_title or f"Generated Song {form.id}",
            duration_seconds=form.requested_duration_seconds or 30,
            task_id=task_id,
            is_explicit=pre_explicit,
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

        occasion = getattr(form, "occasion", "General")
        is_clean_occasion = occasion in CLEAN_OCCASIONS

        # Scan all user-typed text fields for explicit keywords
        from app.strategies.mock_strategy import scan_text_explicit, EXPLICIT_KEYWORDS
        text_inputs = " ".join([
            getattr(form, "prompt", "") or "",
            getattr(form, "background_story", "") or "",
        ])
        text_has_explicit = scan_text_explicit(text_inputs)

        # Build negativeTags: always base, +clean guard, +detected keywords for clean occasions
        negative_tags = "Heavy Metal, Upbeat Drums"
        if is_clean_occasion:
            negative_tags += f", {CLEAN_NEGATIVE_TAGS}"
            if text_has_explicit:
                # Add any detected explicit words directly so Suno avoids them
                found = [kw for kw in EXPLICIT_KEYWORDS if kw in text_inputs.lower()]
                if found:
                    negative_tags += ", " + ", ".join(found[:10])  # cap to avoid payload bloat

        # For non-clean occasions with explicit text: tag style so Suno understands intent
        final_style = style_str
        if text_has_explicit and not is_clean_occasion:
            final_style = style_str + ", explicit"

        payload = {
            "prompt": form.prompt,
            "style": final_style,
            "title": form.requested_title or "Untitled Song",
            "model": "V4_5ALL",
            "customMode": True,
            "instrumental": instrumental,
            "callBackUrl": callback_url,
            "negativeTags": negative_tags,
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
        consecutive_errors = 0
        for _ in range(self.MAX_POLLS):
            try:
                time.sleep(self.POLL_INTERVAL_SECONDS)

                # Guard: webhook may have already resolved this song
                song.refresh_from_db()
                if song.status in ("SUCCESS", "FAILED"):
                    print(f"[Suno] Poll skipped — song {song.id} already {song.status} (resolved by webhook)")
                    return

                status, audio_url, image_url, duration, tags = self._fetch_status(song.task_id)
                consecutive_errors = 0

                print(f"[Suno] Poll — task_id={song.task_id}, resolved_status={status}, audio_url={audio_url or 'none'}")

                if audio_url:
                    song.audio_url = audio_url
                if image_url:
                    song.image_url = image_url
                if duration:
                    song.duration_seconds = int(float(duration))
                song.status = status
                song.save()

                if status == "FAILED":
                    refund_credits_if_deducted(song)
                    return
                if status == "SUCCESS":
                    song.is_explicit = classify_explicit(song.form, suno_tags=tags)
                    song.save(update_fields=["is_explicit"])
                    return

            except requests.exceptions.HTTPError as e:
                code = e.response.status_code if e.response is not None else 0
                print(f"[Warning] Suno poll HTTP {code} for task {song.task_id}: {e}")
                if code >= 500:
                    consecutive_errors += 1
                    if consecutive_errors >= 3:
                        song.status = "FAILED"
                        song.failure_reason = f"Suno API returned {code} error after {consecutive_errors} retries."
                        song.save()
                        refund_credits_if_deducted(song)
                        print(f"[Suno] Failing task {song.task_id} due to repeated {code} responses.")
                        return
            except Exception as e:
                consecutive_errors += 1
                print(f"[Warning] Error polling Suno API for task {song.task_id}: {e}")

        # Polling timeout — mark as failed and refund
        song.status = "FAILED"
        song.failure_reason = "Generation timed out after 15 minutes."
        song.save()
        refund_credits_if_deducted(song)
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
        print(f"[Suno] Raw record-info response: {data}")

        records = (data.get("data") or {})
        record = records[0] if isinstance(records, list) and records else records

        # Base status from explicit field (some formats use it)
        raw_status = record.get("status", "") if isinstance(record, dict) else ""

        audio_url = None
        image_url = None
        duration = None
        tags = ""

        if isinstance(record, dict):
            # Modern sunoData format (response.sunoData[])
            resp_obj = record.get("response")
            if isinstance(resp_obj, dict):
                suno_data = resp_obj.get("sunoData") or []
                if isinstance(suno_data, list) and suno_data:
                    audio_url = suno_data[0].get("audioUrl") or suno_data[0].get("audio_url")
                    image_url = suno_data[0].get("imageUrl") or suno_data[0].get("image_url")
                    duration = suno_data[0].get("duration") or suno_data[0].get("audio_duration")
                    tags = suno_data[0].get("tags") or ""

            # clips/songs format
            if not audio_url:
                clips = record.get("clips") or record.get("songs") or []
                if isinstance(clips, list) and clips:
                    audio_url = clips[0].get("audioUrl") or clips[0].get("audio_url")
                    image_url = image_url or clips[0].get("imageUrl") or clips[0].get("image_url")
                    duration = duration or clips[0].get("duration") or clips[0].get("audio_duration")
                    tags = tags or clips[0].get("tags") or ""

            # Callback-style: data.callbackType + data.data[]
            callback_type = record.get("callbackType", "")
            if not audio_url:
                nested = record.get("data") or []
                if isinstance(nested, list) and nested:
                    audio_url = nested[0].get("audio_url") or nested[0].get("audioUrl")
                    image_url = image_url or nested[0].get("image_url") or nested[0].get("imageUrl")
                    duration = duration or nested[0].get("duration")
                    tags = tags or nested[0].get("tags") or ""

        # Resolve final status — priority: audio found > callbackType > raw status field
        if audio_url:
            status = "SUCCESS"
        elif callback_type in ("complete",):
            status = "SUCCESS"
        elif callback_type in ("failed", "error") or raw_status in ("FAILED", "failed", "error"):
            status = "FAILED"
        elif raw_status in ("SUCCESS", "complete", "success"):
            status = "SUCCESS"
        else:
            status = "PENDING"

        return status, audio_url, image_url, duration, tags

