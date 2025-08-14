{{
  config(
    materialized='view',
    tags=['intermediate', 'transactional']
  )
}}

with transaction_data as (
    select 
        transaction_id,
        country_code,
        loan_id,
        transaction_type,
        transaction_category,
        amount,
        currency,
        transaction_date,
        beneficiary_id,
        sector,
        status,
        source,
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

-- Daily transaction metrics
daily_metrics as (
    select 
        country_code,
        transaction_date,
        transaction_month_date,
        transaction_year,
        transaction_month,
        transaction_day,
        
        -- Volume metrics
        count(*) as daily_transaction_count,
        sum(amount) as daily_transaction_amount,
        avg(amount) as daily_avg_transaction_amount,
        max(amount) as daily_max_transaction_amount,
        min(amount) as daily_min_transaction_amount,
        
        -- Type breakdown
        count(case when transaction_category = 'Disbursement' then 1 end) as daily_disbursement_count,
        count(case when transaction_category = 'Repayment' then 1 end) as daily_repayment_count,
        count(case when transaction_category = 'Fee' then 1 end) as daily_fee_count,
        
        sum(case when transaction_category = 'Disbursement' then amount else 0 end) as daily_disbursement_amount,
        sum(case when transaction_category = 'Repayment' then amount else 0 end) as daily_repayment_amount,
        sum(case when transaction_category = 'Fee' then amount else 0 end) as daily_fee_amount,
        
        -- Risk metrics
        count(case when is_high_value then 1 end) as daily_high_value_count,
        count(case when is_failed then 1 end) as daily_failed_count,
        sum(case when is_high_value then amount else 0 end) as daily_high_value_amount,
        sum(case when is_failed then amount else 0 end) as daily_failed_amount,
        
        -- Unique entities
        count(distinct loan_id) as daily_unique_loans,
        count(distinct beneficiary_id) as daily_unique_beneficiaries,
        count(distinct sector) as daily_sectors_covered,
        count(distinct currency) as daily_currencies_used
        
    from transaction_data
    group by 
        country_code,
        transaction_date,
        transaction_month_date,
        transaction_year,
        transaction_month,
        transaction_day
),

-- Rolling metrics (7-day and 30-day)
rolling_metrics as (
    select 
        *,
        -- 7-day rolling averages
        avg(daily_transaction_count) over (
            partition by country_code 
            order by transaction_date 
            rows between 6 preceding and current row
        ) as rolling_7d_avg_transaction_count,
        
        avg(daily_transaction_amount) over (
            partition by country_code 
            order by transaction_date 
            rows between 6 preceding and current row
        ) as rolling_7d_avg_transaction_amount,
        
        -- 30-day rolling averages
        avg(daily_transaction_count) over (
            partition by country_code 
            order by transaction_date 
            rows between 29 preceding and current row
        ) as rolling_30d_avg_transaction_count,
        
        avg(daily_transaction_amount) over (
            partition by country_code 
            order by transaction_date 
            rows between 29 preceding and current row
        ) as rolling_30d_avg_transaction_amount,
        
        -- Rolling failure rate
        sum(daily_failed_count) over (
            partition by country_code 
            order by transaction_date 
            rows between 6 preceding and current row
        ) / nullif(sum(daily_transaction_count) over (
            partition by country_code 
            order by transaction_date 
            rows between 6 preceding and current row
        ), 0) as rolling_7d_failure_rate,
        
        sum(daily_failed_count) over (
            partition by country_code 
            order by transaction_date 
            rows between 29 preceding and current row
        ) / nullif(sum(daily_transaction_count) over (
            partition by country_code 
            order by transaction_date 
            rows between 29 preceding and current row
        ), 0) as rolling_30d_failure_rate
        
    from daily_metrics
),

-- Month-to-date metrics
mtd_metrics as (
    select 
        country_code,
        transaction_month_date,
        transaction_year,
        transaction_month,
        
        sum(daily_transaction_count) as mtd_transaction_count,
        sum(daily_transaction_amount) as mtd_transaction_amount,
        avg(daily_transaction_amount) as mtd_avg_transaction_amount,
        
        sum(daily_disbursement_amount) as mtd_disbursement_amount,
        sum(daily_repayment_amount) as mtd_repayment_amount,
        sum(daily_fee_amount) as mtd_fee_amount,
        
        sum(daily_high_value_amount) as mtd_high_value_amount,
        sum(daily_failed_amount) as mtd_failed_amount,
        
        count(distinct case when daily_unique_loans > 0 then transaction_date end) as mtd_active_days,
        
        -- MTD ratios
        case 
            when sum(daily_transaction_amount) > 0 
            then sum(daily_disbursement_amount) / sum(daily_transaction_amount)
            else 0 
        end as mtd_disbursement_ratio,
        
        case 
            when sum(daily_transaction_amount) > 0 
            then sum(daily_repayment_amount) / sum(daily_transaction_amount)
            else 0 
        end as mtd_repayment_ratio,
        
        case 
            when sum(daily_transaction_count) > 0 
            then sum(daily_failed_count) / sum(daily_transaction_count)
            else 0 
        end as mtd_failure_rate
        
    from daily_metrics
    group by 
        country_code,
        transaction_month_date,
        transaction_year,
        transaction_month
),

final as (
    select 
        d.*,
        r.rolling_7d_avg_transaction_count,
        r.rolling_7d_avg_transaction_amount,
        r.rolling_30d_avg_transaction_count,
        r.rolling_30d_avg_transaction_amount,
        r.rolling_7d_failure_rate,
        r.rolling_30d_failure_rate,
        m.mtd_transaction_count,
        m.mtd_transaction_amount,
        m.mtd_avg_transaction_amount,
        m.mtd_disbursement_amount,
        m.mtd_repayment_amount,
        m.mtd_fee_amount,
        m.mtd_high_value_amount,
        m.mtd_failed_amount,
        m.mtd_active_days,
        m.mtd_disbursement_ratio,
        m.mtd_repayment_ratio,
        m.mtd_failure_rate,
        
        -- Derived metrics
        case 
            when daily_transaction_count > 0 
            then daily_failed_count / daily_transaction_count
            else 0 
        end as daily_failure_rate,
        
        case 
            when daily_transaction_amount > 0 
            then daily_high_value_amount / daily_transaction_amount
            else 0 
        end as daily_high_value_ratio,
        
        case 
            when daily_transaction_amount > 0 
            then daily_disbursement_amount / daily_transaction_amount
            else 0 
        end as daily_disbursement_ratio,
        
        case 
            when daily_transaction_amount > 0 
            then daily_repayment_amount / daily_transaction_amount
            else 0 
        end as daily_repayment_ratio
        
    from daily_metrics d
    left join rolling_metrics r on d.country_code = r.country_code 
        and d.transaction_date = r.transaction_date
    left join mtd_metrics m on d.country_code = m.country_code 
        and d.transaction_month_date = m.transaction_month_date
)

select * from final
