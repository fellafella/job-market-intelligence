select
    published_date,
    role_family,
    count(*) as postings_count
from {{ ref('fct_job_postings') }}
group by 1, 2
