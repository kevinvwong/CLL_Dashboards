-- ============================================================================
-- CLL Strategy Portfolio - Revision 2, T-SQL read models
-- ============================================================================
-- Task 5.1-5.5. These are the four cards' data source.
--
-- D2: current progress and status are DERIVED from the latest update, never read
-- from initiative.progress_value / initiative.status. Those two columns are a
-- cache and nothing keeps them in step, so a card reading them would disagree
-- with its own history. vw_initiative_current is the only place that decides.
--
-- D4 / task 5.5: no view computes an aggregate or averaged parent progress.
-- The absence is deliberate and asserted by a test that greps these definitions.
-- ============================================================================

SET NOCOUNT ON;
GO

-- ---------------------------------------------------------------------------
-- The latest update per initiative (the source of current state)
-- ---------------------------------------------------------------------------
CREATE OR ALTER VIEW dbo.vw_latest_update AS
SELECT initiative_id, update_id, update_date, updated_by_person_id,
       narrative, progress_value, status_at_update
FROM (
    SELECT iu.*,
           ROW_NUMBER() OVER (PARTITION BY initiative_id
                              ORDER BY update_date DESC, update_id DESC) AS rn
    FROM dbo.initiative_update iu
) ranked
WHERE rn = 1;
GO

-- ---------------------------------------------------------------------------
-- 5.2 Current progress and status, derived from the update history
-- ---------------------------------------------------------------------------
-- Falls back to the initiative row only when NO update exists at all, and marks
-- that case, so a caller can tell "no update yet" from "reported as zero".
CREATE OR ALTER VIEW dbo.vw_initiative_current AS
SELECT
    i.initiative_id,
    i.initiative_code,
    i.initiative_name,
    i.description,
    i.initiative_level,
    i.initiative_type,
    i.active_flag,
    i.progress_method,
    lu.update_date      AS last_updated,
    lu.status_at_update AS status_current,
    lu.progress_value   AS progress_current,
    lu.narrative        AS latest_narrative,
    CAST(CASE WHEN lu.initiative_id IS NULL THEN 1 ELSE 0 END AS BIT) AS no_update_yet,
    -- recency in days: status is self-reported, so it is only meaningful with a
    -- date beside it. See the design note on staleness.
    DATEDIFF(DAY, lu.update_date, SYSDATETIME()) AS days_since_update
FROM dbo.initiative i
LEFT JOIN dbo.vw_latest_update lu ON lu.initiative_id = i.initiative_id;
GO

-- ---------------------------------------------------------------------------
-- The current primary Reporting Owner per initiative
-- ---------------------------------------------------------------------------
CREATE OR ALTER VIEW dbo.vw_primary_reporting_owner AS
SELECT initowner.initiative_id, initowner.person_id, p.display_name, p.business_email
FROM dbo.initiative_owner initowner
JOIN dbo.person p ON p.person_id = initowner.person_id
WHERE initowner.ownership_role = 'Reporting Owner'
  AND initowner.primary_flag = 1
  AND initowner.effective_end IS NULL;
GO

-- ---------------------------------------------------------------------------
-- Shared initiative card row
-- ---------------------------------------------------------------------------
-- Both the goal list and the priority list project through this, so "the same
-- underlying records" (task 5.1) is true by construction rather than by two
-- views that happen to agree today.
CREATE OR ALTER VIEW dbo.vw_initiative_summary AS
SELECT
    c.initiative_id,
    c.initiative_code,
    c.initiative_name,
    c.initiative_level,
    c.status_current,
    c.progress_current,
    c.progress_method,
    c.last_updated,
    c.days_since_update,
    c.no_update_yet,
    o.person_id      AS owner_person_id,
    o.display_name   AS owner_name
FROM dbo.vw_initiative_current c
LEFT JOIN dbo.vw_primary_reporting_owner o ON o.initiative_id = c.initiative_id
WHERE c.active_flag = 1;
GO

-- ---------------------------------------------------------------------------
-- 5.1 Goal -> initiatives
-- ---------------------------------------------------------------------------
CREATE OR ALTER VIEW dbo.vw_goal_initiatives AS
SELECT
    g.goal_id, g.goal_number, g.short_label, g.canonical_title,
    ig.relationship_type AS goal_relationship,
    s.initiative_id, s.initiative_code, s.initiative_name, s.initiative_level,
    s.status_current, s.progress_current, s.last_updated, s.days_since_update, s.no_update_yet,
    s.owner_person_id, s.owner_name
