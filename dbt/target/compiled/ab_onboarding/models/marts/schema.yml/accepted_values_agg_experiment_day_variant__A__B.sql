
    
    

with all_values as (

    select
        variant as value_field,
        count(*) as n_records

    from "abdb"."analytics"."agg_experiment_day"
    group by variant

)

select *
from all_values
where value_field not in (
    'A','B'
)


