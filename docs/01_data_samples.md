# Raw Data Samples (skills_raw.jsonl)

## Keys set

Each row in `skills_scraper/data/skills_raw.jsonl` is a JSON object with these keys:

- `name`
- `description`
- `example_usage`
- `weekly_installs`
- `first_seen`
- `skill_url`
- `total_installs`

**Note:** The `example_usage` field can be very long (thousands of characters). In the third sample below, the displayed excerpt is truncated; the full value is in the file.

---

## First 3 objects (pretty-printed)

### Object 1

```json
{
  "name": "find-skills",
  "description": "Find Skills This skill helps you discover and install skills from the open agent skills ecosystem.",
  "example_usage": "Find Skills This skill helps you discover and install skills from the open agent skills ecosystem. When to Use This Skill Use this skill when the user: Asks \"how do I do X\" where X might be a common task with an existing skill Says \"find a skill for X\" or \"is there a skill for X\" Asks \"can you do X\" where X is a specialized capability Expresses interest in extending agent capabilities Wants to search for tools, templates, or workflows Mentions they wish they had help with a specific domain (design, testing, deployment, etc.) What is the Skills CLI? The Skills CLI ( npx skills ) is the package manager for the open agent skills ecosystem. Skills are modular packages that extend agent capabilities with specialized knowledge, workflows, and tools. Key commands: npx skills find [query] - Search for skills interactively or by keyword npx skills add &#x3C;package> - Install a skill from GitHub or other sources npx skills check - Check for skill updates npx skills update - Update all installed skills Browse skills at: https://skills.sh/ How to Help Users Find Skills Step 1: Understand What They Need When a user asks for help with something, identify: The domain (e.g., React, testing, design, deployment) The specific task (e.g., writing tests, creating animations, reviewing PRs) Whether this is a common enough task that a skill likely exists Step 2: Search for Skills Run the find command with a relevant query: npx skills find [ query ] For example: User asks \"how do I make my React app faster?\" \u2192 npx skills find react performance User asks \"can you help me with PR reviews?\" \u2192 npx skills find pr review User asks \"I need to create a changelog\" \u2192 npx skills find changelog The command will return results like: Install with npx skills add &#x3C;owner/repo@skill> vercel-labs/agent-skills@vercel-react-best-practices \u2514 https://skills.sh/vercel-labs/agent-skills/vercel-react-best-practices Step 3: Present Options to the User When you find relevant skills, present them to the user with: The skill name and what it does The install command they can run A link to learn more at skills.sh Example response: I found a skill that might help! The \"vercel-react-best-practices\" skill provides React and Next.js performance optimization guidelines from Vercel Engineering. To install it: npx skills add vercel-labs/agent-skills@vercel-react-best-practices Learn more: https://skills.sh/vercel-labs/agent-skills/vercel-react-best-practices Step 4: Offer to Install If the user wants to proceed, you can install the skill for them: npx skills add &#x3C; owner/repo@skill > -g -y The -g flag installs globally (user-level) and -y skips confirmation prompts. Common Skill Categories When searching, consider these common categories: Category Example Queries Web Development react, nextjs, typescript, css, tailwind Testing testing, jest, playwright, e2e DevOps deploy, docker, kubernetes, ci-cd Documentation docs, readme, changelog, api-docs Code Quality review, lint, refactor, best-practices Design ui, ux, design-system, accessibility Productivity workflow, automation, git Tips for Effective Searches Use specific keywords : \"react testing\" is better than just \"testing\" Try alternative terms : If \"deploy\" doesn't work, try \"deployment\" or \"ci-cd\" Check popular sources : Many skills come from vercel-labs/agent-skills or ComposioHQ/awesome-claude-skills When No Skills Are Found If no relevant skills exist: Acknowledge that no existing skill was found Offer to help with the task directly using your general capabilities Suggest the user could create their own skill with npx skills init Example: I searched for skills related to \"xyz\" but didn't find any matches. I can still help you with this task directly! Would you like me to proceed? If this is something you do often, you could create your own skill: npx skills init my-xyz-skill",
  "weekly_installs": "223.0K",
  "first_seen": "Jan 26, 2026",
  "skill_url": "https://github.com/vercel-labs/skills",
  "total_installs": "222973"
}
```

### Object 2

```json
{
  "name": "vitest",
  "description": "Vitest is a next-generation testing framework powered by Vite.",
  "example_usage": "Vitest is a next-generation testing framework powered by Vite. It provides a Jest-compatible API with native ESM, TypeScript, and JSX support out of the box. Vitest shares the same config, transformers, resolvers, and plugins with your Vite app. Key Features: Vite-native: Uses Vite's transformation pipeline for fast HMR-like test updates Jest-compatible: Drop-in replacement for most Jest test suites Smart watch mode: Only reruns affected tests based on module graph Native ESM, TypeScript, JSX support without configuration Multi-threaded workers for parallel test execution Built-in coverage via V8 or Istanbul Snapshot testing, mocking, and spy utilities The skill is based on Vitest 3.x, generated at 2026-01-28. Core Topic Description Reference Configuration Vitest and Vite config integration, defineConfig usage core-config CLI Command line interface, commands and options core-cli Test API test/it function, modifiers like skip, only, concurrent core-test-api Describe API describe/suite for grouping tests and nested suites core-describe Expect API Assertions with toBe, toEqual, matchers and asymmetric matchers core-expect Hooks beforeEach, afterEach, beforeAll, afterAll, aroundEach core-hooks Features Topic Description Reference Mocking Mock functions, modules, timers, dates with vi utilities features-mocking Snapshots Snapshot testing with toMatchSnapshot and inline snapshots features-snapshots Coverage Code coverage with V8 or Istanbul providers features-coverage Test Context Test fixtures, context.expect, test.extend for custom fixtures features-context Concurrency Concurrent tests, parallel execution, sharding features-concurrency Filtering Filter tests by name, file patterns, tags features-filtering Advanced Topic Description Reference Vi Utilities vi helper: mock, spyOn, fake timers, hoisted, waitFor advanced-vi Environments Test environments: node, jsdom, happy-dom, custom advanced-environments Type Testing Type-level testing with expectTypeOf and assertType advanced-type-testing Projects Multi-project workspaces, different configs per project advanced-projects",
  "weekly_installs": "4.2K",
  "first_seen": "Jan 28, 2026",
  "skill_url": "https://github.com/antfu/skills",
  "total_installs": "4193"
}
```

### Object 3 (example_usage truncated in this excerpt)

The `example_usage` field in object 3 is very long (tens of thousands of characters). Below it is truncated for display; the full content is in `skills_scraper/data/skills_raw.jsonl` (third line).

```json
{
  "name": "clawdirect-dev",
  "description": "ClawDirect-Dev Build agent-facing web experiences with ATXP-based authentication.",
  "example_usage": "ClawDirect-Dev Build agent-facing web experiences with ATXP-based authentication. Reference implementation : https://github.com/napoleond/clawdirect What is ATXP? ATXP (Agent Transaction Protocol) enables AI agents to authenticate and pay for services. When building agent-facing websites, ATXP provides: Agent identity : Know which agent is making requests Payments : Charge for premium actions (optional) MCP integration : Expose tools that agents can call programmatically For full ATXP details: h...[truncated]",
  "weekly_installs": "4.2K",
  "first_seen": "Jan 30, 2026",
  "skill_url": "https://github.com/napoleond/clawdirect",
  "total_installs": "4213"
}
```
