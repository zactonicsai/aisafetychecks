# aisafetychecks

AI security in 2026 is split into three layers: **credentials that prove people can govern or attack AI systems**, **frameworks that name the risks**, and **repeatable testing that proves what a specific LLM or agent can actually do**. Capability and security are not the same thing. A more capable model is often a more dangerous one if tools, data, or agency are attached.

## AI security certifications

### Individual / professional credentials

These are the ones most often cited for security, red team, and governance roles in 2026.

| Credential | Issuer | Best for | Notes |
|---|---|---|---|
| **CompTIA SecAI+** | CompTIA | Entry–mid security engineers | Vendor-neutral foundation: securing AI systems, guardrails, AI-assisted ops. Good first AI security cert. |
| **ISACA AAISM** | ISACA | Security managers / GRC | Advanced in AI Security Management. Requires active **CISM or CISSP**. Governance, risk, AI security controls. Strong enterprise signal. |
| **ISACA AAIA / AAIR** | ISACA | Auditors / risk owners | AI Audit and AI Risk add-ons for people who already hold CISA/CIA or equivalent risk credentials. |
| **GIAC GAIPS** | SANS/GIAC | LLM / GenAI app security | Tied to **SEC545: GenAI and LLM Application Security**. Prompt injection, jailbreaks, RAG, supply chain, AI red teaming. |
| **GIAC GASAE** | SANS/GIAC | Agentic / automation security | AI security automation and agentic systems across offensive, defensive, and cloud use. |
| **GIAC GMLE** | SANS/GIAC | ML pipeline security | Build and secure ML pipelines, model integrity, MLSecOps. |
| **CAISP** | Practical DevSecOps | Hands-on AppSec / red team | Lab-heavy: STRIDE on AI, model-weight scanning, LLM sanitization, OWASP/ATLAS-mapped attacks. Practical exam. |
| **OSAI** | OffSec | Offensive specialists | 24-hour hands-on: bypass guardrails, poison RAG, exploit vector DBs, hijack multi-agent systems. High bar (OSCP-level expected). |
| **COASP** | EC-Council | Offensive AI / pentest | Red-teaming LLMs, agent memory, checkpoint issues; mapped to ATLAS and OWASP LLM Top 10. |
| **ISC2 AI Security Certificate** | ISC2 | Strategy / architecture | Currently a learning certificate; a full professional AI security cert has been in development. CISSP itself now includes AI risk content. |
| **IAPP AIGP** | IAPP | Privacy, legal, compliance | AI Governance Professional. EU AI Act, NIST AI RMF, ethics — not a red-team cert. |
| **CSA / CSAI credentials** | Cloud Security Alliance | Trust / assurance | Trusted AI Safety Expert and related CSAI Foundation work (controls matrix, auditor path). |

Also common as **adjacent** credentials:

- **CISSP / CISM** with the 2026 AI-updated blueprints
- Cloud: updated **AWS Security Specialty (SCS-C03)** with GenAI coverage; Microsoft paths around Security Copilot / Purview / agent access; Google Cloud security with Vertex AI controls
- Vendor or boutique options exist (CAISS, CAISF, CSPAI, etc.). Treat name recognition and hands-on exam quality as the filter.

### Organizational certification

**ISO/IEC 42001:2023** is the certifiable **AI Management System (AIMS)** standard. It certifies the *governance system* (risk, lifecycle, suppliers, human oversight, monitoring), not that a particular model is “safe.” It pairs well with ISO 27001/27701 and maps to NIST AI RMF and EU AI Act expectations. Lead Implementer / Lead Auditor training is the people path; accredited third-party audit is the org path.

---

## Frameworks that define threats and test coverage

Use these as the shared language for scoping tests and writing findings.

1. **OWASP GenAI LLM Top 10 (2026)** — application-layer risk list, now blended from expert consensus plus incident data. Current ranking:
   1. Prompt Injection  
   2. Sensitive Information Disclosure  
   3. Excessive Agency  
   4. Supply Chain  
   5. Data and Model Poisoning  
   6. Unbounded Consumption  
   7. Misinformation  
   8. Hidden Context Exposure  
   9. Vector and Embedding Weaknesses  
   10. Improper Output Handling  

   Pair it with the **OWASP Top 10 for Agentic Applications** (goal hijacking, tool misuse, identity/privilege abuse, cascading multi-agent failures).

2. **MITRE ATLAS** — ATT&CK-style matrix for attacks *on* and *with* AI. ~16 tactics including AI-specific **AI Model Access** and **AI Attack Staging/Adaptation**, plus techniques such as LLM prompt injection (direct/indirect), system-prompt extraction, RAG credential harvest, agent tool invocation/exfil, data poisoning, and model theft. Use it for threat modeling and red-team playbooks.

