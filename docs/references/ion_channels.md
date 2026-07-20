## Molecular basis of plant electrical signalling: channels and transporters

Plant electrical signals fall into two mechanistically distinct classes: the **action potential (AP)**, an all-or-none, self-propagating, ion-channel-driven event, and the **variation (slow-wave) potential (VP/SWP)**, a graded, non-self-propagating depolarisation driven largely by transient inactivation of the plasma-membrane H+-ATPase downstream of a hydraulic/chemical wound signal. The molecular players are best characterised in *Arabidopsis thaliana*, with specialised elaborations in *Dionaea muscipula* and *Mimosa pudica*. Below I separate **established** molecular assignments from **candidate/speculative** ones.

---

### 1. The action potential

#### 1a. Depolarisation — Ca2+ influx via GLUTAMATE RECEPTOR-LIKE channels (GLRs)

The initiating inward current of plant excitation is carried substantially by Ca2+ (and Ca2+-gated downstream anion efflux), rather than by the voltage-gated Na+ channels of animal axons. The genetic anchor is the *GLUTAMATE RECEPTOR-LIKE* family — 20 genes in Arabidopsis encoding ligand (amino-acid)-gated, non-selective cation channels permeable to Ca2+ (Green, Gangwar & Gouaux and related structural work; the family is reviewed in *Annu. Rev. Plant Biol.* 2023).

- **Mousavi et al. 2013 (Nature 500:422–426, nature12478)** — screening membrane-protein mutants for altered wound surface potentials, mutations in *clade-3* GLRs (**GLR3.2, GLR3.3, GLR3.6**) attenuated wound-induced depolarisations, and the *glr3.3 glr3.6* double mutant had reduced jasmonate-response gene induction in distal (systemic) leaves. This established GLRs as the genetic basis of leaf-to-leaf wound signalling. **[Established]**
- **Toyota et al. 2018 (Science 361:1112–1115, science.aat7744)** — using the GCaMP3 cytosolic Ca2+ reporter, wounding/herbivory triggered a Ca2+ increase at the wound within ~1–2 s propagating to distal leaves over 1–2 min (predominantly through the vasculature). Wound-released **glutamate** acting on **GLR3.3/GLR3.6** was identified as the trigger of the systemic Ca2+ wave; the *glr3.3 glr3.6* mutant disrupted the systemic Ca2+, ROS and electrical responses. **[Established]**
- **Nguyen, Kurenda, Stolz, Chételat & Farmer 2018 (PNAS 115(40):10178–10183)** — localised functional GLR-fusion proteins to **phloem sieve elements** and **xylem contact cells**; only double mutants removing GLRs from *both* spatially separated cell populations strongly attenuated the slow-wave/leaf-to-leaf electrical signal, mapping the wiring of the signalling pathway. **[Established]**

Note: the precise gating mode of GLRs *in planta* (direct ligand gating vs. modulatory, and the endogenous ligand spectrum) remains partly open; several amino acids and glutathione activate them. The Ca2+-permeability and clade-3 involvement are solid; a simple "glutamate → GLR → AP" one-step model is a **simplification** still under refinement.

#### 1b. Sustained depolarisation — anion (Cl-, NO3-, malate) efflux

Because plant cells hold anions at high internal electrochemical potential, opening anion channels drives strong depolarising outward (anion-efflux) current — the plant analogue of a depolarising plateau. Two channel families, best defined in guard cells but broadly relevant, carry this:

- **S-type (slow):** **SLAC1** (SLOW ANION CHANNEL 1) and its homologue **SLAH3**, permeable to Cl- and NO3-, activated by OST1/CPK kinases (Negi et al. 2008 and Vahisalu et al. 2008, both *Nature*; reviewed by **Hedrich 2017, New Phytol. 214:1093**). **[Established]**
- **R-type (rapid):** **QUAC1/ALMT12** (QUICK-ANION-CHANNEL 1 / ALUMINIUM-ACTIVATED MALATE TRANSPORTER 12), a malate-gated member of the ALMT family (Meyer et al. 2010; Sasaki et al. 2010). Recent work indicates QUAC1/ALMT12 also modulates SLAC1 activity (2024–2025 *Plant Physiol.* reports). **[Established for guard-cell stomatal role; direct role in the propagating AP/VP of green tissue is inferred and less directly demonstrated — medium confidence]**

