from typing import Mapping

class LanguageLevel:
    """Class which stores the language and the level associated with the user"""

    """Map n value (mother tongue language level) into 6 (greater than each possibile value into Babel teamplate)"""
    MOTHER_TONGUE_LEVEL = 6

    """The pair language name and level of knowledge"""
    def __init__(self, lang: str, level: int):
        self.lang = lang.strip().lower()
        self.level = level

    def to_dict(self) -> Mapping:
        return  {'lang': self.lang, 'level': self.level}
    
    def __lt__(self, other) -> bool:
        if self.lang == other.lang:
            return self.level < other.level
        return self.lang < other.lang

    def __eq__(self, other) -> bool:
        return self.lang == other.lang and self.level == other.level

    def __repr__(self) -> str:
        return 'lang: {}; level: {}'.format(self.lang, self.level)