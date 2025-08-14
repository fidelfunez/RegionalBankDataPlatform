{{
  config(
    materialized='table',
    tags=['core', 'dimension', 'scd_type2']
  )
}}

with demographic_data as (
    select 
        country_code,
        country_name,
        population,
        gdp_per_capita,
        literacy_rate,
        life_expectancy,
        urban_population_pct,
        development_index,
        population_category,
        income_category,
        year,
        source,
        last_updated,
        processed_at
    from {{ ref('stg_demographic_data') }}
),

-- Get the latest record for each country
latest_records as (
    select 
        country_code,
        country_name,
        population,
        gdp_per_capita,
        literacy_rate,
        life_expectancy,
        urban_population_pct,
        development_index,
        population_category,
        income_category,
        year,
        source,
        last_updated,
        processed_at,
        row_number() over (
            partition by country_code 
            order by year desc, last_updated desc nulls last
        ) as rn
    from demographic_data
),

current_data as (
    select 
        country_code,
        country_name,
        population,
        gdp_per_capita,
        literacy_rate,
        life_expectancy,
        urban_population_pct,
        development_index,
        population_category,
        income_category,
        year,
        source,
        last_updated,
        processed_at
    from latest_records
    where rn = 1
),

-- Get existing dimension data
existing_dim as (
    select 
        country_sk,
        country_code,
        country_name,
        population,
        gdp_per_capita,
        literacy_rate,
        life_expectancy,
        urban_population_pct,
        development_index,
        population_category,
        income_category,
        year,
        source,
        effective_date,
        end_date,
        is_current
    from {{ this }}
    where is_current = true
),

-- Identify changes
changes as (
    select 
        c.country_code,
        c.country_name,
        c.population,
        c.gdp_per_capita,
        c.literacy_rate,
        c.life_expectancy,
        c.urban_population_pct,
        c.development_index,
        c.population_category,
        c.income_category,
        c.year,
        c.source,
        c.last_updated,
        c.processed_at,
        e.country_sk,
        case 
            when e.country_sk is null then 'INSERT'
            when c.country_name != e.country_name 
                or c.population != e.population
                or c.gdp_per_capita != e.gdp_per_capita
                or c.literacy_rate != e.literacy_rate
                or c.life_expectancy != e.life_expectancy
                or c.urban_population_pct != e.urban_population_pct
                or c.development_index != e.development_index
                or c.population_category != e.population_category
                or c.income_category != e.income_category
            then 'UPDATE'
            else 'NO_CHANGE'
        end as change_type
    from current_data c
    left join existing_dim e on c.country_code = e.country_code
),

-- Generate new records
new_records as (
    select 
        case 
            when change_type = 'INSERT' then 
                {{ dbt_utils.generate_surrogate_key(['country_code']) }}
            else 
                country_sk
        end as country_sk,
        country_code,
        country_name,
        population,
        gdp_per_capita,
        literacy_rate,
        life_expectancy,
        urban_population_pct,
        development_index,
        population_category,
        income_category,
        year,
        source,
        case 
            when change_type = 'INSERT' then coalesce(last_updated, processed_at)
            else last_updated
        end as effective_date,
        case 
            when change_type in ('INSERT', 'UPDATE') then '9999-12-31'::date
            else end_date
        end as end_date,
        case 
            when change_type in ('INSERT', 'UPDATE') then true
            else false
        end as is_current,
        processed_at
    from changes
    where change_type in ('INSERT', 'UPDATE')
),

-- Update existing records (set end_date for current records that are being updated)
update_existing as (
    select 
        country_sk,
        country_code,
        country_name,
        population,
        gdp_per_capita,
        literacy_rate,
        life_expectancy,
        urban_population_pct,
        development_index,
        population_category,
        income_category,
        year,
        source,
        effective_date,
        case 
            when change_type = 'UPDATE' then current_date - 1
            else end_date
        end as end_date,
        case 
            when change_type = 'UPDATE' then false
            else is_current
        end as is_current
    from existing_dim e
    inner join changes c on e.country_code = c.country_code
    where c.change_type = 'UPDATE'
),

-- Keep unchanged records
unchanged_records as (
    select 
        country_sk,
        country_code,
        country_name,
        population,
        gdp_per_capita,
        literacy_rate,
        life_expectancy,
        urban_population_pct,
        development_index,
        population_category,
        income_category,
        year,
        source,
        effective_date,
        end_date,
        is_current
    from existing_dim e
    inner join changes c on e.country_code = c.country_code
    where c.change_type = 'NO_CHANGE'
),

-- Union all records
final as (
    select * from new_records
    union all
    select 
        country_sk,
        country_code,
        country_name,
        population,
        gdp_per_capita,
        literacy_rate,
        life_expectancy,
        urban_population_pct,
        development_index,
        population_category,
        income_category,
        year,
        source,
        effective_date,
        end_date,
        is_current
    from update_existing
    union all
    select 
        country_sk,
        country_code,
        country_name,
        population,
        gdp_per_capita,
        literacy_rate,
        life_expectancy,
        urban_population_pct,
        development_index,
        population_category,
        income_category,
        year,
        source,
        effective_date,
        end_date,
        is_current
    from unchanged_records
)

select * from final
