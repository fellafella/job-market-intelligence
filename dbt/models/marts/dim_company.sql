select
    md5(lower(trim(company_name)))  as company_id,
    min(company_name)               as company_name,
    count(*)                        as postings_count,
    min(published_at)::date         as first_posting_date,
    max(published_at)::date         as last_posting_date
from {{ ref('stg_jobs') }}
group by 1
