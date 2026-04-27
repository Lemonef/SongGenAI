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


def classify_explicit(form) -> bool:
    occasion = getattr(form, "occasion", "General")
    tone = getattr(form, "tone", "Neutral")
    if occasion in CLEAN_OCCASIONS:
        return False
    if occasion in EXPLICIT_OCCASIONS or tone in EXPLICIT_TONES:
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
