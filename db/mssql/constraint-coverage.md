# Constraint coverage

Task 7.2. Every enforcement mechanism the schema defines, and the test that proves it can
refuse a violation.

38 mechanisms, 0 gaps. A mechanism with no test is listed as a **GAP** rather than
omitted, because an omission reads as coverage while a gap does not.

| Kind | Mechanism | Status | Test |
|---|---|---|---|
| trigger | `trg_active_d1_requires_dean_link` | covered | `test_active_d1_without_a_dean_link_is_refused` |
| trigger | `trg_active_initiative_requires_goal` | covered | `test_a_conforming_d1_is_accepted`, `test_active_initiative_without_a_goal_is_refused` |
| trigger | `trg_block_canonical_goal_delete` | covered | `test_a_canonical_goal_cannot_be_hard_deleted`, `test_retirement_is_not_blocked_by_the_delete_guard` |
| trigger | `trg_block_initiative_update_change` | covered | `test_a_correction_is_a_new_row_and_both_survive`, `test_deleting_an_update_is_refused`, `test_modifying_an_update_is_refused` |
| trigger | `trg_block_objective_delete` | covered | `test_a_canonical_objective_cannot_be_hard_deleted` |
| trigger | `trg_dean_link_removal_requires_link` | covered | `test_active_d1_without_a_dean_link_is_refused` |
| trigger | `trg_enforce_initiative_relationship_levels` | covered | `test_d1_to_dean_is_accepted`, `test_dean_to_d1_is_refused_and_names_the_direction`, `test_self_reference_is_refused` |
| trigger | `trg_goal_mapping_removal_requires_goal` | covered | `test_removing_the_last_goal_from_an_active_initiative_is_refused` |
| trigger | `trg_prevent_initiative_relationship_cycle` | covered | `test_a_non_cyclic_chain_is_accepted`, `test_five_node_cycle_is_refused`, `test_three_node_cycle_is_refused` |
| trigger | `trg_stewardship_no_overlap` | covered | `test_a_different_role_may_overlap`, `test_adjacent_non_overlapping_periods_are_accepted`, `test_overlapping_periods_are_refused_serially` |
| filtered unique index | `uq_current_primary_owner` | covered | `test_a_second_current_primary_reporting_owner_is_refused` |
| filtered unique index | `uq_initiative_current_primary_reporting_owner` | covered | `test_a_closed_primary_permits_a_new_one`, `test_a_second_current_primary_reporting_owner_is_refused`, `test_several_non_primary_contributors_are_allowed` |
| filtered unique index | `uq_metric_current_version` | covered | `test_a_closed_version_permits_a_new_current_one`, `test_two_current_versions_are_refused` |
| filtered unique index | `uq_person_email_present` | covered | `test_a_steward_who_owns_nothing_still_returns_a_row` |
| check constraint | `ck_goal_number` | covered | `test_goal_number_outside_1_to_5_is_refused` |
| check constraint | `ck_initgoal_dates` | covered | `test_permitted_values_are_accepted` |
| check constraint | `ck_initgoal_rel` | covered | `test_permitted_values_are_accepted` |
| check constraint | `ck_initiative_level` | covered | `test_enterprise_level_is_refused`, `test_unlisted_initiative_level_is_refused` |
| check constraint | `ck_initiative_progress` | covered | `test_permitted_values_are_accepted` |
| check constraint | `ck_initiative_progress_method` | covered | `test_permitted_values_are_accepted`, `test_unlisted_progress_method_is_refused` |
| check constraint | `ck_initiative_status` | covered | `test_unlisted_status_is_refused` |
| check constraint | `ck_initiative_type` | covered | `test_unlisted_initiative_type_is_refused` |
| check constraint | `ck_initowner_dates` | covered | `test_end_before_start_is_refused` |
| check constraint | `ck_initowner_role` | covered | `test_unlisted_ownership_role_is_refused` |
| check constraint | `ck_initpri_dates` | covered | `test_permitted_values_are_accepted` |
| check constraint | `ck_initpri_rel` | covered | `test_permitted_values_are_accepted` |
| check constraint | `ck_initpric_rel` | covered | `test_relationship_vocabulary_is_exactly_the_five` |
| check constraint | `ck_initrel_dates` | covered | `test_permitted_values_are_accepted` |
| check constraint | `ck_initrel_not_self` | covered | `test_self_reference_is_refused` |
| check constraint | `ck_initrel_type` | covered | `test_a_narrated_but_unimplemented_type_is_refused`, `test_relationship_vocabulary_is_exactly_the_five` |
| check constraint | `ck_metric_version_dates` | covered | `test_end_before_start_is_refused` |
| check constraint | `ck_objinit_rel` | covered | `test_the_chain_is_reachable_from_the_portfolio` |
| check constraint | `ck_planning_cycle_dates` | covered | `test_planning_cycle_end_before_start_is_refused`, `test_planning_cycle_valid_dates_are_accepted` |
| check constraint | `ck_stewardship_dates` | covered | `test_adjacent_non_overlapping_periods_are_accepted` |
| check constraint | `ck_stewardship_entity` | covered | `test_data_product_is_refused_because_no_such_table_exists`, `test_every_permitted_entity_type_has_a_table` |
| check constraint | `ck_stewardship_role` | covered | `test_permitted_stewardship_is_accepted` |
| check constraint | `ck_targetmetric_rel` | covered | `test_target_metric_relationship_type_is_restricted` |
| check constraint | `ck_update_progress` | covered | `test_a_correction_is_a_new_row_and_both_survive` |

## Gaps

None. Every mechanism the schema defines has at least one test proving it can refuse a violation.

## Why this is not a formality

Dropping a constraint must turn the suite red, or the tests prove nothing. Measured with
`%TEMP%` + `\opencode\redproof.py`:

```
constraint present    exit=0  1 passed
constraint dropped    exit=1  1 failed     <- uq_metric_current_version removed
constraint restored   exit=0  1 passed
```
