-- Une ligne par offre : dernière version collectée, JSON déplié, HTML retiré,
-- salaire analysé (devise, min, max), famille de métier et séniorité déduites du titre.

with latest as (

    select
        *,
        row_number() over (
            partition by source, job_id
            order by extracted_at desc
        ) as rn
    from {{ source('raw', 'jobs_raw') }}

),

parsed as (

    select
        md5(source || '-' || job_id)                         as job_key,
        source,
        job_id,
        extracted_at,
        trim(payload ->> 'title')                            as title,
        trim(payload ->> 'company_name')                     as company_name,
        payload ->> 'category'                               as category,
        payload ->> 'job_type'                               as job_type,
        payload ->> 'candidate_required_location'            as location,
        nullif(trim(payload ->> 'salary'), '')               as salary_raw,
        payload ->> 'url'                                    as job_url,
        (payload ->> 'publication_date')::timestamp          as published_at,
        regexp_replace(
            coalesce(payload ->> 'description', ''), '<[^>]+>', ' ', 'g'
        )                                                    as description
    from latest
    where rn = 1

),

salary as (

    select
        p.*,
        case
            when p.salary_raw like '%€%' then 'EUR'
            when p.salary_raw like '%£%' then 'GBP'
            when p.salary_raw like '%$%' then 'USD'
        end                                                  as salary_currency,
        s.salary_min,
        s.salary_max
    from parsed p
    left join lateral (
        -- "$80k - $100k" -> 80000 / 100000 ; les nombres < 1000 sont ignorés (bruit)
        select min(val) as salary_min, max(val) as salary_max
        from (
            select
                (m[1])::numeric * case when lower(m[2]) = 'k' then 1000 else 1 end as val
            from regexp_matches(
                replace(coalesce(p.salary_raw, ''), ',', ''),
                '(\d+(?:\.\d+)?)\s*([kK])?',
                'g'
            ) as m
        ) v
        where val >= 1000
    ) s on true

)

select
    job_key,
    source,
    job_id,
    title,
    company_name,
    category,
    job_type,
    location,
    job_url,
    published_at,
    extracted_at,
    description,
    salary_raw,
    salary_currency,
    salary_min,
    salary_max,

    case
        when title ~* 'analytics engineer'                                   then 'Analytics Engineer'
        when title ~* 'data engineer|data platform|dataops|etl developer'    then 'Data Engineer'
        when title ~* 'data scien'                                           then 'Data Scientist'
        when title ~* 'machine learning|ml engineer|ai engineer|mlops'       then 'ML / AI Engineer'
        when title ~* 'analyst|business intelligence'                        then 'Data Analyst'
        else 'Other'
    end                                                      as role_family,

    case
        when title ~* 'principal|staff|lead|head of|director'                then 'Lead+'
        when title ~* 'senior|sr[. ]'                                        then 'Senior'
        when title ~* 'junior|jr[. ]|intern|graduate|entry'                  then 'Junior'
        else 'Mid'
    end                                                      as seniority

from salary
