---
name: monarch-money
description: Analyze Monarch Money accounts, transactions, cashflow, budgets, recurring charges, and investments with the mmoney CLI. Use for personal finance questions, spending reviews, budget checks, net worth summaries, and safe Monarch Money updates.
---

# Monarch Money

Use the `mmoney` CLI to inspect Monarch Money data and answer personal finance questions with context. `mmoney` is an unofficial community CLI for Monarch Money.

## Onboarding

Run `python3 scripts/onboard.py` from this skill directory to collect non-secret local preferences such as the CLI command name, preferred output format, default date window, and privacy level. The script writes `~/.config/agent-skills/monarch-money.json`.

Do not collect or store Monarch passwords, MFA secrets, device IDs, browser tokens, or session files in the skill config. Authentication belongs in `mmoney auth login` and `mmoney config`.

## Safety

- Start in read-only mode. Most tasks should only run list, get, summary, status, or details commands.
- Use `-f json` for structured output whenever the installed CLI supports it.
- Never ask the user to paste passwords, MFA secrets, browser tokens, session files, or full account numbers into chat.
- Use interactive login by default so passwords are not captured in shell history.
- Ask for explicit confirmation before every command that uses `--allow-mutations`.
- Summarize sensitive financial data at the level needed for the request. Avoid repeating full transaction IDs, account IDs, or unnecessary identifying details.
- If repeated 403 errors occur, treat them as likely rate limiting and wait before retrying.

## Authentication

Check auth before data pulls:

```bash
mmoney auth status
```

If login is needed, prefer interactive auth:

```bash
mmoney auth login -e EMAIL --mfa-code 123456
```

If the user has a secure MFA secret workflow, the CLI also supports MFA-secret login. Do not ask the user to reveal the secret in chat. Have them run the command locally or provide it through their normal secure credential injection.

Device ID setup, when needed, should be handled by the user in their browser and saved through:

```bash
mmoney config set device-id ID
```

## Analysis Stance

Explore before interrogating. When the user asks a financial question:

1. Pull the relevant data first.
2. Analyze what is visible.
3. Present concise insights, then ask focused follow-up questions only if needed.

Build a financial picture across:

- Net worth: assets minus liabilities.
- Liquidity: checking, savings, money market, taxable brokerage, retirement, CDs, and restricted funds.
- Cashflow: income, expenses, savings, and savings rate.
- Debt profile: high-interest debt versus lower-interest debt.
- Investments: holdings, allocation, account type, and concentration risk.

Flag concerns proactively, including low cash reserves, high credit-card balances, irregular income, forgotten subscriptions, large uncategorized transactions, stale institution connections, and budget categories that are consistently over plan.

## Data Model

- Institutions have credentials/connections.
- Credentials link accounts from a bank or brokerage login.
- Accounts contain transactions, holdings, and balance history.
- Transactions have an account, category, merchant, and optional tags.
- Categories belong to category groups.

## Common Commands

Use the configured CLI name from `~/.config/agent-skills/monarch-money.json` if present. Examples below assume `mmoney`.

```bash
mmoney -f json accounts list
mmoney -f json accounts types
mmoney -f json accounts refresh-status
mmoney -f json transactions list --limit 50
mmoney -f json transactions list --search "merchant" --limit 20
mmoney -f json transactions list --start-date 2026-01-01 --end-date 2026-01-31
mmoney -f json transactions get TXN_ID
mmoney -f json transactions summary
mmoney -f json categories list
mmoney -f json categories groups
mmoney -f json tags list
mmoney -f json budgets list
mmoney -f json cashflow summary
mmoney -f json cashflow details
mmoney -f json recurring list
mmoney -f json institutions list
mmoney -f json holdings list ACCOUNT_ID
mmoney -f json holdings history ACCOUNT_ID
mmoney -f json holdings snapshots
mmoney -f json holdings balances
```

Use `mmoney --help` or the relevant subcommand help if an option differs in the installed version.

## Useful Patterns

Account balances:

```bash
mmoney -f json accounts list | jq '.accounts[] | {name: .displayName, balance: .currentBalance, type: .type.name}'
```

Net worth:

```bash
mmoney -f json accounts list | jq '[.accounts[] | select(.includeInNetWorth) | if .isAsset then .currentBalance else -.currentBalance end] | add'
```

Recurring subscriptions:

```bash
mmoney -f json recurring list | jq '.recurringTransactionItems[] | {merchant: .stream.merchant.name, amount: .stream.amount, frequency: .stream.frequency}'
```

Monthly spending by category:

```bash
mmoney -f json cashflow details --start-date 2026-01-01 --end-date 2026-01-31
```

## Write Operations

The CLI runs read-only by default. To modify data, it requires `--allow-mutations`, for example:

```bash
mmoney --allow-mutations transactions update TXN_ID --category-id NEW_CAT_ID
```

Before any mutation:

1. Show the exact intended command with sensitive IDs shortened when presenting to the user.
2. Explain what will change.
3. Ask for confirmation.
4. Run one mutation at a time.
5. Verify the changed object afterward with a read-only command.

## Error Handling

Common error codes:

- `AUTH_REQUIRED`: run or guide interactive login.
- `AUTH_FAILED`: credentials or MFA failed; ask the user to retry through the CLI.
- `MUTATION_BLOCKED`: the command needs `--allow-mutations`; confirm before adding it.
- `VALIDATION_MISSING_FIELD`: rerun with the required parameter.
- `NOT_FOUND`: refresh IDs or pull the relevant list again.
- `API_ERROR`: report the API message and avoid guessing.
