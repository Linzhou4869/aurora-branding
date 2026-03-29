# Metro Tower Q4 Safety Compliance Audit
## Data Requirements Checklist

**Prepared for:** Carlos Ramirez  
**Audit Date:** 2026-03-29  
**Status:** Awaiting Data Extraction  

---

## 📋 Required GitLab Data Extracts

To complete the compliance gap analysis and finalize the Executive Summary, please provide the following data from `gitlab.ramirez-construction.local/projects/metro-tower`:

---

### 1. Merge Requests (Priority: CRITICAL)

**Command:**
```bash
glab mr list --state=opened --label="safety-protocols" --label="site-configurations" --all
```

**Required Fields:**
- [ ] MR ID number
- [ ] Title
- [ ] Author/Creator
- [ ] Created date
- [ ] Current status (opened, approved, merged)
- [ ] Labels/tags
- [ ] Description/summary
- [ ] Files modified
- [ ] Reviewers assigned
- [ ] Approval status
- [ ] Pipeline/CI status
- [ ] Comments count
- [ ] Days since creation

**Alternative (if glab unavailable):**
```bash
# Export as JSON
glab mr list --state=opened --all --output json > open_merge_requests.json
```

---

### 2. Commit History (Priority: HIGH)

**Command:**
```bash
git log --oneline --grep='safety-protocols\|site-configurations' --all --since="2026-10-01"
```

**Required Fields:**
- [ ] Commit SHA (full hash)
- [ ] Author name and email
- [ ] Commit date
- [ ] Commit message (full text)
- [ ] Branch name
- [ ] Files changed (list)
- [ ] Lines added/removed (if available)

**Detailed View:**
```bash
git log --all --grep='safety\|fall\|protection\|height\|anchor\|guardrail' \
  --since="2026-10-01" --pretty=format:"%H|%an|%ae|%ad|%s" --date=iso
```

---

### 3. Branch Information (Priority: MEDIUM)

**Command:**
```bash
git branch -a -v
```

**Required Fields:**
- [ ] Branch name
- [ ] Last commit SHA
- [ ] Last commit date
- [ ] Ahead/behind main branch
- [ ] Protected status
- [ ] Associated MR (if any)

---

### 4. Pending Code Reviews (Priority: CRITICAL)

**Command:**
```bash
glab mr list --state=opened --reviewer-required
```

**Required Fields:**
- [ ] MR ID
- [ ] Reviewer(s) assigned
- [ ] Review status (pending, approved, changes requested)
- [ ] Days pending review
- [ ] Blocking issues/comments
- [ ] Safety impact assessment (if documented)

---

### 5. Specific Safety-Related Files (Priority: HIGH)

Please extract contents of any modified files matching these patterns:

- [ ] `**/safety-protocols/**`
- [ ] `**/site-configurations/**`
- [ ] `**/fall-protection/**`
- [ ] `**/osha-compliance/**`
- [ ] `*.yaml` or `*.yml` containing "safety", "fall", "anchor", "guardrail"
- [ ] `*.json` containing safety configurations
- [ ] `docs/safety/**`

**Command:**
```bash
git diff HEAD~10..HEAD -- '**/safety**' '**/fall**' '**/osha**' '**/anchor**' '**/guardrail**'
```

---

### 6. CI/CD Pipeline Status (Priority: MEDIUM)

**Command:**
```bash
glab pipeline list --state=running --state=failed
```

**Required Fields:**
- [ ] Pipeline ID
- [ ] Associated MR/branch
- [ ] Status (running, passed, failed)
- [ ] Failed stage/job name (if applicable)
- [ ] Error messages (if failed)

---

### 7. Tags and Releases (Priority: LOW)

**Command:**
```bash
git tag -l --sort=-version:refname
git describe --tags --always
```

**Required Fields:**
- [ ] Tag name
- [ ] Tag date
- [ ] Associated commit
- [ ] Release notes (if any)

---

## 📊 Data Format Preferences

**Preferred Format:** JSON or CSV (for automated analysis)

**Example JSON Structure:**
```json
{
  "merge_requests": [
    {
      "id": 142,
      "title": "Update fall arrest anchor specifications",
      "author": "j.smith",
      "created_at": "2026-11-15T14:30:00Z",
      "state": "opened",
      "labels": ["safety-protocols", "high-priority"],
      "changes": {
        "files": ["config/safety/anchors.yaml"],
        "additions": 45,
        "deletions": 12
      }
    }
  ]
}
```

---

## 🔍 Specific Analysis Targets

When extracting data, please flag any changes related to:

### Fall Protection Systems
- [ ] Anchor point specifications (load ratings, spacing)
- [ ] Guardrail dimensions (height, spacing, load capacity)
- [ ] Safety net installation parameters
- [ ] PFAS (Personal Fall Arrest System) configurations
- [ ] Lanyard/lifeline specifications

### Height Thresholds
- [ ] Work-at-height trigger heights
- [ ] Fall distance calculations
- [ ] Clearance requirements
- [ ] Deceleration distance settings

### Training & Documentation
- [ ] Training record schemas
- [ ] Inspection frequency configurations
- [ ] Competent person assignments
- [ ] Fall protection plan templates

### Site-Specific Configurations
- [ ] Leading edge protocols
- [ ] Roof work procedures
- [ ] Excavation fall protection
- [ ] Steel erection parameters

---

## ⚠️ Red Flags to Highlight

Please explicitly call out any changes that:

1. **Reduce existing safety margins** (e.g., lower anchor ratings, increased spacing)
2. **Remove or disable safety checks** in CI/CD pipelines
3. **Modify height thresholds** without documented engineering approval
4. **Change inspection frequencies** to less frequent intervals
5. **Update PPE specifications** to lower-rated equipment
6. **Remove required approvals** from workflows

---

## 📤 Delivery Method

**Secure Transfer Options:**

1. **Encrypted Archive:**
   ```bash
   tar czf metro_tower_safety_data.tar.gz \
     merge_requests.json \
     commits.json \
     branches.json \
     safety_file_diffs/
   
   # Then encrypt with gpg
   gpg -c metro_tower_safety_data.tar.gz
   ```

2. **Direct Paste:** For smaller datasets, paste directly into our chat

3. **Shared Location:** Upload to secure shared drive and provide path

---

## ⏱️ Timeline

| Milestone | Target Date |
|-----------|-------------|
| Data Extraction Complete | 2026-03-29 (today) |
| Gap Analysis Complete | 2026-03-29 (within 2 hours of data receipt) |
| Executive Summary Finalized | 2026-03-29 |
| Board Distribution | 2026-03-30 |

---

## 📞 Questions?

If any of these extracts are difficult to obtain or require different commands for your GitLab setup, let me know and I'll adjust the requirements.

**Key Contact:** Carlos Ramirez  
**Audit Reference:** MT-Q4-2026-SAFETY-001

---

*End of Data Requirements*
