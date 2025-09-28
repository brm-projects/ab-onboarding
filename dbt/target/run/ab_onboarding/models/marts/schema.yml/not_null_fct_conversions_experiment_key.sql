
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select experiment_key
from "abdb"."analytics"."fct_conversions"
where experiment_key is null



  
  
      
    ) dbt_internal_test