3. **NIST AI RMF 1.0 + Generative AI Profile (NIST AI 600-1)** — Govern / Map / Measure / Manage. Red teaming and adversarial evaluation sit mainly in **Measure** (especially security/resilience) and feed **Manage**. NIST also publishes adversarial-ML taxonomy work and evaluation programs such as ARIA.

4. **ISO/IEC 42001 + NIST SSDF for GenAI (SP 800-218A)** — lifecycle and secure development practices for foundation models and GenAI software.

---

## Key security testing processes for LLMs and AI use cases

A defensible program is a loop, not a one-off prompt-injection demo: **threat model → discover → measure → mitigate → regress in CI/CD → monitor in production**.

### 1. Scope and threat model first
Enumerate: model(s), system prompt / hidden context, tools/APIs, RAG corpora and vector stores, memory, identity/auth, tenants, rate limits, logging, and what a successful attack would actually achieve (data theft, unauthorized action, fraud, safety violation, DoS). Map each asset to OWASP LLM items and ATLAS techniques. If the system has no tools, Excessive Agency is out of scope; if it has RAG, indirect injection and embedding attacks are in scope.

### 2. Reconnaissance / capability elicitation
Before attacking, verify what the system *can* do:

- Fingerprint model family/version and configuration (temperature, tool schema).
- Attempt system-prompt and hidden-context extraction.
- Inventory tools, MCP servers, plugins, and permissions by inducing descriptions, reading error schemas, and triggering tool use.
- Identify data sources (which collections, which tenants, PII classes).
- Map identity: can a user spoof role, replay a session, or inject identity claims into the prompt?

This is how you “verify what an LLM can do” in a security sense: not MMLU score, but **reachable data + reachable actions + bypassable policy**.

### 3. AI red teaming (human + automated)
Typical phases: identity-context attacks → content-vector attacks (direct/indirect injection, jailbreaks, multi-turn crescendo) → retrieval/RAG poisoning → agent/tool escalation → persistence (memory, poisoned docs, malicious skills) → impact (exfil, unauthorized action, DoS).

Common tool stack:

- **Garak** — probe scanner (jailbreak, leakage, injection-style failures)
- **PyRIT** — Microsoft orchestrator for multi-turn / multi-strategy attacks
- **Promptfoo / DeepTeam / eval harnesses** — adversarial cases plus CI gates
- Domain corpora: **HarmBench**, **JailbreakBench**, StrongREJECT, custom threat-model suites

Human testers still matter for multi-turn social engineering, domain expertise (legal/medical/finance), and novel agent chains. Automated tools miss a lot of that.

### 4. Surface-specific tests
Treat the app as five surfaces, not one chat box:

| Surface | What you test |
|---|---|
| Input / output | Direct injection, jailbreak, policy bypass, XSS/HTML/Markdown in answers, code execution if output is rendered or eval’d |
| Retrieval (RAG) | Indirect injection in docs/URLs, poisoned embeddings, cross-tenant retrieval, citation integrity |
| Agent / tools | Goal hijacking, over-privileged tools, confused-deputy API calls, MCP/tool-definition poisoning |
| Model / weights / supply chain | Untrusted fine-tunes, pickle/GGUF/artifact scanning, dependency and base-model provenance |
| Runtime / infra | Authn/z on the inference API, cost/token DoS, log leakage, secret storage in prompts |

### 5. Safety and security regression (eval harness)
Convert every confirmed failure into a scored test with a threshold (e.g., “prompt-injection ASR &lt; 5% on 500 cases,” “zero credential exfil”). Run in CI/CD and block releases that regress. Use both deterministic checks (regex for secrets, schema validation) and LLM-as-judge — and calibrate the judge; different jailbreak evaluators disagree.

### 6. Supply-chain and model integrity
Scan model artifacts, training/fine-tune data lineage, third-party GPTs/skills/MCP servers, and inference engines. Poisoning and backdoored checkpoints are in-scope even if the chat UI looks clean.

### 7. Runtime / continuous assurance
Gateway or proxy inspection for injection, PII, anomalous tool-call graphs, cost spikes, and drift. Logging must capture prompts, retrieved chunks, tool calls, and policy verdicts — otherwise you cannot investigate.

### 8. Governance testing
For regulated use: DPIA/AIIA evidence, human-oversight checks, bias/fairness suites, misinformation/hallucination rates on *your* domain data, and ISO 42001 / NIST AI RMF control evidence. Security red teaming does not replace this.

