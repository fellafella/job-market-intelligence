-- Demande par compétence, famille de métier et mois.
-- pct_of_postings = part des offres du segment qui citent la compétence.

with postings as (

    select
        job_key,
        role_family,
        date_trunc('month', published_date)::date as posting_month
    from {{ ref('fct_job_postings') }}

),

totals as (

    select role_family, posting_month, count(*) as total_postings
    from postings
    group by 1, 2

),

skill_counts as (

    select
        p.role_family,
        p.posting_month,
        s.skill_name,
        s.skill_category,
        count(distinct s.job_key) as postings_with_skill
    from {{ ref('fct_job_skills') }} as s
    inner join postings as p on p.job_key = s.job_key
    group by 1, 2, 3, 4

)

select
    c.role_family,
    c.posting_month,
    c.skill_name,
    c.skill_category,
    c.postings_with_skill,
    t.total_postings,
    round(100.0 * c.postings_with_skill / t.total_postings, 1) as pct_of_postings
from skill_counts as c
inner join totals as t
    on t.role_family = c.role_family
    and t.posting_month = c.posting_month
