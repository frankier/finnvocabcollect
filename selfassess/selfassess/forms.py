from .database import Participant
from wtforms_alchemy import ModelForm
from .quali import ProofAge, ProofType
from wtforms import SelectField


def choices_of_enum(en):
    return [(member.value, name.capitalize()) for name, member in en.__members__.items()]


class ParticipantForm(ModelForm):
    class Meta:
        model = Participant
        only = [
            "given_name",
            "surname",
            "proof_type",
            "proof_age",
            "cefr_proof_speaking",
            "cefr_proof_writing",
            "cefr_proof_listening_comprehension",
            "cefr_proof_reading_comprehension",
            "cefr_selfassess_speaking",
            "cefr_selfassess_writing",
            "cefr_selfassess_listening_comprehension",
            "cefr_selfassess_reading_comprehension",
            "text_on_proof",
        ]

    proof_type = SelectField("Type of proof", choices=[
        ("yki_intermediate", "YKI (Intermediate level)"),
        ("yki_advanced", "YKI (Advanced level)"),
        ("other", "Other proof"),
    ])
    proof_age = SelectField("Age of proof", choices=[
        ("lt1", "Less than 1 year"),
        ("lt3", "Less than 3 years"),
        ("lt5", "Less than 5 years"),
        ("gte5", "5 or more years"),
    ])
