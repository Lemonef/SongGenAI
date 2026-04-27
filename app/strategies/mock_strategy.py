from .base import SongGeneratorStrategy
from app.models.song import Song
from app.models.credit_transaction import CreditTransaction


class MockSongGeneratorStrategy(SongGeneratorStrategy):
    PLACEHOLDER_AUDIO_URL = (
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
    )
    PLACEHOLDER_AUDIO_DURATION = 372  # actual duration of SoundHelix-Song-1.mp3

    def generate(self, form) -> Song:
        if hasattr(form, "song"):
            return form.song

        song = Song.objects.create(
            creator=form.creator,
            form=form,
            title=form.requested_title or f"Generated Song {form.id}",
            duration_seconds=self.PLACEHOLDER_AUDIO_DURATION,
            audio_url=self.PLACEHOLDER_AUDIO_URL,
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

        print(f"[Mock] Song generated — id={song.id}, title='{song.title}', status={song.status}, audio_url={song.audio_url}")
        return song
