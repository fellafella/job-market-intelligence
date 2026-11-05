-- Test singulier : une fourchette salariale doit avoir min <= max.
-- Toute ligne renvoyée fait échouer le test.
select job_key, salary_min, salary_max
from {{ ref('fct_job_postings') }}
where salary_min > salary_max
