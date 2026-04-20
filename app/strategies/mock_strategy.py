from .base import SongGeneratorStrategy
from app.models.song import Song
from app.models.credit_transaction import CreditTransaction


class MockSongGeneratorStrategy(SongGeneratorStrategy):
    PLACEHOLDER_AUDIO_URL = (
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
    )

    def generate(self, form) -> Song:
        if hasattr(form, "song"):
            return form.song

        song = Song.objects.create(
            creator=form.creator,
            form=form,
            title=form.requested_title or f"Generated Song {form.id}",
            duration_seconds=form.requested_duration_seconds or 30,
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

        return song