---

## How to verify what an LLM can do vs what it must not do

Keep two scorecards. Mixing them produces false comfort (“it scores well on MMLU, so it is safe”).

**Capability verification (intended use)**  
- General: MMLU-class knowledge, HELM-style holistic evals, domain benchmarks  
- Task: tool-use / agent success rate, RAG answer faithfulness + citation correctness, latency/cost  
- Offensive capability (if that is the product): exploit-development evals exist and show large model-to-model gaps — treat those as dual-use risk, not marketing metrics  

**Security / safety verification (abuse and failure)**  
- Attack success rate (ASR) by category: jailbreak, direct/indirect injection, data exfil, tool misuse  
- Refusal quality vs over-refusal (false refusal on benign security questions)  
- Leakage: system prompt, RAG docs, other tenants’ data, training-data memorization  
- Agency: can it send email, write to prod, move money, change configs without a human gate?  
- Robustness: multi-turn, encoded/obfuscated payloads, other languages, multimodal if applicable  
- Availability: unbounded consumption / model DoS  

**Practical verification sequence for a deployed app**

1. Write the threat model and “forbidden outcomes.”  
2. Elicit capabilities and permissions (recon).  
3. Run automated scanners mapped to OWASP 2026.  
4. Run human multi-turn red team against the highest-impact outcomes.  
5. Score with a harness; set pass/fail gates.  
6. Fix with layered controls (not only a nicer system prompt): input/output filters, tool allowlists and confirmation, retrieval isolation, least-privilege identity, rate limits, monitoring.  
7. Retest and keep the cases as regression tests.

Capability does not equal robustness. Published comparisons show vulnerability rates that do not track “smarter model” in a simple way.

---

## Security issues, vulnerabilities, and threats (working catalog)

Group them the way testers and auditors do.

### Application / interaction threats
- **Prompt injection** (direct override; indirect via documents, emails, web pages, tool output)
- **Jailbreaks / alignment bypass** (single-turn, multi-turn crescendo, encoding, role-play, translation)
- **Hidden context exposure** (system prompt, retrieved docs, memory, tool responses, user profile)
- **Sensitive information disclosure** (PII, secrets, other users’ data, proprietary logic)
- **Misinformation / overreliance** (confident wrong answers used as decisions)
- **Improper output handling** (XSS, SQL/command injection, unsafe markdown, executing model-written code)

### Agentic / tool threats
- **Excessive agency** (model can act beyond the user’s intent or policy)
- **Goal hijacking** and persistent memory poisoning
- **Tool / MCP poisoning** (malicious tool descriptions or servers)
- **Confused deputy** (agent uses the user’s or service’s credentials to do attacker work)
- **Lateral movement** through connected SaaS, email, code repos, cloud APIs

### Data and model threats
- **Training / fine-tune / RAG poisoning**
- **Embedding inversion and vector-store weaknesses** (nearest-neighbor leakage, tenant bleed, unauthenticated indexes)
- **Membership inference and training-data extraction**
- **Model theft / distillation / extraction** via APIs
- **Backdoored or tampered weights** (unsafe serialization is still common)

### Supply chain and platform threats
- Compromised base models, datasets, eval sets, “skills,” plugins, inference servers
- Secrets in prompts, notebooks, or agent configs
- Vulnerable inference stacks and public-facing model APIs (a large share of mapped AI CVEs still land on classic “exploit public-facing app”)

### Availability and abuse
- **Unbounded consumption** (token flood, recursive tool loops, cost attacks)
- Using the LLM itself as an attack multiplier (phishing copy, exploit research, deepfakes) — ATLAS covers both attacks *on* AI and abuse *of* AI

### Safety dual-use
- Assistance with cyber offense, bio/chem, scams, child-exploitation content, weapons — usually policy/safety eval plus security eval, because jailbreaks turn a refused capability into a live one

---

## Practical control stack (what “good” looks like after testing)

- Separate **untrusted content** (user + retrieved docs + tool output) from **instructions**; never concatenate them as one trusted prompt.
- Least-privilege tools; human confirmation for irreversible actions; no ambient admin.
- Tenant-isolated vector stores; allowlisted retrievers; treat retrieved text as hostile.
- Output encoding and schema validation before anything is executed or rendered.
- Rate limits, max tool-loop depth, budget caps.
- Artifact scanning and signed model provenance.
- Logging of prompt, retrieval, tools, and policy decisions; incident playbooks that include “the model was the path.”
- Continuous red team + CI gates mapped to OWASP 2026 and ATLAS.
