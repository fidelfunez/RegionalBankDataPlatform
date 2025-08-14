{{
  config(
    materialized='view',
    tags=['staging', 'economic']
  )
}}

with source as (
    select * from {{ source('raw', 'economic_indicators') }}
),

cleaned as (
    select
        -- Primary keys
        country_code,
        indicator_code,
        year,
        month,
        
        -- Dimensions
        trim(upper(country_code)) as country_code_clean,
        trim(country_name) as country_name,
        trim(upper(indicator_code)) as indicator_code_clean,
        trim(indicator_name) as indicator_name,
        
        -- Measures
        cast(value as decimal(18,4)) as value,
        trim(unit) as unit,
        
        -- Metadata
        source,
        last_updated,
        current_timestamp as processed_at
        
    from source
    where 
        -- Data quality filters
        country_code is not null
        and indicator_code is not null
        and value is not null
        and year is not null
        and month is not null
        and month between 1 and 12
        and year between 2000 and extract(year from current_date) + 1
),

final as (
    select
        country_code_clean as country_code,
        country_name,
        indicator_code_clean as indicator_code,
        indicator_name,
        value,
        unit,
        year,
        month,
        source,
        last_updated,
        processed_at,
        
        -- Derived fields
        case 
            when indicator_code_clean like 'GDP%' then 'GDP'
            when indicator_code_clean like 'INFL%' then 'Inflation'
            when indicator_code_clean like 'EXCH%' then 'Exchange Rate'
            when indicator_code_clean like 'INT%' then 'Interest Rate'
            when indicator_code_clean like 'UNEMP%' then 'Unemployment'
            else 'Other'
        end as indicator_category,
        
        -- Date fields
        date_trunc('month', date(year || '-' || month || '-01')) as month_date,
        year * 100 + month as year_month
        
    from cleaned
)

select * from final
