from app.models import Song, CreditTransaction


def create_mock_song_from_form(form):
    if hasattr(form, "song"):
        return form.song

    song = Song.objects.create(
        creator=form.creator,
        form=form,
        title=form.requested_title or f"Generated Song {form.id}",
        duration_seconds=form.requested_duration_seconds or 30,
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