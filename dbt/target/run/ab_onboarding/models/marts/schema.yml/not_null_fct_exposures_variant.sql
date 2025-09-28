
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select variant
from "abdb"."analytics"."fct_exposures"
where variant is null



  
  
      
    ) dbt_internal_test