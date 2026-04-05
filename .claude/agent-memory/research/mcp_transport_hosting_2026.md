---
name: MCP Transport and Hosting Landscape 2026
description: Complete picture of MCP transport methods, hosting platforms, gateways, and auth patterns as of April 2026
type: reference
---

# MCP Transport and Hosting Landscape — April 2026

Researched 2026-04-05. Source file: ~/epigenome/chromatin/euchromatin/mcp-transport-hosting-landscape-2026-04.md

## Key Facts

**Transports (official):**
- stdio — local only, single-user
- Streamable HTTP — current standard for remote, single endpoint POST+GET
- SSE — deprecated March 2025, don't build new

**Transports (emerging, not in spec):**
- gRPC — Google contributing pluggable package to MCP SDKs, ~mid-2026, not in spec
- WebSocket — SEP-1288, community proposal, not accepted yet

**Spec roadmap (next release ~June 2026):**
- Stateless protocol redesign (sessions to data layer)
- Server Cards (/.well-known/mcp.json discovery)
- NOT adding new transports this cycle

**Hosting platforms:**
- Cloudflare Workers — best for low-cost remote, edge, near-zero cold start
- Vercel — Fluid Compute, good for Next.js ecosystem
- Prefect Horizon — managed MCP platform (FastMCP team), CI/CD + RBAC + audit, GA Jan 2026
- Railway/Render — containers, better for stateful servers

**Gateways:**
- Cloudflare MCP Server Portals (Zero Trust) — enterprise, single URL over N servers
- Portkey MCP Gateway — managed/self-hosted, RBAC, multi-tenant, SOC 2
- mcp-remote (npm) — stdio client -> remote HTTP bridge, OAuth 2.1 + PKCE
- mcp-proxy (sparfenyuk) — stdio server -> HTTP bridge (inverse of mcp-remote)

**Auth:**
- OAuth 2.1 + PKCE mandatory for public remote servers (spec Nov 2025)
- CIMD replaced Dynamic Client Registration (Nov 2025)
- URL Mode Elicitation for sensitive delegated flows
