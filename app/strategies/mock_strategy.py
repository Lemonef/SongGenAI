from .base import SongGeneratorStrategy
from app.models.song import Song
from app.models.credit_transaction import CreditTransaction

CLEAN_OCCASIONS = {
    "Birthday", "Wedding", "Graduation", "Christmas",
    "Valentine's Day", "Anniversary", "Children's Party",
    "Funeral / Memorial", "Meditation / Relaxation",
}
EXPLICIT_TONES = {"Sensual", "Aggressive"}
EXPLICIT_OCCASIONS = {"Party / Nightclub"}

EXPLICIT_KEYWORDS = {
    "sex", "sexy", "sexual", "fuck", "fucking", "shit", "bitch", "ass",
    "dick", "pussy", "cock", "naked", "nude", "explicit", "adult", "nsfw",
    "porn", "erotic", "horny", "orgasm", "breast", "nipple", "penis",
    "vagina", "masturbat", "foreplay", "bondage", "fetish", "stripper",
    "seduct", "lust", "lustful", "kinky",
}


def scan_text_explicit(text: str) -> bool:
    if not text:
        return False
    lower = text.lower()
    return any(kw in lower for kw in EXPLICIT_KEYWORDS)


def classify_explicit(form, suno_tags: str = "") -> bool:
    occasion = getattr(form, "occasion", "General")
    tone = getattr(form, "tone", "Neutral")

    # Clean occasions always override — no explicit regardless of other fields
    if occasion in CLEAN_OCCASIONS:
        return False

    # Occasion or tone explicitly signals adult content
    if occasion in EXPLICIT_OCCASIONS or tone in EXPLICIT_TONES:
        return True

    # Scan user-typed text fields
    text = " ".join([
        getattr(form, "prompt", "") or "",
        getattr(form, "background_story", "") or "",
    ])
    if scan_text_explicit(text):
        return True

    # Suno response tags (e.g. "explicit, adult, rock")
    if suno_tags and scan_text_explicit(suno_tags):
        return True

    return False


class MockSongGeneratorStrategy(SongGeneratorStrategy):
    PLACEHOLDER_AUDIO_URL = (
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
    )
    PLACEHOLDER_AUDIO_DURATION = 372  # actual duration of SoundHelix-Song-1.mp3

    def generate(self, form) -> Song:
        if hasattr(form, "song"):
            return form.song

        is_explicit = classify_explicit(form)

        song = Song.objects.create(
            creator=form.creator,
            form=form,
            title=form.requested_title or f"Generated Song {form.id}",
            duration_seconds=self.PLACEHOLDER_AUDIO_DURATION,
            audio_url=self.PLACEHOLDER_AUDIO_URL,
            is_explicit=is_explicit,
            status="SUCCESS",
        )

        CreditTransaction.objects.create(
            creator=form.creator,
            form=form,
            song=song,
            transaction_type="DEDUCT",
            amount=1,
            note="Mock song generation",
        )

        print(f"[Mock] Song generated — id={song.id}, title='{song.title}', explicit={is_explicit}, status={song.status}")
        return song
