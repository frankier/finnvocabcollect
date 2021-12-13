MARKER_COMPARE_QUERY = """
select
    miniexam_response.participant_id,
    participant_language.language,
    miniexam_mark_ann1.mark as mark1,
    miniexam_mark_ann2.mark as mark2
from miniexam_response
join miniexam_mark as miniexam_mark_ann1
    on miniexam_mark_ann1.selfassess_response_id = miniexam_response.id
join miniexam_mark as miniexam_mark_ann2
    on miniexam_mark_ann2.selfassess_response_id = miniexam_response.id
join participant_language
    on miniexam_response.participant_id = participant_language.participant_id
where
    participant_language.level = 7
    and miniexam_mark_ann1.marker = 'ann1'
    and miniexam_mark_ann2.marker = 'ann2';
"""

MARK_TRANSLATION_COMPARE_QUERY = """
select
    selfassess_session.participant_id,
    participant_language.language,
    miniexam_response.word,
    selfassess_response.rating,
    miniexam_mark.marker,
    miniexam_mark.mark
from selfassess_session
join selfassess_response
    on selfassess_session.id = selfassess_response.session_id
join miniexam_response
    on selfassess_session.participant_id = miniexam_response.participant_id
    and miniexam_response.word = selfassess_response.word
join miniexam_mark
    on miniexam_mark.selfassess_response_id = miniexam_response.id
join participant_language
    on selfassess_session.participant_id = participant_language.participant_id
where
    participant_language.level = 7;
"""
