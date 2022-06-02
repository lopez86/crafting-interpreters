class LoxObject:
    def __init__(self) -> None:
        """Top level LoxObject for literals."""
        pass

    def __str__(self) -> str:
        return "LoxObject."

    def equals(self, other: "LoxObject") -> bool:
        return self is other