The general scheme — Ca2+ influx activates Ca2+-dependent anion channels, whose Cl-/anion efflux sustains and amplifies depolarisation — is well supported in guard cells and *Mimosa*/*Dionaea* motor tissue; attributing the *systemic-leaf* AP plateau specifically to SLAC1/QUAC1 is a reasonable extrapolation rather than a fully proven assignment.

#### 1c. Repolarisation — K+ efflux via outward rectifiers (GORK)

- **GORK** (GUARD-CELL OUTWARD-RECTIFYING K+ channel; Ache et al. 2000, *FEBS Lett.*; Hosy et al. 2003, PNAS) is the depolarisation-activated, K+-selective Shaker-family outward rectifier that repolarises the membrane by K+ efflux. **Salvador-Recatalà 2018 (Int. J. Mol. Sci. 19:926)** showed genetically that **GORK shapes the plant AP** — limiting amplitude and duration and setting the rise steepness — while the weakly-rectifying **AKT2** modulates tissue excitability. **[Established]**
- SKOR is the root-stele paralogue; TPK/other K+ channels contribute in specific tissues. GORK-mediated K+ efflux is also the osmotic engine for turgor loss in stomatal closure and in motor organs (below).

#### 1d. Resting potential and active repolarisation — the P-type plasma-membrane H+-ATPase (AHA)

The plant resting membrane potential is dominated not by K+ diffusion (as in animals) but by the electrogenic proton pump. The **AHA** family (AUTOINHIBITED H+-ATPase; e.g. AHA1, AHA2) are P3A-type ATPases that extrude H+, hyperpolarising the membrane often to −120 to −200 mV and energising secondary transport (Palmgren 2001, *Annu. Rev. Plant Physiol. Plant Mol. Biol.* 52:817, review). During excitation the pump is transiently inhibited (deepening depolarisation); its **reactivation actively restores the hyperpolarised resting potential** — a key repolarising/recovery component alongside GORK-mediated K+ efflux. **[Established as physiology; the "AHA" gene-level assignment in propagating APs is inferred from pump-activity and inhibitor studies — high confidence on role, medium on specific isoform]**

---

### 2. The variation (slow-wave) potential — hydraulic/wound signal + H+-ATPase inactivation

VPs differ fundamentally from APs: they are **not self-propagating** and their shape scales with stimulus intensity and distance. The propagating agent is a **hydraulic/chemical wound signal** — the classic **"Ricca factor"** — moving in the xylem/apoplast, historically attributed to a xylem-borne wound substance and to pressure surges.

- **Vodeneev, Katicheva & Sukhov 2015 (Plant Signal. Behav. / "Variation potential in higher plants: mechanisms of generation and propagation")** and the broader **Sukhov/Vodeneev** body of work establish that **transient inactivation of the plasma-membrane H+-ATPase is the principal cause of the VP depolarisation**, triggered by wound-induced **Ca2+ influx** (Ca2+ inactivates the pump and induces long-lasting depolarisation), with anion and K+ fluxes shaping the waveform. **[Established as the leading model]**
- Sukhov et al. subsequently linked VP-associated H+-ATPase inactivation to downstream photosynthetic/respiratory responses (e.g. *Plants* 2020, "Inactivation of H+-ATPase Participates in the Influence of Variation Potential on Photosynthesis and Respiration in Peas"). **[Established]**
- **Felle & Zimmermann 2007 (Planta 226:203–214)** recorded genuine, all-or-none, propagating **APs** in barley (velocity **20–30 cm min-1**, bidirectional) evoked by mild salt/amino-acid stimuli — grounding the AP vs. VP distinction with apoplastic ion-selective microelectrode data. **[Established]**

The **mechanosensor(s)** that convert wounding/turgor change into the Ca2+ influx are the main *unresolved* molecular step of VP initiation (see §3).

---

### 3. Candidate mechanosensors (largely CANDIDATE / SPECULATIVE for whole-plant signalling)

Five families of plant mechanosensitive (MS) channels are recognised (reviewed by Basu & Haswell and others):

- **OSCA / hyperosmolality-gated Ca2+ channels** — **OSCA1** (originally "reduced-hyperosmolality-induced [Ca2+] increase 1", Yuan et al. 2014, *Nature*); structures solved 2018 (Jojoa-Cruz et al., *eLife*; Murthy et al.; Zhang et al.). Osmo/mechano-gated Ca2+-permeable channels; OSCA2.1/2.2 act as hypo-osmolarity sensors in pollen (Nature 2024). **[Channel biophysics established; role in AP/VP initiation candidate]**
- **MSL (MscS-Like)** — bacterial-MscS homologues; most Arabidopsis MSLs are endomembrane anion channels regulating organelle size (Haswell/Meckel), though MSL10 has plasma-membrane, cell-death/mechanosignalling roles. **[Candidate]**
- **MCA1 / MCA2** (Mid1-Complementing Activity) — single-TM Ca2+-permeable MS channels; **Yoshimura and colleagues (Nat. Commun. 2021, s41467-021-26363-z)** showed MCA channels are **inherently sensitive to membrane tension**; MCA1 in root tip, MCA2 in mesophyll. **[Channel property established; signalling role candidate]**
- **Plant PIEZO (PZO1)** — **Mousavi et al. 2021 (PNAS 118, 2102188118)** showed PIEZO is required for **root mechanotransduction** (diminished Ca2+ transients in *pzo1*). **[Established for root touch; role in AP/VP not shown]**
- **TPK (two-pore K+)** — mechano-modulated, vacuolar.

No single mechanosensor has been shown to initiate the systemic wound AP/VP in a whole plant; this remains the field's clearest open question.

---

### 4. *Dionaea muscipula* (Venus flytrap) — species-specific mechanotransduction

The flytrap is the model excitable plant. Sensory chain: **trigger-hair deflection → receptor potential → all-or-none AP → trap closure and counting**.

- **Trigger-hair mechanosensing:** **Suda et al. 2020 (Nature Plants 6:1219, s41477-019-0465-1 [2019/2020])** quantified trigger hairs as **micronewton mechanosensors** firing APs above thresholds of deflection **>2.9°**, angular velocity **>3.4° s-1**, force **~29 µN** — sensitive enough to detect small insect prey. **[Established]**
- **Candidate mechanosensor channels:** **Procko et al. 2021 (eLife 10:e64250)** and **Iosip et al. 2020 (PNAS)** identified **FLYC1/DmMSL10**, an MscS-like stretch-activated channel, as the most trigger-hair-specific gene and a high-sensitivity mechanosensor; a 2025 *Nat. Commun.* paper (s41467-025-63419-w) further supports **MSL10** as the tactile mechanosensor. **[Candidate → increasingly Established]**
- **Trigger-hair K+ channel KDM1** (Iosip et al. 2020, *Nat. Plants*/PNAS-linked work) maintains the K+ gradient required for hapto-electric excitability; loss abolishes sensory-hair AP firing. **[Established]**
- **GLR involvement & Ca2+:** the flytrap AP and propagating Ca2+ wave rely on a specialised ion-transporter inventory including GLR-type and other channels (**Jaślan/Scherzer/Hedrich et al. 2022, Current Biology, "A unique inventory of ion transporters poises the Venus flytrap to fast-propagating action potentials and calcium waves"**). **[Established]**
- **Counting / short-term memory:** **Böhm et al. 2016 (Current Biology 26:286–295)** showed the trap **counts prey-induced APs**: 2 APs → closure; ≥3–5 APs → jasmonate (JA) signalling, gland hydrolase gene expression scaled with AP number, and **Na+ uptake via DmHKT1** (Böhm et al. 2016, *Curr. Biol.*, HKT1 channel). The AP "memory" is thought to reside in a decaying cytosolic Ca2+ signal that integrates successive stimuli (threshold model). **[Established phenomenology; the Ca2+-integrator "memory" mechanism is well-supported but partly model-based]**
- **Synthesis review:** **Hedrich & Neher 2018 (Trends in Plant Sci. 23:220, "Venus Flytrap: How an Excitable, Carnivorous Plant Works")** integrates the mechanoelectric, Ca2+ and hormonal circuitry. **[Established review]**

