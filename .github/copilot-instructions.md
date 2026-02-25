# GitHub Copilot Instructions

## Security Guidelines

### 🚨 CRITICAL: NEVER Share `.env` File with Copilot

**WARNING: The `.env` file contains SECRET credentials that MUST NEVER be:**
- ❌ Pasted into Copilot chat or prompts
- ❌ Included in code context windows for AI assistance
- ❌ Shared with any AI coding tool (Copilot, ChatGPT, Claude, etc.)
- ❌ Referenced directly in prompts (e.g., "here's my OPENAI_API_KEY")
- ❌ Uploaded as file attachments to AI or external services

**CONSEQUENCE:** Exposing `.env` will leak API keys, database credentials, and authentication tokens to external AI services.

### What To Do If You Accidentally Share Secrets

**Immediate Actions:**
1. **STOP** using the compromised credentials immediately
2. **REGENERATE** all exposed API keys/tokens in their respective services
3. **UPDATE** `.env` with new secrets locally (do NOT re-share)
4. **DELETE** the AI chat history if possible (depends on AI service)
5. **ALERT** your team if using shared credentials

Example:
- If you pasted `OPENAI_API_KEY=sk-...` → Regenerate the key in OpenAI account immediately
- If you exposed database credentials → Rotate passwords in your database admin console
- If you exposed other secrets → Repeat for each service

### Safe Way to Ask for Code Help

**✅ DO This:**
```
"I need to load OPENAI_API_KEY from environment variables in my Python code. 
Can you show me how to use os.getenv()?"
```

**❌ DON'T Do This:**
```
"My OPENAI_API_KEY is sk-proj-abc123xyz... and I'm getting an error"
```

### Safe Code Context Rules

When requesting Copilot assistance:
1. **EXCLUDE** the `.env` file from your context
2. **EXCLUDE** all `.env.*` variants (`.env.local`, `.env.production`, etc.)
3. **SAFE TO SHARE:** Code, configuration, architecture, documentation
4. **ALWAYS REVIEW** Copilot suggestions before applying to production code
5. **USE [REDACTED]** if you must reference secret names in chat

### Environment Variables This Project Uses

**NEVER share these with Copilot:**
- `OPENAI_API_KEY` ← API authentication token
- `OPENAI_REALTIME_MODEL` ← Model identifier (public, but keep private for consistency)
- Any database connection strings or credentials
- Any third-party API tokens

### For Code Reviewers & Team Leads

**PR/Code Review Checklist:**
- [ ] Verify `.env` file was NOT pasted in PR description
- [ ] Verify no secrets appear in commit messages
- [ ] Verify no secrets appear in code comments or docstrings
- [ ] If external AI was used, confirm context was safe (no `.env` included)
- [ ] Use `[REDACTED]` format for any sensitive references in tickets

**Example comment:**
```
"Set OPENAI_API_KEY=[REDACTED] in your .env file to enable this feature"
```

## For Copilot Enterprise Users

If your organization has **Copilot Business or Enterprise**, configure Content Exclusion at the organization level:

**In GitHub → Organization Settings → Copilot:**
```yaml
"*":
  - "**/.env"
  - "**/.env.local"
  - "**/.env.*.local"
  - "**/secrets/**"
  - "**/*.key"
  - "**/*.pem"
```

This provides hard technical enforcement across all IDEs and prevents Copilot from accessing these files.

**Reference:** [GitHub Copilot Content Exclusion](https://docs.github.com/en/copilot/how-tos/configure-content-exclusion/exclude-content-from-copilot)

## Enforcement & Accountability

- `.env` is in `.gitignore` (prevents accidental commits)
- `.github/copilot-instructions.md` serves as documented guidance
- Code reviews must verify no secrets in context
- Developers are responsible for following these guidelines
- Report accidental exposures immediately to the team security contact

