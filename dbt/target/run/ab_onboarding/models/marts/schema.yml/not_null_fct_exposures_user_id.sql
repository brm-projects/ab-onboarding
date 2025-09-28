
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select user_id
from "abdb"."analytics_analytics"."fct_exposures"
where user_id is null



  
  
      
    ) dbt_internal_test