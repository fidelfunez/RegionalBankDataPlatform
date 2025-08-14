{{
  config(
    materialized='table',
    tags=['core', 'fact']
  )
}}

with transactions as (
    select 
        transaction_id,
        country_code,
        loan_id,
        transaction_type,
        amount,
        currency,
        transaction_date,
        beneficiary_id,
        sector,
        status,
        source,
        transaction_category,
        is_high_value,
        is_failed,
        transaction_year,
        transaction_month,
        transaction_day,
        transaction_month_date,
        transaction_hash,
        processed_at
    from {{ ref('stg_transactions') }}
),

-- Get current country dimension records
countries as (
    select 
        country_sk,
        country_code,
        is_current
    from {{ ref('dim_countries') }}
    where is_current = true
),

-- Create date dimension surrogate key
date_dim as (
    select 
        date_sk,
        date_value,
        year,
        month,
        day,
        month_name,
        quarter,
        is_weekend,
        is_month_end
    from {{ ref('dim_date') }}
),

final as (
    select
        -- Surrogate keys
        {{ dbt_utils.generate_surrogate_key(['transaction_id']) }} as transaction_sk,
        c.country_sk,
        d.date_sk,
        
        -- Natural keys
        t.transaction_id,
        t.country_code,
        t.loan_id,
        t.beneficiary_id,
        
        -- Dimensions
        t.transaction_type,
        t.transaction_category,
        t.sector,
        t.status,
        t.currency,
        t.source,
        
        -- Measures
        t.amount,
        
        -- Flags
        t.is_high_value,
        t.is_failed,
        
        -- Dates
        t.transaction_date,
        t.transaction_year,
        t.transaction_month,
        t.transaction_day,
        t.transaction_month_date,
        
        -- Metadata
        t.transaction_hash,
        t.processed_at,
        current_timestamp as dbt_updated_at
        
    from transactions t
    left join countries c on t.country_code = c.country_code
    left join date_dim d on t.transaction_date = d.date_value
    
    -- Ensure we have valid foreign keys
    where c.country_sk is not null
        and d.date_sk is not null
)

select * from final
