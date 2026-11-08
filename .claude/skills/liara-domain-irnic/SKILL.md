---
name: liara-domain-irnic
description: Use when attaching a custom domain (.ir or international) to a Liara project, configuring DNS records (A, ANAME, CNAME) in IRNIC (nic.ir) or Cloudflare, or checking Let's Encrypt SSL issuance.
allowed-tools:
  - liara_domain_and_network
---

# `liara-domain-irnic` — Custom Domain, IRNIC (`.ir`) DNS & SSL Wizard Skill

## Instructions
1. **Register Domain in Liara:** Call `liara_domain_and_network(action="attach_domain")` (`POST /v1/domains`) to bind the domain to the target Liara project and retrieve assigned `CNAME` (`edge.liara.ir`) and Static IP (`A` record) values.
2. **Explicitly Disclose API Boundaries:** Clearly inform the user that external domain registrars such as IRNIC (`nic.ir`) or Cloudflare do not provide direct API access to Liara, so DNS record insertion in IRNIC is an out-of-band guided user action.
3. **Render Interactive DNS Guide (`DomainDNSGuideWidget`):** Present one-click copyable `A`/`ANAME` (`@ -> 185.141.107.44`) and `CNAME` (`www -> edge.liara.ir`) records along with step-by-step Persian instructions for IRNIC (`nic.ir`).
4. **Verify DNS Propagation & SSL:** Call `POST /v1/domains/{id}/check` via `check_domain_dns_ssl` to confirm DNS resolution and automated Let's Encrypt SSL certificate issuance.

## Examples
- **User:** «دامنه shop.example.ir رو چطوری به پروژه‌ام در لیارا وصل کنم؟»
- **Agent Action:** Registers the domain in Liara, states the IRNIC API boundary transparently, and renders `DomainDNSGuideWidget` with one-click copy records and SSL check button.

## Constraints
- NEVER hallucinate or fabricate an API endpoint that logs into `nic.ir` on the user's behalf.
- ALWAYS provide exact record types (`A`, `CNAME`, `NS`) and TTL recommendations.
