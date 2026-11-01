# Judge Demonstration Storyboard & Video Script (2-3 Minutes)
**Project:** InnerOS Autonomous Infrastructure Guardian  
**Hackathon:** Meta Global AI Developer Hackathon 2026 (Startup Track / Push the Frontier)  
**Presenter:** Rafael López, CEO & Founder, InnerChispa LLC  

---

## Storyboard & Video Narrative (180 Seconds)

### [0:00 - 0:25] ACT I: The Real-World Physical Infrastructure Problem
- **Visual:** Real physical server rack in Guayaquil, Ecuador. Flashing switch lights, UPS battery telemetry, fiber distribution trays.
- **Narrative (Voiceover):**  
  *"Most AI agents today answer questions in chat windows. But the physical world doesn't live in chat windows. In critical facilities, network centers, and edge infrastructure, when a link drops or temperature spikes, engineers don't need another hallucinating chatbot. They need an autonomic guardian that observes real signals, remembers past incidents, reasons carefully, requests human permission, and proves what happened."*

---

### [0:25 - 0:55] ACT II: Live Observation & Memory Recall
- **Visual:** Switch to InnerOS Guardian Web Console. Operator clicks **"📡 Casa Network (13 signals)"**.
- **Action:**  
  1. The UI instantly ingests live readings from `https://guardian.creatorcore.ai/api/guardian/live/readings/casa/network`.
  2. The SHA-256 snapshot digest `d4c9...` is anchored.
  3. Operator clicks **"Recall Facts"**.
  4. The **AG-60 Verified Memory** box illuminates with verified topology facts (dual-node core, APC Smart-UPS battery buffering, past incident baseline).
- **Narrative:**  
  *"Here is InnerOS in action. We don't simulate telemetry—we ingest live telemetry from our production network in Ecuador, with 13 live signals and an exact SHA-256 snapshot digest. Notice stage two: InnerOS recalls verified memory from our AG-60 knowledge store, providing historical context without exposing private credentials."*

---

### [0:55 - 1:30] ACT III: Meta Muse Spark 1.3 Governed Reasoning
- **Visual:** Operator clicks **"Mint One-Shot Grant"**, then **"Reason with Muse Spark 1.3"**.
- **Action:**  
  1. Single-use grant token `grant_a8f9...` is generated, bound to the snapshot hash.
  2. The operator runs Muse Spark reasoning.
  3. A tamper-evident Meta receipt appears, displaying:
     - Model: `muse-spark-1.3`
     - Status: `REAL` (or `GOVERNED_ONE_SHOT_RECEIPT`)
     - Structured breakdown: Observations, Hypotheses, Uncertainty, and Recommended Governed Action.
- **Narrative:**  
  *"Now we bring in Meta's frontier model: Muse Spark 1.3. Notice our safety boundary: the model cannot be triggered by arbitrary web crawlers. It requires an atomic single-use cryptographic grant bound to the snapshot digest. Muse Spark analyzes the live signals and historical memory, explicitly distinguishing what is proven from uncertainty, and suggests a safe notification action."*

---

### [1:30 - 2:05] ACT IV: Human Authority, Virtual Actuation & VoiceOps Proof
- **Visual:** The lifecycle advances to **APPROVE**, **ACT**, and **VERIFY**.
- **Action:**  
  1. Rafael López (Owner) clicks **"Approve Safe Action"**.
  2. Operator clicks **"Execute Virtual Action"**. Virtual actuator engages with state isolation.
  3. Operator clicks **"Verify Readback"**.
  4. The **VoiceOps Telephone Verification** card highlights:
     - SIP 200 OK signaling.
     - 3,853 outbound and 9,389 inbound RTP packets.
     - 7 accepted speech turns using local Whisper STT and Piper TTS.
- **Narrative:**  
  *"The AI can recommend, but only the owner can authorize. Once approved, the action executes in an isolated virtual actuator, followed by an independent readback. We also link the verified VoiceOps telephone confirmation receipt—proven by over 13,000 RTP packets and 7 conversation turns."*

---

### [2:05 - 2:35] ACT V: Secondary Vision Demo with Meta SAM 3.1
- **Visual:** Scroll to the **SAM 3.1 Visual Inspection** panel.
- **Action:**  
  1. Operator selects `Lab Core Switch LED & Cabling`.
  2. Clicks **"Run SAM 3.1 Inspection"**.
  3. Bounding boxes and confidence scores appear for switch chassis (98%), SFP optical uplink (94%), and patch cord bend radius compliance (96%).
- **Narrative:**  
  *"As a secondary physical AI capability, we integrated Meta SAM 3.1 to inspect laboratory hardware visually. SAM detects optical transceivers and verifies that fiber patch cords comply with physical bend radiuses—strictly using laboratory equipment with zero client PII."*

---

### [2:35 - 3:00] ACT VI: Forensic Evidence & Conclusion
- **Visual:** Operator clicks **"Export Verified JSON Evidence"**. The audit table shows the valid SHA-256 hash chain.
- **Narrative:**  
  *"Finally, stage seven: PROVE. Every observation, memory fact, Meta receipt, approval, and readback is cryptographically linked in a tamper-evident SHA-256 audit chain that can be exported for forensic verification. InnerOS is the physical AI control plane that remembers and responds. Built for Meta Hackathon 2026. Thank you."*
