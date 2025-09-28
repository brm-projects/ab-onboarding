
    
    

with child as (
    select conversion_rate as from_field
    from "abdb"."analytics_analytics"."agg_experiment_day"
    where conversion_rate is not null
),

parent as (
    select experiment_key as to_field
    from "abdb"."analytics_analytics"."fct_conversions"
)

select
    from_field

from child
left join parent
    on child.from_field = parent.to_field

where parent.to_field is null


