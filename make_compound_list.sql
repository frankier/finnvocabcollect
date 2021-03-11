SELECT DISTINCT(headword.name)
FROM headword
  JOIN etymology ON headword.id = etymology.headword_id
  JOIN derivation ON derivation.etymology_id = etymology.id
WHERE derivation.type = "compound"
ORDER BY headword.name;
