{{
  config(
    materialized='view',
    tags=['intermediate', 'economic']
  )
}}

with economic_data as (
    select 
        country_code,
        country_name,
        indicator_code,
        indicator_name,
        indicator_category,
        value,
        unit,
        year,
        month,
        month_date,
        year_month,
        source,
        last_updated,
        processed_at
    from {{ ref('stg_economic_indicators') }}
),

-- Calculate year-over-year growth
yoy_growth as (
    select 
        country_code,
        indicator_code,
        year,
        month,
        value,
        lag(value) over (
            partition by country_code, indicator_code, month 
            order by year
        ) as prev_year_value,
        case 
            when lag(value) over (
                partition by country_code, indicator_code, month 
                order by year
            ) is not null and lag(value) over (
                partition by country_code, indicator_code, month 
                order by year
            ) != 0
            then (value - lag(value) over (
                partition by country_code, indicator_code, month 
                order by year
            )) / lag(value) over (
                partition by country_code, indicator_code, month 
                order by year
            ) * 100
            else null
        end as yoy_growth_pct
    from economic_data
),

-- Calculate moving averages
moving_averages as (
    select 
        country_code,
        indicator_code,
        year,
        month,
        value,
        avg(value) over (
            partition by country_code, indicator_code 
            order by year_month 
            rows between 11 preceding and current row
        ) as ma_12_month,
        avg(value) over (
            partition by country_code, indicator_code 
            order by year_month 
            rows between 2 preceding and current row
        ) as ma_3_month
    from economic_data
),

final as (
    select 
        e.country_code,
        e.country_name,
        e.indicator_code,
        e.indicator_name,
        e.indicator_category,
        e.value,
        e.unit,
        e.year,
        e.month,
        e.month_date,
        e.year_month,
        e.source,
        e.last_updated,
        e.processed_at,
        y.yoy_growth_pct,
        m.ma_12_month,
        m.ma_3_month,
        -- Calculate volatility (standard deviation over 12 months)
        stddev(e.value) over (
            partition by e.country_code, e.indicator_code 
            order by e.year_month 
            rows between 11 preceding and current row
        ) as volatility_12_month
    from economic_data e
    left join yoy_growth y on e.country_code = y.country_code 
        and e.indicator_code = y.indicator_code 
        and e.year = y.year 
        and e.month = y.month
    left join moving_averages m on e.country_code = m.country_code 
        and e.indicator_code = m.indicator_code 
        and e.year = m.year 
        and e.month = m.month
)

select * from final
