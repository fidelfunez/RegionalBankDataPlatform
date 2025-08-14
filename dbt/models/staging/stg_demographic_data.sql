{{
  config(
    materialized='view',
    tags=['staging', 'demographic']
  )
}}

with source as (
    select * from {{ source('raw', 'demographic_data') }}
),

cleaned as (
    select
        -- Primary keys
        country_code,
        year,
        
        -- Dimensions
        trim(upper(country_code)) as country_code_clean,
        trim(country_name) as country_name,
        
        -- Measures
        cast(population as bigint) as population,
        cast(gdp_per_capita as decimal(18,2)) as gdp_per_capita,
        cast(literacy_rate as decimal(5,2)) as literacy_rate,
        cast(life_expectancy as decimal(5,2)) as life_expectancy,
        cast(urban_population_pct as decimal(5,2)) as urban_population_pct,
        
        -- Metadata
        source,
        last_updated,
        current_timestamp as processed_at
        
    from source
    where 
        -- Data quality filters
        country_code is not null
        and year is not null
        and population is not null
        and year between 2000 and extract(year from current_date) + 1
        and population > 0
        and (literacy_rate is null or (literacy_rate >= 0 and literacy_rate <= 100))
        and (life_expectancy is null or (life_expectancy >= 0 and life_expectancy <= 120))
        and (urban_population_pct is null or (urban_population_pct >= 0 and urban_population_pct <= 100))
),

final as (
    select
        country_code_clean as country_code,
        country_name,
        population,
        gdp_per_capita,
        literacy_rate,
        life_expectancy,
        urban_population_pct,
        year,
        source,
        last_updated,
        processed_at,
        
        -- Derived metrics
        case 
            when gdp_per_capita is not null and literacy_rate is not null and life_expectancy is not null
            then (gdp_per_capita / 1000) * 0.4 + (literacy_rate / 100) * 0.3 + (life_expectancy / 100) * 0.3
            else null
        end as development_index,
        
        -- Population categories
        case 
            when population < 1000000 then 'Small'
            when population < 10000000 then 'Medium'
            when population < 100000000 then 'Large'
            else 'Very Large'
        end as population_category,
        
        -- Development categories
        case 
            when gdp_per_capita < 1000 then 'Low Income'
            when gdp_per_capita < 4000 then 'Lower Middle Income'
            when gdp_per_capita < 12000 then 'Upper Middle Income'
            else 'High Income'
        end as income_category
        
    from cleaned
)

select * from final
