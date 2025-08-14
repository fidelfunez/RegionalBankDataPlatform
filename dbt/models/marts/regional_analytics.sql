{{
  config(
    materialized='table',
    tags=['marts', 'analytics']
  )
}}

with country_transactions as (
    select 
        c.country_code,
        c.country_name,
        c.population,
        c.gdp_per_capita,
        c.development_index,
        c.income_category,
        c.population_category,
        date_trunc('month', f.transaction_date) as month_date,
        extract(year from f.transaction_date) as year,
        extract(month from f.transaction_date) as month,
        
        -- Transaction metrics
        count(*) as total_transactions,
        count(distinct f.loan_id) as unique_loans,
        count(distinct f.beneficiary_id) as unique_beneficiaries,
        sum(f.amount) as total_amount,
        avg(f.amount) as avg_transaction_amount,
        max(f.amount) as max_transaction_amount,
        min(f.amount) as min_transaction_amount,
        
        -- Transaction type breakdown
        sum(case when f.transaction_category = 'Disbursement' then f.amount else 0 end) as disbursement_amount,
        sum(case when f.transaction_category = 'Repayment' then f.amount else 0 end) as repayment_amount,
        sum(case when f.transaction_category = 'Fee' then f.amount else 0 end) as fee_amount,
        
        count(case when f.transaction_category = 'Disbursement' then 1 end) as disbursement_count,
        count(case when f.transaction_category = 'Repayment' then 1 end) as repayment_count,
        count(case when f.transaction_category = 'Fee' then 1 end) as fee_count,
        
        -- Risk metrics
        count(case when f.is_high_value then 1 end) as high_value_transactions,
        count(case when f.is_failed then 1 end) as failed_transactions,
        sum(case when f.is_high_value then f.amount else 0 end) as high_value_amount,
        sum(case when f.is_failed then f.amount else 0 end) as failed_amount,
        
        -- Sector breakdown
        count(distinct f.sector) as sectors_covered,
        
        -- Currency breakdown
        count(distinct f.currency) as currencies_used
        
    from {{ ref('fact_transactions') }} f
    inner join {{ ref('dim_countries') }} c on f.country_sk = c.country_sk
    where c.is_current = true
    group by 
        c.country_code,
        c.country_name,
        c.population,
        c.gdp_per_capita,
        c.development_index,
        c.income_category,
        c.population_category,
        date_trunc('month', f.transaction_date),
        extract(year from f.transaction_date),
        extract(month from f.transaction_date)
),

economic_indicators as (
    select 
        country_code,
        year,
        month,
        date_trunc('month', month_date) as month_date,
        avg(value) as avg_economic_value,
        count(distinct indicator_code) as indicators_count,
        count(distinct indicator_category) as categories_count
    from {{ ref('stg_economic_indicators') }}
    group by 
        country_code,
        year,
        month,
        date_trunc('month', month_date)
),

final as (
    select
        -- Keys
        ct.country_code,
        ct.country_name,
        ct.month_date,
        ct.year,
        ct.month,
        
        -- Country characteristics
        ct.population,
        ct.gdp_per_capita,
        ct.development_index,
        ct.income_category,
        ct.population_category,
        
        -- Transaction volume metrics
        ct.total_transactions,
        ct.unique_loans,
        ct.unique_beneficiaries,
        ct.total_amount,
        ct.avg_transaction_amount,
        ct.max_transaction_amount,
        ct.min_transaction_amount,
        
        -- Transaction type metrics
        ct.disbursement_amount,
        ct.repayment_amount,
        ct.fee_amount,
        ct.disbursement_count,
        ct.repayment_count,
        ct.fee_count,
        
        -- Risk metrics
        ct.high_value_transactions,
        ct.failed_transactions,
        ct.high_value_amount,
        ct.failed_amount,
        
        -- Coverage metrics
        ct.sectors_covered,
        ct.currencies_used,
        
        -- Economic context
        ei.avg_economic_value,
        ei.indicators_count,
        ei.categories_count,
        
        -- Derived KPIs
        case 
            when ct.population > 0 then ct.total_transactions / ct.population * 1000
            else 0 
        end as transactions_per_1000_population,
        
        case 
            when ct.population > 0 then ct.total_amount / ct.population
            else 0 
        end as amount_per_capita,
        
        case 
            when ct.total_transactions > 0 then ct.failed_transactions::float / ct.total_transactions
            else 0 
        end as failure_rate,
        
        case 
            when ct.total_transactions > 0 then ct.high_value_transactions::float / ct.total_transactions
            else 0 
        end as high_value_rate,
        
        case 
            when ct.total_amount > 0 then ct.disbursement_amount / ct.total_amount
            else 0 
        end as disbursement_ratio,
        
        case 
            when ct.total_amount > 0 then ct.repayment_amount / ct.total_amount
            else 0 
        end as repayment_ratio,
        
        case 
            when ct.disbursement_amount > 0 then ct.repayment_amount / ct.disbursement_amount
            else 0 
        end as repayment_to_disbursement_ratio,
        
        -- Efficiency metrics
        case 
            when ct.unique_loans > 0 then ct.total_transactions / ct.unique_loans
            else 0 
        end as avg_transactions_per_loan,
        
        case 
            when ct.unique_beneficiaries > 0 then ct.total_amount / ct.unique_beneficiaries
            else 0 
        end as avg_amount_per_beneficiary,
        
        -- Timestamp
        current_timestamp as created_at
        
    from country_transactions ct
    left join economic_indicators ei on ct.country_code = ei.country_code 
        and ct.month_date = ei.month_date
)

select * from final
