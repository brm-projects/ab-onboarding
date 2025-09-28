
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    (user_id || '|' || experiment_key) as unique_field,
    count(*) as n_records

from "abdb"."analytics_analytics"."fct_exposures"
where (user_id || '|' || experiment_key) is not null
group by (user_id || '|' || experiment_key)
having count(*) > 1



  
  
      
    ) dbt_internal_test