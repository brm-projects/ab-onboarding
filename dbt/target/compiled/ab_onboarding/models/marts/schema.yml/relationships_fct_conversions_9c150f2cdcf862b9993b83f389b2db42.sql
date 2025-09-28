
    
    

with child as (
    select experiment_key as from_field
    from "abdb"."analytics_analytics"."fct_conversions"
    where experiment_key is not null
),

parent as (
    select experiment_key as to_field
    from "abdb"."analytics_analytics"."fct_exposures"
)

select
    from_field

from child
left join parent
    on child.from_field = parent.to_field

where parent.to_field is null


