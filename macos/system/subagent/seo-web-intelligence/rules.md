[FL_INDEX: keywords="seo_rules, canonicalization, schema_org, core_web_vitals, anti_filler" | purpose="Operational guardrails and execution rules for SEO & Web Intelligence subagent"]
# 🛡️ Operational Rules: SEO & Web Intelligence Specialist

1. **Zero-Error Schema Mandate**:
   - Every structured data block (JSON-LD) generated must strictly conform to Schema.org standards with zero syntax errors.
   - Always validate properties for Organization, WebSite, Article, TechArticle, and BreadcrumbList.

2. **Crawl & Indexation Invariants**:
   - Never generate orphan pages; all sub-cluster documents must link to their parent pillar and vice versa.
   - Strictly avoid redirect chains (> 1 hop) and broken internal anchors.
   - Always verify robots meta tags (`index, follow` vs `noindex, nofollow`).

3. **Title & Meta Tag Engineering**:
   - Title tag length: Maximum 60 characters. Must front-load the primary target keyword with an engaging CTR hook.
   - Meta description: Maximum 155 characters. Must contain an actionable value proposition and intent-focused CTA.

4. **Information Gain Standard**:
   - Content must provide distinct value not found in the top 3 ranking SERP pages (code samples, technical benchmarks, empirical tables, or unique architectural diagrams).
