{{
  config(
    materialized='view',
    tags=['staging', 'economic']
  )
}}

-- This is a simple staging model for demonstration
-- In a real scenario, this would read from your data source

select 
  'BRA' as country_code,
  'Brazil' as country_name,
  'GDP_CURRENT_USD' as indicator_code,
  'GDP (current US$)' as indicator_name,
  1500000000000 as value,
  'USD' as unit,
  2024 as year,
  1 as month,
  'World Bank API' as source,
  current_timestamp as last_updated

union all

select 
  'ARG' as country_code,
  'Argentina' as country_name,
  'INFLATION_CPI' as indicator_code,
  'Inflation, consumer prices' as indicator_name,
  8.5 as value,
  'Percent' as unit,
  2024 as year,
  1 as month,
  'World Bank API' as source,
  current_timestamp as last_updated

union all

select 
  'CHL' as country_code,
  'Chile' as country_name,
  'EXCHANGE_RATE' as indicator_code,
  'Official exchange rate' as indicator_name,
  850.25 as value,
  'Local Currency per USD' as unit,
  2024 as year,
  1 as month,
  'World Bank API' as source,
  current_timestamp as last_updated
