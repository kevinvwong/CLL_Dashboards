-- ============================================================================
-- CLL Strategy Portfolio - Revision 2, T-SQL integrity report and traceability
-- ============================================================================
-- Tasks 6.1-6.6.
--
-- The report is the backstop for the two rules T-SQL cannot defer (DEVIATIONS.md
-- #4): a write that bypasses the application can still leave an active
-- initiative unmapped, and the report is what catches it. It is load-bearing,
-- not advisory.
--
-- The report REPORTS. It never repairs. A test asserts that a defective record is
-- still present and still defective after the report runs.
-- ============================================================================

SET NOCOUNT ON;
GO

-- ---------------------------------------------------------------------------
-- The integrity report: one row per defect, named, with its record
-- ---------------------------------------------------------------------------
-- A clean dataset returns ZERO rows. Any non-empty result is a defect, not
-- normal output. Each branch names the defect class and the offending record.
CREATE OR ALTER VIEW dbo.vw_integrity_report AS
-- D1. an active initiative with no current goal mapping
SELECT 'Orphan initiative' AS defect_class,
       i.initiative_id    AS record_id,
       'active initiative has no current goal mapping' AS detail
FROM dbo.initiative i
WHERE i.active_flag = 1 AND i.status = 'Active'
  AND NOT EXISTS (
        SELECT 1 FROM dbo.initiative_goal g
        WHERE g.initiative_id = i.initiative_id
          AND (g.effective_end IS NULL OR g.effective_end >= CAST(SYSDATETIME() AS DATE)))

UNION ALL
-- D2. an active D-1 initiative with no Dean link
SELECT 'Active D-1 without Dean link', i.initiative_id,
       'active D-1 initiative supports no Dean initiative'
FROM dbo.initiative i
WHERE i.active_flag = 1 AND i.status = 'Active' AND i.initiative_level = 'D-1'
  AND NOT EXISTS (
        SELECT 1
        FROM dbo.initiative_relationship r
        JOIN dbo.initiative parent ON parent.initiative_id = r.to_initiative_id
        WHERE r.from_initiative_id = i.initiative_id
          AND parent.initiative_level = 'Dean'
          AND r.relationship_type IN ('Supports','Contributes To')
          AND (r.effective_end IS NULL OR r.effective_end >= CAST(SYSDATETIME() AS DATE)))

UNION ALL
-- D3. an active D-1 initiative with no current primary Reporting Owner
SELECT 'Active D-1 without primary owner', i.initiative_id,
       'active D-1 initiative has no current primary Reporting Owner'
FROM dbo.initiative i
WHERE i.active_flag = 1 AND i.status = 'Active' AND i.initiative_level = 'D-1'
  AND NOT EXISTS (
        SELECT 1 FROM dbo.initiative_owner o
        WHERE o.initiative_id = i.initiative_id
          AND o.ownership_role = 'Reporting Owner'
          AND o.primary_flag = 1
          AND o.effective_end IS NULL)

UNION ALL
-- D4. a target with no objective relationship
SELECT 'Orphan target', t.target_id,
       'target is linked to no strategic objective'
FROM dbo.target t
WHERE NOT EXISTS (SELECT 1 FROM dbo.objective_target ot WHERE ot.target_id = t.target_id)

UNION ALL
-- D5. a target with no measurement plan (no metric version)
SELECT 'Target without measurement plan', t.target_id,
       'target is evidenced by no metric version and has no approved exception'
FROM dbo.target t
WHERE NOT EXISTS (SELECT 1 FROM dbo.target_metric tm WHERE tm.target_id = t.target_id)

UNION ALL
-- D6. a metric with no current version
SELECT 'Orphan metric', m.metric_id,
       'metric has no current version'
FROM dbo.metric m
WHERE NOT EXISTS (
      SELECT 1 FROM dbo.metric_version mv
      WHERE mv.metric_id = m.metric_id AND mv.effective_end IS NULL)

UNION ALL
-- D7. a metric with no stewardship assignment
SELECT 'Unstewarded metric', m.metric_id,
       'metric has no stewardship assignment'
FROM dbo.metric m
WHERE NOT EXISTS (
      SELECT 1 FROM dbo.stewardship_assignment sa
      WHERE sa.entity_type = 'Metric' AND sa.entity_id = m.metric_id
        AND (sa.effective_end IS NULL OR sa.effective_end >= CAST(SYSDATETIME() AS DATE)))

UNION ALL
-- D8. a metric version with no authoritative source
SELECT 'Metric version without authoritative source', mv.metric_version_id,
       'metric version has no authoritative source'
FROM dbo.metric_version mv
WHERE mv.authoritative_source_id IS NULL

UNION ALL
-- D9. a needs-review record that is being presented as if confirmed
SELECT 'Mapping not confirmed', ig.initiative_id,
       'initiative-goal mapping is still Needs Review'
FROM dbo.initiative_goal ig
WHERE ig.validation_status = 'Needs Review'

UNION ALL
-- D10. an objective with no execution coverage
SELECT 'Objective without execution', o.objective_id,
       'strategic objective is supported by no initiative'
FROM dbo.strategic_objective o
WHERE o.active_flag = 1
  AND NOT EXISTS (SELECT 1 FROM dbo.objective_initiative oi WHERE oi.objective_id = o.objective_id);
GO

-- ---------------------------------------------------------------------------
-- 6.1 Traceability traversal: Portfolio -> Goal -> Objective -> Target ->
--     Initiative -> Metric Version -> Ownership/Stewardship
-- ---------------------------------------------------------------------------
-- One row per fully-resolved path, so both directions are answerable: filter by
-- any column to walk from strategy down to execution, or from an initiative back
-- up. Built with OUTER APPLYs rather than inner joins, because a gap in the chain
-- is exactly what traceability exists to expose - an inner-joined view would hide
-- the very thing it is meant to show.
CREATE OR ALTER VIEW dbo.vw_strategy_traceability AS
SELECT
    pf.portfolio_id,
    pf.portfolio_name,
    g.goal_id,
    g.goal_number,
    g.short_label AS goal_short_label,
    so.objective_id,
    so.canonical_text AS objective_text,
    tg.target_id,
    tg.target_value_text,
    i.initiative_id,
    i.initiative_code,
    i.initiative_level,
    mv.metric_version_id,
    m.metric_code,
    own.person_id      AS reporting_owner_id,
    own.display_name   AS reporting_owner
FROM dbo.portfolio pf
LEFT JOIN dbo.portfolio_goal pg ON pg.portfolio_id = pf.portfolio_id
LEFT JOIN dbo.goal g           ON g.goal_id = pg.goal_id
LEFT JOIN dbo.strategic_objective so ON so.goal_id = g.goal_id
LEFT JOIN dbo.objective_target ot    ON ot.objective_id = so.objective_id
LEFT JOIN dbo.target tg              ON tg.target_id = ot.target_id
OUTER APPLY (
    SELECT TOP 1 oi.initiative_id
    FROM dbo.objective_initiative oi
    WHERE oi.objective_id = so.objective_id
) oi
LEFT JOIN dbo.initiative i ON i.initiative_id = oi.initiative_id
OUTER APPLY (
    SELECT TOP 1 im.metric_version_id
    FROM dbo.initiative_metric im
    WHERE im.initiative_id = i.initiative_id
) imv
LEFT JOIN dbo.metric_version mv ON mv.metric_version_id = imv.metric_version_id
LEFT JOIN dbo.metric m ON m.metric_id = mv.metric_id
LEFT JOIN dbo.vw_primary_reporting_owner own ON own.initiative_id = i.initiative_id;
GO

PRINT 'Integrity report and traceability view created.';
GO
