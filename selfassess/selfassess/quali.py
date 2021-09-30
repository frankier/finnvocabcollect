import enum


class ProofType(enum.Enum):
    yki_intermediate = 1
    yki_advanced = 2
    other = 3
    course_english_degree = 4
    completed_finnish_upper_secondary = 5
    completed_finnish_degree = 6


class ProofAge(enum.Enum):
    lt1 = 1
    lt3 = 2
    lt5 = 3
    gte5 = 4


CEFR_SKILLS = [
    "speaking",
    "writing",
    "listening_comprehension",
    "reading_comprehension",
]

CEFR_LEVELS = ["a1", "a2", "b1", "b2", "c1", "c2"]
CEFR_LEVELS_NATIVE = CEFR_LEVELS + ["native"]
