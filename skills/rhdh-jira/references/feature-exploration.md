# Feature Exploration Process

Checklist for reviewing and refining Features and Epics before sprint planning. This is the process followed during **Feature Exploration** meetings (not "Feature Refinement" — see Terminology note below).

## Terminology

The meeting is called **Feature Exploration**. The Jira workflow status is **Refinement**. These are different things:

- **Feature Exploration** — the meeting where team leads, architects, and engineers review candidate features, ask questions, and identify risks
- **Refinement (Jira status)** — the workflow status a Feature enters after initial fields are set

Do not confuse the two. When referring to the meeting or process, use "Feature Exploration."

**Features in New status is expected going into Feature Exploration.** The exploration meeting is where the team reviews candidates, identifies risks, and produces the information needed to advance features through the pipeline. Do not frame New→Refinement transition as a prerequisite for exploration — it is an *outcome*. Sizing and field population happen during and after exploration.

**Epic creation can happen before or during exploration.** Teams often create child Epics before the exploration meeting to help size the Feature — aggregate Epic sizes inform the Feature’s T-shirt size. Do not treat Epic creation as exclusively an output of exploration.

## Feature Exploration Checklist

Team leads, architects, and engineers review feature candidates to identify dependencies and risks.

### 1. Set Required Jira Fields

- **Priority** — set based on business value and urgency
- **Team** — assign the owning scrum team
- **Assignee** — assign a Feature Owner (single point of contact)

### 2. Cross-Team Engagement

- Identify if the feature requires work from other scrum teams
- Engage with those teams to design the solution
- Document dependencies in the Jira issue
- Confirm the other teams are aware and have capacity

### 3. Labels for PM and Reporter Communication

- Add `needs-pm` if there are questions for Product Management
- Add `needs-info` if there are questions for the feature reporter from Engineering
- Use Feature Exploration meetings to ask unanswered questions after discussing in the Jira issue first

### 4. Update Jira with Decisions

- Document decisions, questions, and next steps in the issue (as comments, not description bloat)
- Consider rescoping if the feature is too large to fit within a single release

### 5. Set Components

Components must be accurate — they affect Feature Freeze and Code Freeze queries.

- Validate components against the project's component list (see Component Validation below)
- If the feature involves documentation, set the `Documentation` component and invoke the doc automation: **Feature → More → Create Doc EPIC from RHDHPlan**
  - Note: This is a Jira UI automation action. The agent should prompt the user to perform this step manually after the Feature is created.
  - Note: Doc EPIC automation is only available for the Documentation component. If it's not available, coordinate with the Docs team directly.
- Some components may be excluded from Feature Freeze (FF) or Code Freeze (CF). Check the component's FF/CF status before assuming it blocks a freeze.

### 6. Set Labels

- `demo` — if the feature requires a customer-facing feature demo
- `rhdh-testday` — if this feature should be tested as part of release test day
- `rhdh-X.Y-candidate` — candidate for a specific release (e.g., `rhdh-2.1-candidate`)
- `stretch` — stretch goal for the release (may be descoped)

### 7. Create Epics for Each Scrum Team

Refine the Feature and create Epic(s) for work to be delivered by each scrum team. For each Epic:

- Set the **Team** field to the owning scrum team
- Assign an **Epic Owner** (Assignee) — work with the scrum team to identify
- The Epic Owner is responsible for sizing the Epic

Set these fields on each Epic:

| Field | What to set |
|-------|------------|
| Component(s) | Validate against project component list |
| Size | T-shirt size per the sizing guide |
| Links (Dependencies) | Link or note key dependencies on other issues, teams, upstream work |

### 8. Size the Feature

- Feature Owner sizes the Feature by updating the **Size** field
- Base Feature size on the sizing guide and the aggregate of Epic T-shirt sizes
- If multiple L or XL Epics exist within a Feature, reassess scope — the Feature may be too large

### 9. Set Feature Status

After exploration is complete:

- Set Feature Status to **Backlog**
- Ensure all child Epics are created and linked

## Component Validation

Components are critical for freeze queries and team routing. Validate proposed components against the live Jira data.

> Same validation pattern as `fields.md` Component Validation — duplicated here to avoid transitive loading.

```bash
# List all components for a project
curl -s -H "Authorization: Basic $(cat "$TOKEN_FILE")" \
  "https://redhat.atlassian.net/rest/api/3/project/RHIDP/components" | \
  python -c "import sys,json; [print(c['name']) for c in json.load(sys.stdin)]"

# For RHDHPLAN
curl -s -H "Authorization: Basic $(cat "$TOKEN_FILE")" \
  "https://redhat.atlassian.net/rest/api/3/project/RHDHPLAN/components" | \
  python -c "import sys,json; [print(c['name']) for c in json.load(sys.stdin)]"
```

When setting components during feature creation or refinement:

1. **Infer components** from the issue summary and description — match against known component names
2. **Validate** the proposed components exist in the project
3. **Flag mismatches** — if a component doesn't exist, suggest the closest match
4. **Check FF/CF status** — note if a component is excluded from freeze queries (this affects release planning)

The agent should suggest components based on issue details, but always confirm with the user before setting them.

## Feature Demo and Test Day

Features that are customer-facing should be assessed for:

- **Demo requirement** — does this need a feature demo? If yes, add the `demo` label. A link to the Feature Demo is required at **Release Pending** status.
- **Test day candidacy** — should this be tested during release test day? If yes, add the `rhdh-testday` label.

Ask about both during feature creation and refinement.

## Rescoping

If a feature is too large for a single release:

1. Consider splitting into multiple Features across releases
2. Identify the minimum viable scope for the current release
3. Document what's being deferred and why (as a comment on the Feature)
4. Adjust the `rhdh-X.Y-candidate` label if the target release changes
