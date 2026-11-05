-- Salaires annoncés par famille de métier, séniorité et devise (jamais de mélange de devises).

select
    role_family,
    seniority,
    salary_currency,
    count(*)                                                   as postings_with_salary,
    round(avg(salary_mid))                                     as avg_salary,
    round(percentile_cont(0.5) within group (order by salary_mid)::numeric) as median_salary,
    min(salary_min)                                            as min_salary,
    max(salary_max)                                            as max_salary
from {{ ref('fct_job_postings') }}
where salary_mid is not null
  and salary_currency is not null
group by 1, 2, 3