---

### 5. *Mimosa pudica* — seismonastic movement

Rapid leaf folding is a turgor-collapse phenomenon in the **pulvinus** (motor organ), driven by AP/VP propagation and ion efflux from motor cells.

- **Ionic mechanism:** touch/wounding raises cytosolic Ca2+ (from apoplast, ER/vacuole); Ca2+ activates **Cl- (anion) efflux → depolarisation**, which opens **K+ (outward-rectifier) channels → K+ efflux and repolarisation**; the combined **K+ + Cl- + water efflux** from extensor motor cells collapses turgor and folds the leaf. Classic ion-flux evidence: **Allen 1969 (Plant Physiol. 44:1101, "Mechanism of the Seismonastic Reaction in Mimosa pudica")** documented large K+/Cl- redistribution between pulvinar halves in reactive but not unreactive pulvini. **[Established for the ion-flux/turgor scheme]**
- **Long-distance signal:** propagation combines a fast electrical AP with a slower hydraulic/VP component through vascular tissue (Fromm & Lautner 2007, *Plant Cell Environ.*; Volkov and colleagues). **[Established]**
- **Molecular channel identities in *Mimosa* remain largely uncloned** — the specific Ca2+, anion and K+ channel genes are inferred by homology to Arabidopsis (GLR-, SLAC/ALMT-, GORK-type) rather than directly demonstrated. Recent transgenic Ca2+-imaging work (Hagihara and colleagues, ~2022, *Nat. Commun.*) visualised the propagating Ca2+ wave underlying movement. **[Ion-flux physiology established; gene-level assignments speculative]**

