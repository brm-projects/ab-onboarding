
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select conversion_rate
from "abdb"."analytics_analytics"."agg_experiment_day"
where conversion_rate is null



  
  
      
    ) dbt_internal_test