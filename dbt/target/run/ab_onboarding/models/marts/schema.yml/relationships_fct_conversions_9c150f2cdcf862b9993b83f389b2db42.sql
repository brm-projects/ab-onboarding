
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

with child as (
    select experiment_key as from_field
    from "abdb"."analytics"."fct_conversions"
    where experiment_key is not null
),

parent as (
    select experiment_key as to_field
    from "abdb"."analytics"."fct_exposures"
)

select
    from_field

from child
left join parent
    on child.from_field = parent.to_field

where parent.to_field is null



  
  
      
    ) dbt_internal_test