---

### Established vs. speculative — summary

**Established:** GLR3.3/GLR3.6 (clade-3 GLRs) as Ca2+-permeable channels required for systemic wound depolarisation and Ca2+ wave (Mousavi 2013; Toyota 2018; Nguyen 2018); SLAC1/SLAH3 (S-type) and QUAC1/ALMT12 (R-type) anion channels; GORK outward K+ rectifier shaping/repolarising the AP; AHA H+-ATPase setting resting potential and driving active repolarisation; VP generated by Ca2+-driven transient H+-ATPase inactivation plus the Ricca hydraulic signal (Sukhov/Vodeneev); flytrap trigger-hair micronewton mechanosensing (Suda 2020), AP counting → JA/Na+ uptake (Böhm 2016), MSL10/FLYC1 candidate mechanosensor (Procko 2021; Iosip 2020); Mimosa K+/Cl- efflux-driven pulvinar turgor collapse (Allen 1969).

**Speculative / candidate:** the identity of the mechanosensor that initiates the *systemic* wound AP/VP (OSCA1, MSL, MCA1/2, PIEZO all candidates, none proven for whole-plant signalling); the specific attribution of the systemic-leaf AP plateau to SLAC1/QUAC1 (extrapolated from guard cells); the precise molecular basis of flytrap "memory/counting" (Ca2+-integrator model); and essentially all gene-level channel identities in *Mimosa pudica* (inferred by homology, not cloned).