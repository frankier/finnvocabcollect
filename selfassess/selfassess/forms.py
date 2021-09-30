from .database import Participant, ParticipantLanguage
from wtforms_alchemy import ModelForm, ModelFieldList
from .quali import ProofAge, ProofType
from itertools import chain
from wtforms import SelectField, FormField, ValidationError, Field, RadioField
from wtforms.widgets import TextInput
import langcodes
from werkzeug.datastructures import ImmutableMultiDict


class LanguageField(Field):
    widget = TextInput()

    def _value(self):
        if self.object_data:
            return langcodes.get(self.object_data).language_name()
        elif self.data:
            return langcodes.get(self.data).language_name()
        else:
            return ""

    def process_formdata(self, value):
        if value and value[0]:
            try:
                self.data = langcodes.find(value[0]).language
            except LookupError:
                self.data = None
        else:
            self.data = None


def choices_of_enum(en):
    return [(member.value, name.capitalize()) for name, member in en.__members__.items()]


class ParticipantLanguageForm(ModelForm):
    class Meta:
        model = ParticipantLanguage
        only = [
            "language",
            "level",
        ]
        strip_string_fields = True

    def validate_langauge(form, field):
        try:
            langcodes.find(field.data)
        except LookupError:
            raise ValidationError(
                f"Could not find language {field.data}. "
                "Please check your spelling or remove."
            )

    language = LanguageField()


def group_languages(formdata):
    grouped = {}
    for k, v in formdata.items(multi=True):
        if not k.startswith("languages-"):
            continue
        _, num, field = k.split("-", 2)
        num = int(num)
        grouped.setdefault(num, {})[field] = v
    return grouped


def remove_empty_languages(formdata):
    grouped = group_languages(formdata)
    exclude_keys = set()
    for field_num, field_dict in grouped.items():
        if not field_dict["language"]:
            exclude_keys.update((
                f"languages-{field_num}-{field}"
                for field in field_dict
            ))
    return ImmutableMultiDict(
        ((k, v) for k, v in formdata.items(multi=True) if k not in exclude_keys),
    )


class ParticipantForm(ModelForm):
    class Meta:
        model = Participant
        only = [
            "given_name",
            "surname",
            "lived_in_finland",
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

    proof_type = RadioField("Type of proof", choices=[
        ("yki_intermediate", "YKI (Intermediate level)"),
        ("yki_advanced", "YKI (Advanced level)"),
        (
            "course_english_degree",
            "Short course completed as part of primarily non-Finnish degree "
            "(e.g. international degree programme in English)"
        ),
        (
            "freestanding_course",
            "Free-standing short course "
            "(e.g. at an Adult Education Center)"
        ),
        (
            "completed_finnish_upper_secondary",
            "Upper secondary school or vocational school completed in Finnish"
        ),
        (
            "completed_finnish_degree",
            "University or University of Applied Science degree completed in Finnish"
        ),
        ("other", "Other proof"),
    ])
    proof_age = SelectField("Age of proof", choices=[
        ("lt1", "Less than 1 year"),
        ("lt3", "Less than 3 years"),
        ("lt5", "Less than 5 years"),
        ("gte5", "5 or more years"),
    ])

    def process(self, formdata=None, obj=None, data=None, **kwargs):
        if formdata is not None:
            formdata = remove_empty_languages(formdata)
        return super().process(formdata=formdata, obj=obj, data=data, **kwargs)
