## Simulating and discriminating plant electrical signals from a two-channel extracellular pair

This lens gives you (1) the passive cable propagator in closed form, (2) the active excitable models (FitzHugh–Nagumo and Hodgkin–Huxley-type plant AP models) with plant-realistic parameters, and (3) a decisive near/far waveform test that separates passive electrotonic spread from an actively regenerated travelling wave. Throughout, "near" = proximal channel, "far" = distal channel, separation `d`.

---

### 1. Passive cable theory (the null model)

**1.1 The 1D cable equation.** For a thin, uniform, cylindrical conductor (sieve tube, symplastic strand, or a giant characean internode) with membrane, the transmembrane potential `V(x,t)` obeys

$$\tau\,\frac{\partial V}{\partial t} \;=\; \lambda^2\,\frac{\partial^2 V}{\partial x^2}\;-\;V ,$$

with the two intrinsic constants

$$\lambda=\sqrt{\tfrac{r_m}{r_i}}\quad(\text{space constant, cm}),\qquad \tau = r_m c_m = R_m C_m\quad(\text{time constant, s}).$$

Here `r_m` (Ω·cm) is membrane resistance times unit length, `r_i` (Ω/cm) axial resistance per unit length, `c_m` (F/cm) membrane capacitance per unit length; equivalently `R_m` (Ω·cm²) and `C_m` (F/cm²) are the specific quantities. This is the classical Hodgkin–Rushton/Rall linear cable (Hodgkin & Rushton 1946, *Proc. R. Soc. B* 133:444–479; Rall in Koch & Segev, *Methods in Neuronal Modeling*; Keener & Sneyd, *Mathematical Physiology*). It is a linear, dissipative diffusion equation with a leak — **no regeneration, no threshold, no constant-velocity wave**. That property is exactly what makes it the correct null hypothesis against "active." *(VERIFIED — c1)*

Define the effective electrotonic diffusivity

$$D_{\text{cab}}=\frac{\lambda^2}{\tau}=\frac{r_m/r_i}{r_m c_m}=\frac{1}{r_i c_m}\quad(\text{cm}^2/\text{s}).$$

**1.2 Green function (impulse response).** For an instantaneous unit charge injected at `x=0, t=0` on an infinite cable, the substitution `V=e^{-t/\tau}W` reduces the cable equation to the heat equation `W_t=D_{\text{cab}}W_{xx}`, giving

$$G(x,t)=\underbrace{e^{-t/\tau}}_{\text{leak}}\;\underbrace{\frac{1}{\sqrt{4\pi D_{\text{cab}}\,t}}\exp\!\Big(-\frac{x^2}{4 D_{\text{cab}}\,t}\Big)}_{\text{diffusive spread}},\qquad t>0 .$$

Three signatures fall out immediately: the peak **amplitude falls** with `x`, the peak **time is delayed** and broadened (dispersion), and the response is **causal but not a sharp front** — the "arrival" smears. *(VERIFIED — c2)*

**1.3 The point-to-point propagator (the object you actually fit).** The decisive quantity for a near/far pair is the transfer function relating an *imposed* proximal waveform `V_{\text{near}}(t)=V(0,t)` to the distal waveform `V_{\text{far}}(t)=V(d,t)`. In Laplace domain the bounded solution of the cable equation is

$$\widehat V(x,s)=\widehat V(0,s)\,\exp\!\Big[-\frac{x}{\lambda}\sqrt{1+s\tau}\Big]\;\;\Rightarrow\;\; H_d(s)=\exp\!\Big[-\frac{d}{\lambda}\sqrt{1+s\tau}\Big].$$

This single expression encodes all three passive fingerprints:

- **DC amplitude decrement:** `H_d(0)=e^{-d/\lambda}` — pure exponential attenuation with distance.
- **Delay + low-pass:** the `\sqrt{1+s\tau}` term is a distributed-RC dispersive delay; high frequencies are attenuated more (the far waveform is a *smoothed, delayed, shrunken* copy of the near one).

The inverse transform is closed-form (an inverse-Gaussian / Lévy-type first-passage kernel):

$$\boxed{\,h_d(t)=\frac{d/\lambda\,\sqrt{\tau}}{2\sqrt{\pi}}\;t^{-3/2}\,\exp\!\Big(-\frac{t}{\tau}-\frac{(d/\lambda)^2\,\tau}{4t}\Big),\qquad t>0\,}$$

