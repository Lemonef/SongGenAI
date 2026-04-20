
def generate_song_from_form(form):
    from app.strategies.factory import get_generator_strategy
    strategy = get_generator_strategy()
    return strategy.generate(form)