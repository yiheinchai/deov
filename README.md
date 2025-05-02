# **Directed Evolution Oncolytic Viruses (DE-OV)** 

The core principle is harnessing controlled, accelerated evolution *within the patient* to continuously generate viral variants that overcome tumor resistance and immune evasion faster than the cancer evolves defenses.
![ezgif-47983c15dd892d](https://github.com/user-attachments/assets/d7174dce-a836-43df-bc03-8c67dcf99042)

**The Problem We All Face:** Cancer's greatest weapon is its relentless evolution. It mutates, adapts, and develops resistance, constantly moving the goalposts and rendering even our best static or targeted therapies ineffective over time. We're essentially fighting a learning opponent with non-learning tools.

**The Core Idea:** What if we could create a therapy that *fights fire with fire*? This project simulates precisely that: a next-generation **Directed Evolution Oncolytic Virus (DE-OV)** designed to engage cancer in an evolutionary arms race – and win.

**Think of it like this:**

1.  **The Virus as a Smart Missile:** We start with a simulated oncolytic virus designed to target and kill cancer cells.
2.  **Cancer's Defenses:** The simulated cancer cells do what real cancer does:
    *   They change their surface markers (altering **Tropism** "locks") to prevent the virus from entering.
    *   They exist within an environment where the immune system tries to clear the virus.
3.  **The Virus That Learns (Hyper-Evolution):** Here's the key – this simulated virus isn't static. We've computationally embedded an **accelerated, targeted evolution engine** within it. During replication, it rapidly mutates two critical functions:
    *   **Its Targeting System (Tropism):** It constantly tries out new "keys" to match the changing "locks" on the cancer cells. If the cancer shifts its main receptor, the virus population rapidly evolves variants that can target the *new* receptor.
    *   **Its Stealth Coating (Immune Evasion):** Simultaneously, it rapidly mutates its ability to hide from the simulated immune system. Viruses that can't hide get cleared; only those that evolve better evasion survive long enough to infect and replicate.

**Why This Simulation is Exciting (Potential Clinical Relevance):**

*   **Autonomous Adaptation:** Unlike current adaptive therapies requiring external monitoring and intervention, this simulated virus adapts *on its own*, continuously responding to the tumor's evolution *in situ*.
*   **Overcoming Heterogeneity & Resistance:** By constantly evolving its targeting and evasion, the DE-OV population aims to keep pace with diverse and changing cancer clones, potentially overcoming the resistance mechanisms that plague static therapies.
*   **Potential for Durable Cure:** If the virus can adapt *faster* and *more effectively* than the cancer, it holds the potential (in theory, demonstrated here *in silico*) to drive the cancer population to extinction, even low-aggressiveness types that might otherwise persist against less adaptive agents.
*   **Guiding Real-World Design:** This simulation acts as a powerful "wind tunnel." By tweaking parameters (like mutation rates, immune interaction, viral potency), we can explore the fundamental design principles and critical thresholds needed to engineer a *real* synthetic virus capable of this autonomous, rapid evolution in the future.

**In Essence:** We're computationally modeling a therapeutic agent that doesn't just kill cancer but actively *learns* and *co-evolves* to defeat its adaptive strategies. It's a simulated glimpse into a future where therapies might finally operate on cancer's own evolutionary terms, but with engineered speed and intelligence.

## **I. The Oncolytic Virus (OV) Backbone: The Starting Chassis**

1.  **Virus Selection:** The choice of parental virus is critical. Common candidates include:
    *   **Adenovirus (Ad):** Non-integrating DNA virus, well-characterized, highly engineerable capsid for retargeting, relatively immunogenic. Often engineered by deleting E1A/E1B regions, making replication dependent on dysfunctional Rb/p53 pathways common in cancer.
    *   **Vaccinia Virus (VV):** Large DNA virus, robust replication, large payload capacity, inherent tumor selectivity (exploits high nucleotide pools, EGFR signaling, defective IFN pathways). TK (thymidine kinase) gene deletion enhances tumor selectivity.
    *   **Herpes Simplex Virus (HSV):** DNA virus, neurotropism needs attenuation (e.g., ICP34.5 deletion making it sensitive to normal cell PKR response but not cancer cells with defective PKR pathways), good payload capacity.
    *   **Vesicular Stomatitis Virus (VSV) / Measles Virus (MV):** RNA viruses, rapid replication, potent exploitation of defective Interferon (IFN) signaling in cancer cells. RNA viruses naturally have higher mutation rates due to RNA-dependent RNA polymerase (RdRP) infidelity, providing a baseline for further enhancement.
2.  **Baseline Oncolysis & Safety:** The chosen virus must be engineered for preferential replication in tumor cells and attenuation in normal tissues (as described above, e.g., exploiting defective IFN/PKR, p53/Rb pathways, or using tumor-specific promoters like hTERT, CEA, PSA to drive essential viral genes).
3.  **Initial Targeting (Optional but Recommended):** While evolution will refine tropism, starting with enhanced tumor targeting accelerates the process. This involves modifying viral surface proteins (e.g., Ad Fiber knob, HSV gD, MV H protein, VSV G protein) to bind tumor-associated antigens (TAAs) like EGFR, HER2, PSMA, Integrins, etc., often using inserted peptides, antibody fragments (scFvs), or designed ankyrin repeat proteins (DARPins).

## **II. The Directed Evolution Engine: Forcing Rapid Adaptation**

This is the crux. We need to introduce mechanisms for *hypermutation* or *hyper-recombination* specifically targeted to viral genes crucial for overcoming resistance.

1.  **Target Genes for Evolution:**
    *   **Tropism/Entry Genes:** Genes encoding receptor-binding proteins (as listed above). Evolution here allows the virus to adapt to cancer cells that downregulate or mutate the initial target receptor.
    *   **Immune Evasion Genes:** Viral genes that counteract host innate (IFN, PKR, RNase L) and adaptive (MHC-I presentation, T-cell recognition) immunity. Examples: VSV M protein (IFN suppression), HSV ICP47 (TAP inhibition), Ad E3 proteins (MHC-I downregulation). Evolution here allows the virus to persist longer against immune clearance.
    *   **(Potentially) Replication Efficiency Genes:** Genes involved in viral replication, specifically those whose efficiency might be impacted by anti-viral pathways active in resistant sub-clones.

2.  **Mechanisms for Inducing Targeted Diversity:**
    *   **Targeted Hypermutation using APOBEC/AID Systems:**
        *   **Mechanism:** Cytidine deaminases (like APOBEC3 family or Activation-Induced Deaminase) convert C -> U in DNA (or RNA via DNA intermediate/editing), leading to C:G -> T:A transitions upon replication. These enzymes are highly mutagenic.
        *   **Targeting:** Fuse the deaminase enzyme (or its catalytic domain) to a nuclease-deficient Cas9 (dCas9). Use guide RNAs (gRNAs) specific to the viral target genes (Tropism, Immune Evasion genes). The dCas9-AID fusion protein is recruited to the target loci, inducing localized hypermutation *only* in those genes during viral replication.
        *   **Control:** Expression of the dCas9-AID and gRNAs could be under an inducible promoter (e.g., tetracycline-responsive) or a tumor-specific promoter within the viral genome itself.
    *   **Error-Prone Polymerase Expression:**
        *   **Mechanism:** Introduce a gene encoding an error-prone DNA polymerase (like DNA Pol V - UmuC/D) or engineer the virus's own polymerase (DNA or RdRP) to be less faithful.
        *   **Targeting (Cruder):** This often increases the global mutation rate, which is less ideal. Targeting could be attempted by linking polymerase expression timing to the replication of specific genes or using inducible systems, but precise localization is harder than with dCas9-AID.
    *   **Site-Specific Recombination for Domain Shuffling:**
        *   **Mechanism:** Flank pre-designed libraries of genetic variants (e.g., multiple slightly different receptor-binding domains or immune evasion domain variants) within the target gene with recombination sites (e.g., LoxP or FRT sites). Include a gene for the corresponding recombinase (Cre or Flp) under stochastic or inducible control.
        *   **Action:** When the recombinase is expressed, it randomly shuffles or swaps these pre-defined cassettes, rapidly generating combinatorial diversity in the target protein. This is less "random evolution" and more "testing pre-designed solutions."
    *   **Segmented Virus Reassortment (If applicable):** For viruses with segmented genomes (like Influenza, though not typically oncolytic), co-infection allows natural shuffling of segments, a potent evolutionary force. Could potentially be engineered into synthetic segmented viruses.

## **III. Selection Pressures: Driving the Evolution**

The "intelligence" comes from the environment selecting the fittest variants:

1.  **Tumor Cell Resistance:** Cancer cells that alter receptors, upregulate anti-viral pathways, or develop other resistance mechanisms will kill off poorly adapted viral variants. Only viruses that mutate to overcome these specific defenses (e.g., bind a new receptor, better inhibit the specific anti-viral pathway) will successfully replicate and spread.
2.  **Immune System Pressure:**
    *   **Neutralizing Antibodies:** Target viral surface proteins. Viruses must mutate epitopes in these proteins to evade neutralization.
    *   **T-cell Recognition:** Targets viral peptides presented on MHC-I. Viruses must mutate epitopes or enhance MHC-I downregulation mechanisms to avoid T-cell killing of infected cells.
3.  **Tumor Microenvironment (TME):** Hypoxia, acidity, nutrient scarcity can impose selective pressures that favor viral variants better adapted to replicate under these harsh conditions.

## **IV. Interaction with the Immune System: A Double-Edged Sword**

*   **Positive:** Viral replication causes immunogenic cell death (ICD), releasing tumor antigens, PAMPs (viral nucleic acids, proteins), and DAMPs (HMGB1, ATP, calreticulin). This acts as an *in situ* vaccine, activating APCs (like dendritic cells) and priming potent anti-tumor T-cell responses via danger signaling (TLRs, STING). The *evolving* virus provides continually novel PAMPs and potentially reveals new tumor antigens.
*   **Negative:** The immune system will also target the virus itself. The DE-OV must evolve immune evasion strategies *just enough* to persist and spread within the tumor, but ideally not so much that it prevents the beneficial tumor-clearing immune response or causes systemic uncontrolled infection. This is a critical balance.

## **V. Safety and Control Considerations:**

*   **Precision Targeting of Evolution:** dCas9-AID offers the best theoretical control by limiting hypermutation to desired genes.
*   **Inducible Systems:** Controlling the mutation engine (e.g., requiring an external drug) adds a layer of safety.
*   **Suicide Genes:** Incorporating genes (e.g., HSV-tk) that make the virus susceptible to a safe prodrug (like Ganciclovir) allows for systemic elimination if needed.
*   **Self-Limiting Replication:** Relying on tumor-specific replication dependencies ensures the virus attenuates as the tumor burden decreases.
*   **Rigorous Preclinical Testing:** Assessing the risk of generating overly virulent or off-target pathogenic variants is paramount. Mathematical modeling of the evolutionary dynamics will be essential.

## **VI. The "Second-Order" Nature (via Speed and Parallelism):**

DE-OV approach aims for second-order *outcomes* by:

*   **Proactive Adaptation Speed:** The engineered hypermutation rate aims to be orders of magnitude faster than the cancer's mutation rate and the host's adaptive immune response generation time. It seeks to solve resistance problems *as they emerge* or even slightly before they become dominant.
*   **Massive Parallelism:** A vast population of diverse viral mutants explores the "solution space" simultaneously. Instead of one agent trying to predict, millions of variants test different strategies in parallel, driven by the immediate selective pressures.
*   **Targeting Evolvability (Implicitly):** By constantly adapting to the tumor's defenses, it keeps pressure on the cancer, potentially selecting against highly adaptable cancer clones if they cannot simultaneously counter the rapidly evolving virus.

## **Conclusion:**

The Directed Evolution Oncolytic Virus concept is technically demanding but represents a plausible biological implementation of a learning, adaptive therapeutic. It leverages principles of directed evolution, synthetic biology (dCas9-AID, targeted recombination), and virology. Its success hinges on precisely controlling the evolutionary engine, balancing viral persistence with safety, navigating the complex interplay with the host immune system, and achieving an adaptation speed that consistently outpaces tumor evolution. This approach shifts the paradigm from static or slowly adapting therapies to one where the therapeutic agent itself rapidly evolves *in situ* to overcome the dynamic challenge of cancer.


## Simulations
![simulation_plot_agg_0 10](https://github.com/user-attachments/assets/df6dbcaa-d871-4f99-8fe8-cc307c25ca16)

![ezgif-47983c15dd892d](https://github.com/user-attachments/assets/d7174dce-a836-43df-bc03-8c67dcf99042)


### Explaining tropism in simulations
Think of it like a **key and lock system**:

1.  **The Lock (Cancer Cell):** Each `CancerCell` object has an attribute called `receptor_type`. In our simulation, this can be 'ReceptorA', 'ReceptorB', or 'ReceptorC'. This represents a specific molecule or structure on the surface of that particular cancer cell. This is the "lock."
2.  **The Key (Virus Particle):** Each `VirusParticle` object has a `genotype`, which is a dictionary. Inside this dictionary, there's a key called `'tropism'`. The value associated with `'tropism'` (e.g., 'ReceptorA', 'ReceptorB', or 'ReceptorC') represents the specific type of "lock" that this particular virus particle is designed to fit. This is the "key."
3.  **Infection Attempt:** When a virus particle encounters a cancer cell, the simulation checks if the virus's "key" matches the cell's "lock." Specifically, the `CancerCell.attempt_infection` method checks if `virus.genotype['tropism'] == self.receptor_type`.
    *   **Match:** If the virus's `tropism` matches the cell's `receptor_type`, the virus has a high base probability (`VIRAL_INFECTION_PROB_BASE`) of successfully infecting the cell (modified by the cell's general antiviral resistance).
    *   **Mismatch:** If they don't match, the infection probability is essentially zero. The virus cannot effectively "unlock" and enter the cell.

**Why Tropism is Crucial in this Simulation (The Evolutionary Arms Race):**

*   **Cancer Resistance:** Cancer cells can evolve resistance by changing their surface receptors. In the simulation, this happens randomly based on the `effective_cancer_mutation_rate_resistance`. A cell might switch from expressing 'ReceptorA' to 'ReceptorB'. Viruses with `tropism` 'ReceptorA' can no longer effectively infect this mutated cell. If many cells make this switch, the original virus population becomes ineffective.
*   **Viral Adaptation (Directed Evolution):** This is where the DE-OV concept comes in. The virus isn't static. During replication (in the `CancerCell.lyse` method), there's a high probability (`MUTATION_RATE_TROPISM`) that the *new* virus particles produced will have a *different* `tropism` than their parent. They might randomly switch from targeting 'ReceptorA' to 'ReceptorB' or 'ReceptorC'.
*   **Selection Pressure:** If the cancer population shifts to predominantly expressing 'ReceptorB', only those newly mutated viruses that happen to have gained the 'ReceptorB' `tropism` will be able to infect successfully and replicate massively. Viruses still targeting 'ReceptorA' or 'ReceptorC' will fail to propagate effectively. This drives the evolution of the virus population to match the current cancer population.

**In the Plots:**

The middle plot, "Virus Tropism Evolution (Frequency)," directly visualizes this dynamic. You see the percentage of the *total virus population* that has a specific `tropism` ('ReceptorA', 'ReceptorB', or 'ReceptorC') changing over time. This reflects the ongoing evolutionary battle – the virus population shifting its targeting strategy (changing its "keys") in response to the cancer cells changing their surface "locks."

In short, **tropism in this simulation is the specific receptor type a virus targets, determining which cancer cells it can effectively infect.** The ability of the virus to rapidly mutate its tropism is essential for it to adapt and overcome cancer cell resistance based on receptor changes.
