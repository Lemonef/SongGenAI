from abc import ABC, abstractmethod


class SongGeneratorStrategy(ABC):
    @abstractmethod
    def generate(self, form) -> "Song":
        """Generate a song from a Form instance. Returns a saved Song."""
        pass