FROM dbo.goal g
JOIN dbo.initiative_goal ig ON ig.goal_id = g.goal_id
JOIN dbo.vw_initiative_summary s ON s.initiative_id = ig.initiative_id;
GO

-- ---------------------------------------------------------------------------
-- 5.1 Priority -> initiatives
-- ---------------------------------------------------------------------------
-- Projects the SAME columns as vw_goal_initiatives from the SAME base view, so an
-- initiative reached through a goal and through a priority is identical field for
-- field. The only difference is which key column leads.
CREATE OR ALTER VIEW dbo.vw_priority_initiatives AS
SELECT
    ap.priority_id, ap.priority_code, ap.priority_name, ap.planning_period,
    ip.relationship_type AS priority_relationship,
    s.initiative_id, s.initiative_code, s.initiative_name, s.initiative_level,
    s.status_current, s.progress_current, s.last_updated, s.days_since_update, s.no_update_yet,
    s.owner_person_id, s.owner_name
FROM dbo.annual_priority ap
JOIN dbo.initiative_priority ip ON ip.priority_id = ap.priority_id
JOIN dbo.vw_initiative_summary s ON s.initiative_id = ip.initiative_id;
GO

-- ---------------------------------------------------------------------------
-- 5.3 Upstream and downstream relationships, both directions
-- ---------------------------------------------------------------------------
-- One row per relationship, seen from each end, so a D-1 that supports two Dean
-- initiatives appears twice - both parents, neither treated as the only one.
CREATE OR ALTER VIEW dbo.vw_initiative_relationships AS
SELECT
    r.from_initiative_id AS initiative_id,
    'Outgoing' AS direction,
    r.relationship_type,
    r.to_initiative_id AS related_initiative_id,
    ri.initiative_code AS related_code,
    ri.initiative_name AS related_name,
    ri.initiative_level AS related_level,
    r.effective_start, r.effective_end
FROM dbo.initiative_relationship r
JOIN dbo.initiative ri ON ri.initiative_id = r.to_initiative_id
UNION ALL
SELECT
    r.to_initiative_id,
    'Incoming',
    r.relationship_type,
    r.from_initiative_id,
    fi.initiative_code,
    fi.initiative_name,
    fi.initiative_level,
    r.effective_start, r.effective_end
FROM dbo.initiative_relationship r
JOIN dbo.initiative fi ON fi.initiative_id = r.from_initiative_id;
GO

-- ---------------------------------------------------------------------------
-- 5.4 A person's initiatives, plus a row for people with none
-- ---------------------------------------------------------------------------
-- A steward or an administrator may own nothing and manage nobody. They must
-- still resolve to a meaningful row rather than to an empty result, so this view
-- is anchored on person and LEFT JOINs the work.
--
-- Deliberately NOT a progress aggregate: counting a person's initiatives is a
-- count of things, not a combined progress figure (task 5.5).
CREATE OR ALTER VIEW dbo.vw_person_portfolio AS
SELECT
    p.person_id,
    p.display_name,
    p.working_title,
    p.active_flag,
    s.initiative_id,
    s.initiative_code,
    s.initiative_name,
    s.initiative_level,
    s.status_current,
    s.progress_current,
    s.last_updated,
    s.days_since_update,
    s.no_update_yet,
    iown.ownership_role,
    iown.primary_flag
FROM dbo.person p
LEFT JOIN dbo.initiative_owner iown
       ON iown.person_id = p.person_id
      AND (iown.effective_end IS NULL OR iown.effective_end >= CAST(SYSDATETIME() AS DATE))
LEFT JOIN dbo.vw_initiative_summary s ON s.initiative_id = iown.initiative_id;
GO

-- ---------------------------------------------------------------------------
-- Stewardship, so a steward's page has content too
-- ---------------------------------------------------------------------------
CREATE OR ALTER VIEW dbo.vw_person_stewardship AS
SELECT
    sa.person_id,
    sa.entity_type,
    sa.entity_id,
    sa.stewardship_role,
    sa.effective_start,
    sa.effective_end
FROM dbo.stewardship_assignment sa
WHERE sa.effective_end IS NULL OR sa.effective_end >= CAST(SYSDATETIME() AS DATE);
GO

PRINT 'Read models created.';
GO
