import logging
from app.strategies.mock_strategy import MockSongGeneratorStrategy

logger = logging.getLogger(__name__)

def generate_song_from_form(form, use_mock=False):
    from app.strategies.factory import get_generator_strategy

    if use_mock:
        return MockSongGeneratorStrategy().generate(form)

    strategy = get_generator_strategy()

    if isinstance(strategy, MockSongGeneratorStrategy):
        return strategy.generate(form)

    return strategy.generate(form)