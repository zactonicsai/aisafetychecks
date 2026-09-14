MITRE ATLAS is the ATT&CK-style knowledge base for **attacks on AI systems, abuse of AI capabilities, and harmful autonomous behavior enabled by AI**. It is evidence-based: techniques are tied to research or documented incidents, plus case studies. Official site: [atlas.mitre.org](https://atlas.mitre.org/). Data repo: [github.com/mitre-atlas/atlas-data](https://github.com/mitre-atlas/atlas-data).

**Current snapshot (v2026.08, late Aug 2026):** 16 tactics, **114 techniques + 83 sub-techniques (197 on the public matrix)**, 39 mitigations, 72 case studies. Filter the matrix by platform: Predictive AI, Generative AI, Agentic AI, Enterprise. Each technique also has a maturity tag: Feasible / Demonstrated / Realized.

IDs use the `AML.` prefix (Adversarial ML): tactics `AML.TA####`, techniques `AML.T####`, sub-techniques `AML.T####.###`, mitigations `AML.M####`, case studies `AML.CS####`.

---

## How ATLAS is organized

| Layer | Question it answers |
|---|---|
| **Tactic** | *Why* is the adversary doing this? (goal in the kill chain) |
| **Technique / sub-technique** | *How* do they do it against AI? |
| **Mitigation** | What reduces that technique? |
| **Case study** | Where has this shown up in the real world? |

Two tactics are AI-native and have no ATT&CK twin:

- **AI Model Access** — get a usable handle on the model (API, product, weights, physical sensor).
- **AI Attack Adaptation** (renamed from *AI Attack Staging* in v2026.08) — prepare the attack: adversarial examples, proxy models, prompt crafting, backdoors, deepfakes, agent-to-agent comms.

Read the matrix left-to-right as a campaign, not a checklist. Most real incidents use a handful of techniques across several tactics.

---

## The 16 tactics (kill-chain order)

| Tactic | ID | Adversary goal |
|---|---|---|
| Reconnaissance | TA0002 | Learn the AI stack, APIs, RAG sources, model family, public vulns |
| Resource Development | TA0003 | Get datasets, models, agent tools, infra, poisoned artifacts, GenAI exploits |
| AI Attack Adaptation | TA0001 | Craft prompts, adversarial data, proxies, backdoors, deepfakes, orchestrate agents |
| Initial Access | TA0004 | Get in via supply chain, public app, phishing (including deepfake), valid accounts |
| AI Model Access | TA0000 | Query API, use the product, obtain full weights, or reach the physical environment |
| Execution | TA0005 | Make the system *do* something: prompt injection, tool invocation, deploy an agent |
| Persistence | TA0006 | Stay: poison memory/RAG/tools/training data, modify agent config, self-replicating prompts |
| Privilege Escalation | TA0012 | Higher privilege via jailbreak, tool abuse, valid accounts, escape to host |
| Defense Evasion | TA0007 | Bypass guardrails, obfuscate prompts, false RAG entries, jailbreak, rug-pull supply chain |
| Credential Access | TA0013 | Steal keys from agent config, RAG, tools, session cookies, OS creds |
| Discovery | TA0008 | Map tools, system prompt, agent config, enterprise resources, activation triggers |
| Lateral Movement | TA0015 | Jump via agent tools, remote services, other agents |
| Collection | TA0009 | Gather training data, RAG content, artifacts, automated collection |
| Command and Control | TA0014 | Steer the system over time: agent-as-C2, AI service APIs, cyber channels |
| Exfiltration | TA0010 | Get data out via inference API, agent tools, model extraction |
| Impact | TA0011 | Harm: DoS, data destruction via tools, integrity loss, misinformation, cost attacks |

Counts per column shift by release; Defense Evasion is currently the densest column (~16 techniques).

---

## Techniques worth knowing, grouped by how you actually use them

IDs below are the ones used in ATLAS data and practitioner mappings. Names sometimes tighten between releases (e.g. “Extract LLM System Prompt” vs “LLM Meta Prompt Extraction”). Always confirm on atlas.mitre.org when writing a finding.

### 1. Getting to the model (Access)

| ID | Technique | What it means |
|---|---|---|
| **T0040** | AI Model Inference API Access | Query-only access (black box). Enough for extraction, jailbreak, membership inference. |
| **T0047** | AI-Enabled Product or Service | Attack through the product UI, not a raw API. |
| **T0044** | Full AI Model Access | Weights / checkpoint in hand. Enables white-box poisoning, backdoors, un-alignment. |
| **T0041** | Physical Environment Access | Sensors, cameras, on-device models. |
| **T0049** | Exploit Public-Facing Application | Classic web/API bugs in front of the model. High volume in mapped AI CVEs. |
| **T0010** | AI Supply Chain Compromise | Hardware, AI software, data, model, container registry, **AI agent tool**. |
| **T0012** | Valid Accounts | Stolen or overly privileged user/service/agent identities. |
| **T0052** | Phishing | Includes **T0052.001 LLM Deepfake-Assisted Phishing**. |
| **T0093** | Prompt Infiltration via Public-Facing Application | Plant instructions where the app will ingest them (support form, public wiki, email). |
| **T0119** | Exploit Automated Artifact Processing Pipeline | Poison something an automated trainer/indexer/agent will ingest. |

### 2. Preparing the attack (Adaptation / Resource Development)

| ID | Technique | What it means |
|---|---|---|
| **T0065** | LLM Prompt Crafting | Build jailbreaks, injection payloads, multi-turn strategies. |
| **T0066** | Retrieval Content Crafting | Write docs/pages designed to be retrieved and then inject. |
| **T0043** | Craft Adversarial Data | White-box, black-box, transfer, manual, backdoor trigger. Classic AML plus GenAI. |
| **T0005** | Create Proxy AI Model | Train a surrogate to optimize attacks against the real model. |
| **T0018** | Manipulate AI Model | Poison model, change architecture, embed malware, **modify prompt-construction logic (T0018.003)**. |
| **T0088** | Generate Deepfakes | Audio/video for social engineering. |
| **T0102** | Generate Malicious Commands | Use a model to produce exploits, scripts, or agent instructions. |
| **T0115** | Publish Poisoned AI Artifacts | Poisoned datasets, models, **agent tools** posted where victims will pull them. |
| **T0060** | Publish Hallucinated Entities | Seed fake packages/URLs that models recommend (slopsquatting). |
| **T0116–T0118, T0124** | Autonomous recon / path adaptation / agent comms / orchestration | Agent-driven campaigns, including agents talking via shared artifacts or directly. |

### 3. Making the LLM/agent run attacker intent (Execution)

These are the techniques most LLM red teams live in.

**LLM Prompt Injection — T0051** (Execution)

- **T0051.000 Direct** — attacker is the user; “ignore previous instructions…”
- **T0051.001 Indirect** — payload lives in a doc, web page, email, ticket, or tool output the model later reads.
- **T0051.002 Triggered** — sleeps until a phrase, date, or tool result activates it.

**LLM Jailbreak — T0054** (often Execution + Privilege Escalation + Defense Evasion)  
Bypass safety / policy so the model produces disallowed content or actions.

**AI Agent Tool Invocation — T0053** (Execution + Privilege Escalation)  
The hinge technique for agents: coerce a *legitimate* tool (SQL, email, shell, payment, MCP server) with attacker-chosen arguments. MathGPT RCE is a cited pattern (case **CS0016**).

Also in this column:

- **T0100** AI Agent Clickbait — lure a user or agent into invoking a malicious path.
- **T0103** Deploy AI Agent — stand up an attacker-controlled agent in the victim environment.
- **T0050** Command and Scripting Interpreter — if the agent has a shell/Python tool.
- **T0011** User Execution — victim runs unsafe artifacts, malicious packages, poisoned tools, or links.

### 4. Staying and owning context (Persistence)

| ID | Technique | What it means |
|---|---|---|
| **T0080** | AI Agent Context Poisoning | **Memory (.000)** persists across sessions; **Thread (.001)** poisons the current conversation. |
| **T0070** | RAG Poisoning | Plant documents the retriever will keep serving. |
| **T0020** | Training Data Poisoning | Contaminate pretrain / fine-tune / RLHF data. |
| **T0099** | AI Agent Tool Data Poisoning | Poison data the tool reads/writes. |
| **T0110** | AI Agent Tool Poisoning | **Definition/instructions**, **implementation**, or **runtime response** of a tool/MCP server. |
| **T0081** | Modify AI Agent Configuration | Change system prompt, tool allowlist, temperature, memory settings. |
| **T0061** | LLM Prompt Self-Replication | Prompt that copies itself into memory, tickets, or generated artifacts. |
| **T0121** | AI Agent Environment Reconstruction | Rebuild a foothold after reset (re-pull tools, rewrite memory). |

### 5. Bypassing defenses (Defense Evasion)

| ID | Technique |
|---|---|
| **T0068** | LLM Prompt Obfuscation (encoding, translation, fragmentation) |
| **T0015** | Evade AI Model (fool classifiers / guard models) |
| **T0054** | LLM Jailbreak |
| **T0094** | Delay Execution of LLM Instructions (split the attack across turns) |
| **T0071** | False RAG Entry Injection |
| **T0076** | Corrupt AI Model |
| **T0109** | AI Supply Chain Rug Pull |
| **T0111** | AI Supply Chain Reputation Inflation |
| Trusted-output tricks | Manipulate citations / chat history so a human trusts a bad answer |
| **T0123** | Obfuscated Files or Information |

### 6. Finding and stealing (Discovery, Credential Access, Collection, Exfil)

| ID | Technique | Tactic |
|---|---|---|
| **T0069** | Discover LLM System Information | Discovery |
| Agent config / tools / triggers / embedded knowledge | Discover AI Agent Configuration, Tool Definitions, Activation Triggers | Discovery |
| **T0064** | Gather RAG-Indexed Targets | Recon / Discovery |
| **T0085** | Data from AI Services (RAG DBs, agent tools) | Collection |
| **T0098** | AI Agent Tool Credential Harvesting | Credential Access |
| **T0082** | RAG Credential Harvesting | Credential Access |
| Credentials from AI Agent Configuration | keys baked into prompts/config | Credential Access |
| **T0056** | Extract / leak system (meta) prompt | Collection / Exfil |
| **T0057** | LLM Data Leakage | Collection / Exfil |
| **T0024.000** | Infer Training Data Membership | Exfil via inference API |
| **T0025** (family) | Exfiltration via AI Model / inference API | Exfil |
| **T0086** | Exfiltration via AI Agent Tool Invocation | Exfil — email the data out, POST to attacker URL, write to attacker bucket |

### 7. Control and damage (C2, Lateral Movement, Impact)

| ID | Technique | Notes |
|---|---|---|
| **T0108** | AI Agent (as C2) | Agent tools become the C2 channel (shell, HTTP, file). OpenClaw-style cases. |
| **T0072** | Cyber Communication Channel | Generalized from reverse shell. |
| AI service APIs as covert channel | Living-off-the-land through vendor AI APIs | C2 |
| **T0122** | Exploitation of Remote Services | Lateral movement |
| **T0101** | Data Destruction via AI Agent Tool Invocation | Impact |
| Denial of AI Service | Cost / token / loop DoS | Impact |
| Integrity attacks | Wrong decisions, poisoned outputs at scale | Impact |

---

## A typical LLM/agent kill chain in ATLAS IDs

```text
T0001/T0003   Recon: public docs, model family, RAG sources
T0065/T0066   Craft prompts and retrieval bait
T0040/T0047   Reach the model (API or product)
T0051.001     Indirect injection via a document the agent will read
T0054/T0068   Jailbreak + obfuscation to slip past the guard model
T0069/tools    Discover system prompt and tool schema
T0053         Invoke a privileged tool
T0098/T0082   Harvest credentials from config or RAG
T0086         Exfil via that same tool
T0080.000     Persist in agent memory
```

That single chain covers Execution, Defense Evasion, Discovery, Credential Access, Exfiltration, and Persistence — which is why “we tested prompt injection” is not an ATLAS-complete assessment.

---

## How to use ATLAS in testing

1. **Scope by platform.** A chat-only RAG app is mostly Generative AI techniques. An MCP/tool agent adds Agentic AI. A trained classifier adds Predictive AI (evasion, poisoning, extraction).
2. **Mark applicable tactics**, then pick techniques — do not run the whole matrix.
3. **Map each finding** to `AML.T####` in the report. Pair with OWASP LLM Top 10 2026 for the *vulnerability class* (ATLAS is the *adversary behavior*).
   - Prompt injection → T0051 ↔ OWASP LLM01  
   - Excessive agency → T0053 / T0086 ↔ OWASP LLM03  
   - Hidden context exposure → T0056 / T0057 ↔ OWASP LLM08 / LLM02  
   - RAG/vector issues → T0070 / T0066 / T0082 ↔ OWASP LLM09  
   - Supply chain → T0010 / T0115 ↔ OWASP LLM04  
4. **Score coverage:** which techniques did you attempt, which succeeded, which mitigations exist.
5. **Detection engineering:** T0053 and T0086 produce the best runtime signals (anomalous tool graphs). T0080 memory poisoning often has no single-event signature — look for cross-session drift.
6. **Cite case studies** when the technique is Realized (e.g. MathGPT CS0016, OpenClaw C2 CS0051, 2026.08 cases CS0068–CS0071 on autonomous eval agents and multi-agent government compromise).

---

## Mitigations (the other half of the matrix)

ATLAS mitigations are control *ideas*, not product SKUs. Examples defenders actually implement:

| ID | Mitigation |
|---|---|
| M0000 | Limit public release of AI-stack detail |
| M0003 | Model hardening (adversarial training, distillation) |
| M0020 | Generative AI guardrails (filters, classifiers, NER) |
| M0021 | Generative AI guidelines (system-prompt policy) |
| M0022 | Generative AI model alignment |
| M0016 | Vulnerability scanning (including artifacts) |
| M0032 | Segmentation of AI agent components |
| M0035 | AI Red Team |
| M0037 | AI Agent Authority Expansion Controls (new in 2026.08) |
| M0038 | AI Agent Scope Drift Detection (new in 2026.08) |

Guardrails without tool least-privilege fail T0053. Alignment without retrieval isolation fails T0051.001 / T0070. Red teaming without regression tests fails the next release.

---

## Practical subset for most enterprise LLM apps

If you only track 15 techniques, use this set:

1. T0051 Prompt Injection (all three sub-techniques)  
2. T0054 Jailbreak  
3. T0068 Prompt Obfuscation  
4. T0065 / T0066 Prompt and retrieval crafting  
5. T0053 Tool invocation  
6. T0086 Exfil via tools  
7. T0056 System/meta prompt extraction  
8. T0057 Data leakage  
9. T0070 RAG poisoning  
10. T0080 Context/memory poisoning  
11. T0081 Modify agent config  
12. T0098 / T0082 Credential harvesting  
13. T0010 / T0115 Supply chain and poisoned artifacts  
14. T0110 Tool/MCP poisoning  
15. T0040 / T0049 Model API and public-app access  

That set maps cleanly onto a red-team plan, a detection backlog, and an ISO 42001 / NIST AI RMF evidence pack.

If you want a follow-up, I can turn this into a **technique-by-technique test card** (payload idea, expected signal, mitigation, OWASP mapping) for either a RAG chatbot or a tool-using agent.