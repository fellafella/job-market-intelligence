with skills as (

    select job_key, count(*) as skills_count
    from {{ ref('fct_job_skills') }}
    group by 1

)

select
    j.job_key,
    md5(lower(trim(j.company_name)))                         as company_id,
    j.published_at::date                                     as published_date,
    j.title,
    j.role_family,
    j.seniority,
    j.job_type,
    j.location,
    j.salary_currency,
    j.salary_min,
    j.salary_max,
    (j.salary_min + j.salary_max) / 2                        as salary_mid,
    coalesce(s.skills_count, 0)                              as skills_count,
    j.job_url
from {{ ref('stg_jobs') }} as j
left join skills as s on s.job_key = j.job_key