with `\int_0^\infty h_d(t)\,dt = e^{-d/\lambda}` (consistent with the DC gain). So the **passive prediction is**

$$V_{\text{far}}(t)=(V_{\text{near}}\ast h_d)(t),$$

a two-parameter kernel governed by the electrotonic distance `\mu\equiv d/\lambda` and the time constant `\tau`. *(VERIFIED analytically as the inverse Laplace of `exp[-k\sqrt{s+b}]` with `k=(d/\lambda)\sqrt\tau`, `b=1/\tau` — c3.)* Practically, latency grows and the pulse broadens with `\mu`, and the peak shrinks as `\approx e^{-\mu}`. That coupling of *delay to broadening and to attenuation* is the passive tell. *(NOTE: the original draft's explicit `t_{\text{peak}}` formula was garbled/incomplete — `\tau(\sqrt{9/4+\mu^2/\ldots}-3/2)` — and has been removed rather than reproduced with an unverified closed form.)*

**1.4 Discretised propagator.** For numerics, use compartments of length `\Delta x` (each an RC node coupled by axial resistors). Semi-implicit Crank–Nicolson on

$$C_m\frac{dV_i}{dt}=\frac{1}{r_i\Delta x^2}\big(V_{i+1}-2V_i+V_{i-1}\big)-\frac{V_i}{R_m}$$

is unconditionally stable; the tridiagonal solve is `O(N)` (Thomas algorithm). Equivalently, discretise `H_d(s)` directly: fit the far channel as an FIR/IIR filter of the near channel (Section 3). Stability of an *explicit* scheme requires `D_{\text{cab}}\,\Delta t/\Delta x^2\le \tfrac12`.

---

### 2. Active excitable models (the alternative)

**2.1 FitzHugh–Nagumo (FHN) reaction–diffusion in 1D.** The minimal excitable-medium caricature (FitzHugh 1961, *Biophys. J.*; Nagumo, Arimoto & Yoshizawa 1962, *Proc. IRE*) is

$$\frac{\partial u}{\partial t}=D\,\frac{\partial^2 u}{\partial x^2}+u-\frac{u^3}{3}-w+I,\qquad \frac{\partial w}{\partial t}=\varepsilon\,(u-a-bw),$$

with `u` a fast voltage-like activator (diffusively coupled, `D` = electrotonic diffusivity `\sim\lambda^2/\tau`), `w` a slow recovery variable, and `\varepsilon\ll1` the timescale separation. For plant signals the natural mapping is: `u`↔membrane depolarisation, `w`↔slow Ca²⁺/Cl⁻ recovery + H⁺-ATPase reactivation, and `\varepsilon^{-1}` set to **seconds**, not milliseconds. *(VERIFIED — c5.)*

**Emergence of a constant-amplitude, constant-velocity wave.** In an excitable medium a supra-threshold local depolarisation ignites its neighbour by diffusion, which regenerates full amplitude, and so on — a self-sustaining travelling pulse `u(x,t)=U(\xi)`, `\xi=x-ct`, that translates without change of shape. Amplitude is set by the reaction kinetics (the fixed points of `u-u^3/3`), **not** by distance — the defining contrast with the passive kernel, whose amplitude decays as `e^{-d/\lambda}`. *(VERIFIED — c7.)*

**Velocity scaling.** For the underlying bistable Nagumo front with cubic reaction `f(u)=u(u-a)(1-u)` the front speed is exactly

$$c=\sqrt{\tfrac{D}{2}}\,(1-2a),$$

so **`c\propto\sqrt{D}`** and increases with excitability (smaller threshold `a`) (Murray, *Mathematical Biology*; the `c_0=1/\sqrt2-a\sqrt2` result at `D=1` follows directly). For the FHN *pulse* the same `c\propto\sqrt{D}` scaling holds to leading order, with a prefactor set by `a` and a weak `\varepsilon` dependence; there is a fast (stable) and a slow (unstable) branch. Practical consequences for plants: a two- to four-fold change in axial coupling changes velocity only ~1.4–2×, and velocity is *independent of stimulus strength* above threshold — both testable. *(VERIFIED — c6.)*

**2.2 Hodgkin–Huxley-type plant AP models.** Plant APs are **not** Na⁺-based. The consensus ionic mechanism (Fromm & Lautner 2007; Vodeneev, Katicheva & Sukhov 2016, *Biophysics* 61:505–512) is: a triggering Ca²⁺ influx (often Ca²⁺-induced, IP₃/second-messenger gated) raises cytosolic Ca²⁺, which activates **Cl⁻ channels**; because `E_{Cl}` is depolarised relative to rest, Cl⁻ efflux drives the **depolarising phase**; repolarisation is carried by **K⁺ efflux** plus reactivation of the electrogenic **H⁺-ATPase**. *(VERIFIED — c8.)*

The Sukhov–Vodeneev family of HH-type models makes this quantitative:

- **Sukhov & Vodeneev (2009), *J. Membr. Biol.* 232:59–67** — a plasmalemma model with voltage/Ca²⁺-gated **Ca²⁺, Cl⁻ and K⁺ channels**, plus **H⁺-ATPase and Ca²⁺-ATPase**, **2H⁺/Cl⁻ symporter** and **H⁺/K⁺ antiporter**, tracking ion concentrations, apoplast/cytoplasm buffering and temperature dependence of the pumps. *(VERIFIED — c9.)*
- **Sukhov, Nerush, Orlova & Vodeneev (2011), "Simulation of action potential propagation in plants," *J. Theor. Biol.* 291:47–55** — couples the generation model across a lattice of electrically-coupled excitable cells to produce a **propagating** AP with plant-scale velocity (cm/s order). *(VERIFIED — c10.)*
- **Sukhov, Akinchits, Katicheva & Vodeneev (2013), "Simulation of Variation Potential in Higher Plant Cells," *J. Membr. Biol.* 246:287–296** — VP model. *(CORRECTED: the draft mis-cited this as "Vodeneev, Akinchits & Sukhov 2013"; the lead author is Sukhov, V. and Katicheva was omitted.)*
- **Novikova, Vodeneev & Sukhov (2017), *Biochem. (Moscow) Suppl. Ser. A* 11:151–167** — extends the AP model to include the **vacuole/tonoplast** (tonoplast Ca²⁺, Cl⁻, K⁺ channels; H⁺- and Ca²⁺-ATPases; H⁺/K⁺, 2H⁺/Cl⁻, 3H⁺/Ca²⁺ antiporters) with Ca²⁺/IP₃ regulation. *(VERIFIED — c11.)*
- **Sukhova, Akinchits & Sukhov (2017), "Mathematical Models of Electrical Activity in Plants," *J. Membr. Biol.* 250:407–423** — review tying the above together. *(CORRECTED: the draft mis-cited this as "Sukhov, Sukhova & Vodeneev 2017/2019." The correct authors are Sukhova E, Akinchits E, Sukhov V — Vodeneev is not an author, Akinchits is, and Sukhova (not Sukhov) is lead. It is a single 2017 paper; there is no 2019 version. Journal, volume 250, pages, and year are otherwise correct — c12.)*

Each channel obeys HH form `I_j=g_j\,m^p h^q (V-E_j)` with gating ODEs `\dot m=(m_\infty-m)/\tau_m`, summed into `C_m\dot V=-\sum_j I_j+ (\text{axial coupling})`. **Plant-realistic timescales/values:** `C_m\approx1\ \mu\text{F/cm}^2` (universal `\sim0.7$–$1`); AP **duration seconds to tens of seconds** (vs ms in animals) because Ca²⁺/Cl⁻ gating and pump kinetics are slow; refractory period **seconds to minutes**; conduction velocity **0.5–20 cm/s** for APs (Fromm & Lautner 2007), with faster values in specialised motor tissue (e.g. *Mimosa* pulvinus) and characean internodes typically a few cm/s. *(VERIFIED — c13, c15. Exact `g_j`, `E_j` and `\tau` values are model- and species-specific; treat any single number as low confidence unless read from the specific paper's tables.)*

**2.3 Reaction–diffusion / transport model for the Variation Potential (VP).** The VP ("slow wave") is mechanistically **distinct** from the AP and is *not* a self-regenerating excitable wave. It is driven by a **hydraulic pressure surge and/or a wound chemical ("Ricca factor") carried by xylem mass flow** that transiently inactivates the H⁺-ATPase in cells along the path (Ricca 1916; Vodeneev, Katicheva & Sukhov 2015, *Plant Signal. Behav.* 10:e1057365; Evans et al. 2017, *Plant Journal* 91:1029–1037 — "Chemical agents transported by xylem mass flow propagate variation potentials"). *(VERIFIED — c14. NUANCE: Evans et al. 2017 present evidence favouring a xylem-transported chemical agent over a hydraulic pressure wave, so of the two proposed carriers the chemical is the better-supported one.)* Because neighbouring cells need not be electrically active, VPs cross **dead/killed tissue** — a hard qualitative discriminator. Modelling therefore couples an **advection–reaction–diffusion transport equation** for the wound signal `s(x,t)`,

$$\frac{\partial s}{\partial t}+v_{\text{flow}}\frac{\partial s}{\partial x}=D_s\frac{\partial^2 s}{\partial x^2}-k\,s,$$

to a *local* electrophysiological response (pump inactivation → depolarisation) at each cell. VP velocity per Fromm & Lautner is **≈ 0.1–1.0 cm/s** (i.e. ~1–10 mm/s), decrementing with distance and stimulus-strength-dependent — again unlike the constant-amplitude AP. *(CORRECTED: the draft's headline "≈ 0.1–1 mm/s" is ~10× lower than and inconsistent with the Fromm & Lautner range it cites in the same sentence (0.1–1.0 cm/s); some primary reports do quote VP as low as sub-mm/s, but the number attributed to Fromm & Lautner must be cm/s — c13.)*

---

### 3. A decisive near/far test: fit `V_far = V_near ∗ h` and read out λ, τ

**Principle.** Both hypotheses predict the far channel is a *filtered* copy of the near channel; they differ in the *kernel*. *(VERIFIED — c16.)*

| | Passive (electrotonic) | Active (regenerated wave) |
|---|---|---|
| Kernel `h(t)` | dispersive cable kernel `h_d(t)` (§1.3) | `h(t)\approx A\,\delta(t-\Delta)` |
| DC gain `\int h` | `e^{-d/\lambda}<1` (decrement) | `A\approx1` (amplitude preserved) |
| Shape change near→far | broadens + low-passes | shape ~invariant |
| Delay↔shape coupling | latency, width, attenuation **co-vary** | delay independent of shape/amplitude |
| Velocity vs coupling | not a true velocity; "speed" `\propto d/\tau`, distance-dependent | constant `c\propto\sqrt D`, distance-independent |

**Procedure.**
1. **Fit the passive model.** Estimate `\hat h(t)` by regularised deconvolution, or directly fit the two-parameter closed form `h_d(t)` (parameters `\mu=d/\lambda`, `\tau`) by nonlinear least squares minimising `\lVert V_{\text{far}}-V_{\text{near}}\ast h_d\rVert^2`. Report `R^2` / fraction of variance explained, and the implied `\lambda=d/\mu` and `\tau`.
2. **Fit the active (delay) model.** `V_{\text{far}}(t)\approx A\,V_{\text{near}}(t-\Delta)`; estimate `\Delta` by cross-correlation peak and `A` by regression. Report `R^2` and `A`.
3. **Compare** with an information criterion (AIC/BIC) since the models differ in parameters, and cross-validate across events.

**Decision rules.**
- **Passive** if the cable kernel fits well (high `R^2`) *with physically plausible* `\lambda,\tau` (`\tau` consistent with `R_mC_m\sim`0.1–10 s; `\lambda` of order the true `d` so that `\mu=d/\lambda` is `O(1)`), *and* the far waveform is visibly broadened/low-passed relative to near, *and* peak amplitude ratio `\approx e^{-\mu}`.
- **Active** if the best passive fit is poor or requires absurd parameters (e.g. `\lambda\gg` tissue length, `\tau` sub-ms or many minutes), while the pure-delay model fits with `A\approx1` and **no broadening**. Confirm with the physiological hard tests: constant amplitude over distance, a threshold, all-or-none behaviour, a refractory period, and (for AP vs VP) transmission through cooled/killed tissue. *(VERIFIED — c16.)*

**Robust quantitative discriminators (compute both):** *(VERIFIED — c17.)*
- **Amplitude ratio** `\rho=\max|V_{\text{far}}|/\max|V_{\text{near}}|`. Passive: `\rho\approx e^{-\mu}<1` and *falls* with `d`. Active: `\rho\approx1`, flat in `d`.
- **Width ratio** `W_{\text{far}}/W_{\text{near}}` (FWHM or second moment). Passive: `>1`, grows with `d`. Active: `\approx1`.
- **Latency–distance slope.** Active gives a straight `\Delta(d)=d/c` (constant velocity); passive gives a *nonlinear*, super-linear latency and no sharp arrival. Recording ≥3 electrodes resolves this cleanly.
- **Amplitude vs stimulus strength.** Active AP: all-or-none (flat above threshold). Passive & VP: graded.

**Numerical schemes.**
- Forward simulation of §2 PDEs: **operator-split** the reaction (stiff ODE per node — use an implicit/Rosenbrock or CVODE solver for the seconds-scale plant gating) from diffusion (Crank–Nicolson tridiagonal). Watch stiffness: plant gating spans ms→minutes.
- Deconvolution/kernel fit: work in the Laplace/Fourier domain using `H_d(s)=\exp[-\mu\sqrt{1+s\tau}]`, or fit the time-domain `h_d(t)` directly (more stable — it is smooth and one-sided). Regularise (Tikhonov / non-negativity, since a causal passive kernel is non-negative).
- Estimate `\Delta` by parabolic interpolation of the cross-correlation peak to beat the sampling interval.

**Pitfalls.**
- **Extracellular vs transmembrane.** Two-channel *extracellular* surface/aphid-stylet records measure a *difference/derivative* of the intracellular signal convolved with an electrode/tissue transfer function; the volume-conductor field is roughly the second spatial derivative of `V_m`. Calibrate the electrode transfer function or the passive `\rho`, width, and latency read-outs are biased. *(VERIFIED — c18.)*
- **Local re-excitation masquerading as passive delay** (and vice versa) — always use ≥3 electrodes to test velocity constancy, not a single pair.
- **AP vs VP confusion.** A decrementing, stimulus-graded, slow event crossing killed tissue is a VP, not a passively-attenuated AP — the transport model (§2.3), not the cable kernel, applies. Deconvolving a VP against the AP near-channel will give a spuriously "good" but meaningless cable fit.
- **Non-uniform cable** (tapering, branch points, gap-junction/plasmodesmatal resistance) breaks the single-`\lambda,\tau` kernel; allow a sum of two cable kernels or fit per-segment.
- **Boundary/reflection.** Finite plants reflect electrotonic signals; use the finite-cable Green function (image sums) if `d` is comparable to the organ length.
- **Velocity ∝ √D is only leading order** for FHN; near propagation failure (large `a`, strong recovery) speed drops steeply to zero — don't extrapolate the scaling to the excitability boundary.
- **Identifiability.** `\lambda` enters the kernel only as `\mu=d/\lambda`; you recover `\lambda` only if `d` is known. `\tau` and `\mu` are partially degenerate in the near field — fit multiple distances jointly.

---

**Sources (verified):** Fromm & Lautner 2007, *Plant Cell Environ.* 30:249–257; Sukhov & Vodeneev 2009, *J. Membr. Biol.* 232:59–67; Sukhov, Nerush, Orlova & Vodeneev 2011, *J. Theor. Biol.* 291:47–55; Sukhov, Akinchits, Katicheva & Vodeneev 2013, *J. Membr. Biol.* 246:287–296 (VP simulation); Vodeneev, Katicheva & Sukhov 2015, *Plant Signal. Behav.* 10:e1057365; Vodeneev, Katicheva & Sukhov 2016, *Biophysics* 61:505–512; Novikova, Vodeneev & Sukhov 2017, *Biochem. (Moscow) Suppl. Ser. A* 11:151–167; Sukhova, Akinchits & Sukhov 2017, *J. Membr. Biol.* 250:407–423 (models review); Evans et al. 2017, *Plant J.* 91:1029–1037; FitzHugh 1961, *Biophys. J.* 1:445–466; Nagumo, Arimoto & Yoshizawa 1962, *Proc. IRE* 50:2061–2070; Hodgkin & Rushton 1946, *Proc. R. Soc. B* 133:444–479 / Rall (cable theory); Keener & Sneyd, *Mathematical Physiology*; Murray, *Mathematical Biology* (Nagumo front speed). *(Author/volume corrections applied to the 2013 VP-simulation and 2017 review citations — see §2.2.)*