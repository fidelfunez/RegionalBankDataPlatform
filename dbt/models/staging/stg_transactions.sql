{{
  config(
    materialized='view',
    tags=['staging', 'transactional']
  )
}}

with source as (
    select * from {{ source('raw', 'transactions') }}
),

cleaned as (
    select
        -- Primary keys
        transaction_id,
        country_code,
        transaction_date,
        
        -- Dimensions
        trim(upper(country_code)) as country_code_clean,
        trim(loan_id) as loan_id,
        trim(upper(transaction_type)) as transaction_type_clean,
        trim(upper(sector)) as sector_clean,
        trim(upper(status)) as status_clean,
        trim(beneficiary_id) as beneficiary_id,
        trim(upper(currency)) as currency_clean,
        
        -- Measures
        cast(amount as decimal(18,2)) as amount,
        
        -- Metadata
        source,
        current_timestamp as processed_at
        
    from source
    where 
        -- Data quality filters
        transaction_id is not null
        and country_code is not null
        and amount is not null
        and transaction_date is not null
        and amount > 0
        and transaction_date >= '2020-01-01'
        and transaction_date <= current_date + interval '1 day'
),

final as (
    select
        transaction_id,
        country_code_clean as country_code,
        loan_id,
        transaction_type_clean as transaction_type,
        amount,
        currency_clean as currency,
        transaction_date,
        beneficiary_id,
        sector_clean as sector,
        status_clean as status,
        source,
        processed_at,
        
        -- Derived fields
        case 
            when transaction_type_clean in ('DISBURSEMENT', 'LOAN_DISBURSEMENT') then 'Disbursement'
            when transaction_type_clean in ('REPAYMENT', 'LOAN_REPAYMENT') then 'Repayment'
            when transaction_type_clean in ('FEE', 'INTEREST') then 'Fee'
            when transaction_type_clean in ('REFUND', 'ADJUSTMENT') then 'Adjustment'
            else 'Other'
        end as transaction_category,
        
        -- Risk indicators
        case 
            when amount >= {{ var('high_value_transaction_threshold') }} then true
            else false
        end as is_high_value,
        
        case 
            when status_clean = 'FAILED' then true
            else false
        end as is_failed,
        
        -- Date fields
        extract(year from transaction_date) as transaction_year,
        extract(month from transaction_date) as transaction_month,
        extract(day from transaction_date) as transaction_day,
        date_trunc('month', transaction_date) as transaction_month_date,
        
        -- Hash for deduplication
        md5(transaction_id || country_code_clean || cast(amount as varchar) || cast(transaction_date as varchar)) as transaction_hash
        
    from cleaned
)

select * from final
