-- Table de faits "compétence demandée par offre" (relation plusieurs-à-plusieurs).
-- Détection par expression régulière sur titre + description, à partir du seed skills.csv.
-- Les frontières (^|[^a-z0-9]) évitent les faux positifs (ex. "java" dans "javascript").

select
    j.job_key,
    s.skill_name,
    s.skill_category
from {{ ref('stg_jobs') }} as j
cross join {{ ref('skills') }} as s
where lower(j.title || ' ' || coalesce(j.description, ''))
    ~ ('(^|[^a-z0-9])(' || s.term || ')($|[^a-z0-9])')
