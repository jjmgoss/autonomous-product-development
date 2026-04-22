# Candidate Evidence Map

## Candidate: Secure Agent Workflow Proxy
- short thesis: HTTP proxy layer that uses LLMs as a judge to secure agent actions in production
- supporting evidence IDs: SRC-004, SRC-001
- weakening evidence IDs: SRC-005
- substitute pressure notes: Existing proxies, manual review, but no agent-specific solution
- open questions that could change ranking: Will LLM-based proxies scale and avoid false positives?

## Candidate: Automated Secrets Management for DevOps
- short thesis: Automated secrets scanning, rotation, and environment variable management for developer platforms
- supporting evidence IDs: SRC-001
- weakening evidence IDs: SRC-004
- substitute pressure notes: HashiCorp Vault, AWS Secrets Manager, but integration is often weak
- open questions that could change ranking: Can automation avoid breaking workflows or leaking secrets?

## Candidate: DevOps Knowledge Base Generator
- short thesis: Tool to automatically generate and maintain a technical reference repository for backend and DevOps teams
- supporting evidence IDs: SRC-002
- weakening evidence IDs: SRC-003
- substitute pressure notes: Notion, Confluence, GitHub Wikis, but onboarding and updating are pain points
- open questions that could change ranking: Can automation keep knowledge current and relevant?

## Candidate: Resilience Pattern Library
- short thesis: Curated, actionable library of real-world resilience patterns for developer workflow automation
- supporting evidence IDs: SRC-005
- weakening evidence IDs: SRC-003
- substitute pressure notes: Blogs, Stack Overflow, but scattered and not actionable
- open questions that could change ranking: Will teams actually adopt and maintain the library?

## Candidate: Job Orchestration Metrics Cleaner
- short thesis: Tool to automatically filter and clean noisy retry/failure metrics in job orchestration systems
- supporting evidence IDs: SRC-003
- weakening evidence IDs: SRC-005
- substitute pressure notes: Custom scripts, manual dashboards, but not automated
- open questions that could change ranking: Can it generalize across platforms and avoid hiding real failures?
