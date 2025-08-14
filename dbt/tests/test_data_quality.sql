-- Test for null values in critical fields
select 
    'stg_economic_indicators' as table_name,
    'null_country_code' as test_name,
    count(*) as failed_count
from {{ ref('stg_economic_indicators') }}
where country_code is null

union all

select 
    'stg_economic_indicators' as table_name,
    'null_indicator_code' as test_name,
    count(*) as failed_count
from {{ ref('stg_economic_indicators') }}
where indicator_code is null

union all

select 
    'stg_economic_indicators' as table_name,
    'null_value' as test_name,
    count(*) as failed_count
from {{ ref('stg_economic_indicators') }}
where value is null

union all

select 
    'stg_demographic_data' as table_name,
    'null_country_code' as test_name,
    count(*) as failed_count
from {{ ref('stg_demographic_data') }}
where country_code is null

union all

select 
    'stg_demographic_data' as table_name,
    'null_population' as test_name,
    count(*) as failed_count
from {{ ref('stg_demographic_data') }}
where population is null

union all

select 
    'stg_transactions' as table_name,
    'null_transaction_id' as test_name,
    count(*) as failed_count
from {{ ref('stg_transactions') }}
where transaction_id is null

union all

select 
    'stg_transactions' as table_name,
    'null_amount' as test_name,
    count(*) as failed_count
from {{ ref('stg_transactions') }}
where amount is null

union all

select 
    'stg_transactions' as table_name,
    'negative_amount' as test_name,
    count(*) as failed_count
from {{ ref('stg_transactions') }}
where amount < 0
