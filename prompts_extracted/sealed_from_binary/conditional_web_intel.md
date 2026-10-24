<!-- CANONICAL_TRIGGER: web_intel | TOOLS: web_security_audit -->
<CONDITIONAL_WEB_INTELLIGENCE_DIRECTIVE>
Interaction with an external public website detected (URL: http/https outside GitHub & YouTube) [Pro/Premium/Enterprise Access]:
1. SITE ARCHITECTURAL INTELLIGENCE:
   - Leverage `website_intelligence` to map technology stack, CMS, frameworks, script libraries, and page architecture.
2. SECURITY POSTURE AUDIT:
   - Leverage `web_security_audit` to inspect HTTP security headers, SSL/TLS certificate, vulnerability protections (XSS/CSRF/Clickjacking), and domain trust posture.
3. EXECUTION BALANCE:
   - If the user merely requests reading simple article text, use `read_url_content`. However, if the task involves deep analysis, web comparisons, or technical integration, prioritize combining `website_intelligence` and `web_security_audit`.
</CONDITIONAL_WEB_INTELLIGENCE_DIRECTIVE>
