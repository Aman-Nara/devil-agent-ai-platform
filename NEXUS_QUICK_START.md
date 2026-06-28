# NEXUS Quick Start Guide

## 🚀 Getting Started

Visit **https://your-domain.com** and log in to access the NEXUS tab.

---

## 📋 Strategic Brief

**Purpose:** Generate comprehensive strategic analysis for any engineering objective.

**How to Use:**
1. Enter your objective (e.g., Migrate authentication to OAuth2)
2. Optionally add constraints (one per line)
3. Click Generate Brief

**What You Get:**
- Risks analysis with mitigation strategies
- Architecture decisions with alternatives
- Estimated effort in hours/minutes
- Success metrics

**Example:**


---

## 🗺️ Task Graph

**Purpose:** Break down complex objectives into executable task sequences.

**How to Use:**
1. Enter your objective
2. Click Generate Plan

**What You Get:**
- Numbered task nodes
- Dependency relationships
- Critical path highlighting
- Total node count

**Example:**


**Result:** 6 nodes showing design → API → UI → testing flow

---

## 🛡️ Sentinel Scan

**Purpose:** Detect security vulnerabilities and code smells.

**How to Use:**
1. Paste code to scan
2. Click Scan Code

**What You Get:**
- Security score (0-100)
- Severity-tagged findings (high/medium/low)
- Line numbers for each issue
- Specific rule violations (OWASP, hardcoded secrets, etc.)

**Example:**


**Result:** Score: 40/100, 2 high-severity findings

---

## ⚖️ Decision Records

**Purpose:** Document architectural decisions for future reference.

**How to Use:**
1. Fill in decision details:
   - Title
   - Context (why this decision is needed)
   - Options (one per line)
   - Final decision
   - Consequences
2. Click Create Decision

**What You Get:**
- Unique DR-XXX identifier
- Timestamped record
- Status badge
- Searchable history

**Example:**


---

## 🧠 Cognitive Load

**Purpose:** Measure code complexity and maintainability.

**How to Use:**
1. Paste function or code block
2. Click Analyze Code

**What You Get:**
- Cognitive load score with band (low/medium/high)
- Cyclomatic complexity
- Max nesting depth
- Lines of code count
- Actionable recommendations

**Example:**


**Result:** Score: 45.2 (medium), Recommendation: Extract 2 helper functions

---

## 💡 Tips

1. **Strategic Brief** - Use at project start or major feature planning
2. **Task Graph** - Great for sprint planning and dependency mapping
3. **Sentinel Scan** - Run before code review or deployment
4. **Decision Records** - Document EVERY significant architectural choice
5. **Cognitive Load** - Check any function > 20 lines or with > 3 nesting levels

---

## 🔐 Authentication

All NEXUS features require authentication. Your JWT token is automatically included in requests once you're logged in.

---

## 🐛 Troubleshooting

**Not authenticated error:**
- Refresh the page and log in again
- Your session may have expired

**No results returned:**
- Check that you filled all required fields
- Verify your input format matches the examples

**Slow response:**
- Complex briefs/plans may take 1-2 seconds
- This is normal for AI-powered analysis

---

## 📖 API Endpoints (for developers)

All endpoints are at 

| Endpoint | Method | Purpose |
|----------|--------|---------|
|  | POST | Strategic analysis |
|  | POST | Task decomposition |
|  | POST | Security scanning |
|  | GET/POST | Decision records |
|  | POST | Complexity analysis |

**Authentication:** Include  header

---

## 🎨 UI Features

- **Dark theme** - Easy on the eyes for long sessions
- **Copy results** - Use the expandable JSON sections
- **Navigation** - Secondary sidebar for quick section switching
- **Loading states** - Clear feedback during processing
- **Color coding** - Red (high severity), Yellow (medium), Blue (info)

---

## 📞 Support

For issues or questions:
1. Check browser console (F12) for errors
2. Verify backend is running: {"ok":true,"name":"NEXUS Autonomous Engineering OS","prompt_version":"1.0","layers":["strategic","tactical","execution","sentinel"],"genome":{"project":"Devil Agent","version":"3.0.0","stack":["FastAPI","React+TS","MongoDB","Nginx","Tailwind"],"adr_count":2,"open_failures":0,"last_deploy":null,"tech_debt":[],"baselines":{"p99_ms":250,"coverage_pct":0,"bundle_kb":0},"updated_at":"2026-06-08T18:07:44.971734+00:00","log_entries":10},"ts":"2026-06-08T18:26:48.134576+00:00"}
3. Review  for technical details

---

**Last Updated:** June 8, 2026  
**Version:** 1.0 - Initial Release
