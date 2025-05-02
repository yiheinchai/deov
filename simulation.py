# -*- coding: utf-8 -*-
import numpy as np
import random
import matplotlib

matplotlib.use("Agg")  # Use Agg backend for non-interactive plot saving
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from collections import Counter
import copy
import math
import os
import shutil  # For removing frame directory
import imageio  # For creating videos/gifs

# --- Simulation Parameters ---
GRID_SIZE = 40
INITIAL_CANCER_CELLS = 150
INITIAL_VIRUS_PARTICLES = 150  # Keep increased initial dose
INITIAL_IMMUNE_CELLS = 15
SIMULATION_STEPS = 350  # Allow enough time for potential clearance

# --- Cancer Aggressiveness Control ---
CANCER_AGGRESSIVENESS_LEVEL = 0.10  # Set default for single run

# Base Cancer Cell Parameters
BASE_CANCER_REPLICATION_PROB = 0.06
BASE_CANCER_ANTIVIRAL_RESISTANCE = 0.05
BASE_CANCER_MUTATION_RATE_RESISTANCE = 0.002

# Aggressiveness Scaling Factors
REPLICATION_AGGRESSIVENESS_FACTOR = 2.0
RESISTANCE_AGGRESSIVENESS_FACTOR = 4.0
MUTATION_AGGRESSIVENESS_FACTOR = 5.0

INITIAL_RESISTANCE_TYPES = ["ReceptorA", "ReceptorB", "ReceptorC"]
INITIAL_RESISTANCE_DISTRIBUTION = {"ReceptorA": 0.6, "ReceptorB": 0.3, "ReceptorC": 0.1}

# Virus Parameters
VIRUS_REPLICATION_BURST_SIZE = 50
INFECTION_LATENCY_PERIOD = 5
VIRAL_INFECTION_PROB_BASE = 0.90

# --- Directed Evolution Parameters ---
VIRUS_GENOTYPE_KEYS = ["tropism", "immune_evasion"]
INITIAL_VIRUS_TROPISM = "ReceptorA"
INITIAL_VIRUS_EVASION = 0.1
MUTATION_RATE_TROPISM = 0.15  # Keep tropism adaptation high
# *** STRONGLY INCREASED EVASION MUTATION ***
MUTATION_RATE_EVASION = 0.25  # Much higher chance to mutate evasion (was 0.10)
MUTATION_EVASION_STEP = 0.15  # Much larger steps in evasion change (was 0.08)

# Immune System Parameters
IMMUNE_CELL_PATROL_RADIUS = 2
IMMUNE_KILL_PROB_INFECTED = 0.7  # Keep pressure on infected cells high
# *** SLIGHTLY REDUCED PRESSURE ON FREE VIRUS ***
IMMUNE_KILL_PROB_FREE_VIRUS = 0.30  # Give free virus slightly better chance (was 0.4)
# *** INCREASED EVASION EFFECTIVENESS ***
EVASION_EFFECTIVENESS = 0.98  # Make evasion almost fully protective (was 0.9)
IMMUNE_RECRUITMENT_PROB = 0.05

# --- Video Generation Parameters ---
SAVE_VIDEO = True
FRAME_SAVE_FREQ = 5
VIDEO_FPS = 10
FRAME_DIR = "simulation_frames"


# --- Helper Functions ---
def get_moore_neighbors(pos, grid_shape, radius=1):
    r, c = pos
    neighbors = []
    for dr in range(-radius, radius + 1):
        for dc in range(-radius, radius + 1):
            if dr == 0 and dc == 0:
                continue
            nr, nc = r + dr, c + dc
            if 0 <= nr < grid_shape[0] and 0 <= nc < grid_shape[1]:
                neighbors.append((nr, nc))
    return neighbors


# --- Agent Classes ---
class CancerCell:
    _id_counter = 0

    def __init__(
        self,
        pos,
        receptor_type,
        replication_prob,
        antiviral_resistance,
        resistance_mutation_rate,
    ):
        self.id = f"C_{CancerCell._id_counter}"
        CancerCell._id_counter += 1
        self.pos = pos
        self.receptor_type = receptor_type
        self.replication_prob = replication_prob
        self.antiviral_resistance = antiviral_resistance
        self.resistance_mutation_rate = resistance_mutation_rate
        self.is_infected = False
        self.infection_timer = 0
        self.virus_genotype_inside = None

    def attempt_replication(self, grid, occupied_claims):
        if not self.is_infected and random.random() < self.replication_prob:
            neighbors = get_moore_neighbors(self.pos, grid.shape)
            empty_neighbors = [
                (r, c)
                for r, c in neighbors
                if grid[r, c] is None and (r, c) not in occupied_claims
            ]
            if empty_neighbors:
                new_pos = random.choice(empty_neighbors)
                new_receptor = self.receptor_type
                if random.random() < self.resistance_mutation_rate:
                    available_receptors = [
                        r for r in INITIAL_RESISTANCE_TYPES if r != self.receptor_type
                    ]
                    if available_receptors:
                        new_receptor = random.choice(available_receptors)
                new_cell = CancerCell(
                    new_pos,
                    new_receptor,
                    self.replication_prob,
                    self.antiviral_resistance,
                    self.resistance_mutation_rate,
                )
                return new_cell
        return None

    def attempt_infection(self, virus):
        if self.is_infected:
            return False
        tropism_match = virus.genotype["tropism"] == self.receptor_type
        infection_prob = VIRAL_INFECTION_PROB_BASE if tropism_match else 0.0
        infection_prob *= 1 - self.antiviral_resistance
        infection_prob = max(0, infection_prob)
        if random.random() < infection_prob:
            self.is_infected = True
            self.infection_timer = INFECTION_LATENCY_PERIOD
            self.virus_genotype_inside = copy.deepcopy(virus.genotype)
            return True
        return False

    def progress_infection(self):
        if self.is_infected:
            self.infection_timer -= 1
            if self.infection_timer <= 0:
                return True
        return False

    def lyse(self):
        if not self.is_infected or not self.virus_genotype_inside:
            return []
        new_viruses = []
        parent_genotype = self.virus_genotype_inside
        for _ in range(VIRUS_REPLICATION_BURST_SIZE):
            new_genotype = copy.deepcopy(parent_genotype)
            # Tropism Mutation
            if random.random() < MUTATION_RATE_TROPISM:
                possible_tropisms = [
                    r for r in INITIAL_RESISTANCE_TYPES if r != new_genotype["tropism"]
                ]
                if possible_tropisms:
                    new_genotype["tropism"] = random.choice(possible_tropisms)
            # Evasion Mutation
            if random.random() < MUTATION_RATE_EVASION:
                change = random.choice([-MUTATION_EVASION_STEP, MUTATION_EVASION_STEP])
                new_genotype["immune_evasion"] = max(
                    0, min(1, new_genotype["immune_evasion"] + change)
                )  # Clamp between 0 and 1
            new_viruses.append(VirusParticle(self.pos, new_genotype))
        return new_viruses


class VirusParticle:
    _id_counter = 0

    def __init__(self, pos, genotype):
        self.id = f"V_{VirusParticle._id_counter}"
        VirusParticle._id_counter += 1
        self.pos = pos
        self.genotype = genotype

    def move_randomly(self, grid_shape):
        dr = random.randint(-1, 1)
        dc = random.randint(-1, 1)
        new_r = max(0, min(grid_shape[0] - 1, self.pos[0] + dr))
        new_c = max(0, min(grid_shape[1] - 1, self.pos[1] + dc))
        self.pos = (new_r, new_c)


class ImmuneCell:
    _id_counter = 0

    def __init__(self, pos):
        self.id = f"I_{ImmuneCell._id_counter}"
        ImmuneCell._id_counter += 1
        self.pos = pos

    def move_randomly(self, grid_shape):
        dr = random.randint(-1, 1)
        dc = random.randint(-1, 1)
        new_r = max(0, min(grid_shape[0] - 1, self.pos[0] + dr))
        new_c = max(0, min(grid_shape[1] - 1, self.pos[1] + dc))
        self.pos = (new_r, new_c)

    def patrol_and_kill(self, grid):
        self.move_randomly(grid.shape)
        targets_killed_ids = {"cancer": [], "virus": []}
        neighbor_coords = get_moore_neighbors(
            self.pos, grid.shape, radius=IMMUNE_CELL_PATROL_RADIUS
        )
        neighbor_coords.append(self.pos)
        potential_targets_at_coord = {}
        for r, c in neighbor_coords:
            content = grid[r, c]
            if content is not None:
                potential_targets_at_coord[(r, c)] = []
                items_to_check = content if isinstance(content, list) else [content]
                for item in items_to_check:
                    if isinstance(item, CancerCell) and item.is_infected:
                        potential_targets_at_coord[(r, c)].append(item)
                    elif isinstance(item, VirusParticle):
                        potential_targets_at_coord[(r, c)].append(item)
        for coord, targets in potential_targets_at_coord.items():
            random.shuffle(targets)
            processed_targets_at_coord = set()
            for target in targets:
                if target.id in processed_targets_at_coord:
                    continue
                kill_prob = 0
                target_type = "none"
                if isinstance(target, CancerCell):
                    evasion_level = (
                        target.virus_genotype_inside["immune_evasion"]
                        if target.virus_genotype_inside
                        else 0
                    )
                    kill_prob = IMMUNE_KILL_PROB_INFECTED * (
                        1 - evasion_level * EVASION_EFFECTIVENESS
                    )
                    target_type = "cancer"
                elif isinstance(target, VirusParticle):
                    evasion_level = target.genotype["immune_evasion"]
                    kill_prob = IMMUNE_KILL_PROB_FREE_VIRUS * (
                        1 - evasion_level * EVASION_EFFECTIVENESS
                    )
                    target_type = "virus"
                kill_prob = max(0, kill_prob)
                if random.random() < kill_prob:
                    if target_type == "cancer":
                        targets_killed_ids["cancer"].append(target.id)
                    elif target_type == "virus":
                        targets_killed_ids["virus"].append(target.id)
                    processed_targets_at_coord.add(target.id)
        return targets_killed_ids


# --- Simulation Class ---
class Simulation:
    def __init__(self, cancer_aggressiveness=0.5):
        self.cancer_aggressiveness = max(0.0, min(1.0, cancer_aggressiveness))
        self.effective_cancer_replication_prob = BASE_CANCER_REPLICATION_PROB * (
            1 + self.cancer_aggressiveness * REPLICATION_AGGRESSIVENESS_FACTOR
        )
        self.effective_cancer_antiviral_resistance = (
            BASE_CANCER_ANTIVIRAL_RESISTANCE
            * (1 + self.cancer_aggressiveness * RESISTANCE_AGGRESSIVENESS_FACTOR)
        )
        self.effective_cancer_antiviral_resistance = min(
            0.95, self.effective_cancer_antiviral_resistance
        )
        self.effective_cancer_mutation_rate_resistance = (
            BASE_CANCER_MUTATION_RATE_RESISTANCE
            * (1 + self.cancer_aggressiveness * MUTATION_AGGRESSIVENESS_FACTOR)
        )

        print("\n--- Effective Cancer Parameters ---")
        print(f"  Aggressiveness Level: {self.cancer_aggressiveness:.2f}")
        print(f"  Replication Prob:     {self.effective_cancer_replication_prob:.4f}")
        print(
            f"  Antiviral Resistance: {self.effective_cancer_antiviral_resistance:.4f}"
        )
        print(
            f"  Resistance Mut Rate:  {self.effective_cancer_mutation_rate_resistance:.5f}"
        )
        print("-----------------------------------\n")

        self.grid = np.full((GRID_SIZE, GRID_SIZE), None, dtype=object)
        self.cancer_cells = {}
        self.virus_particles = {}
        self.immune_cells = {}
        self.current_step = 0
        self.history = {
            "step": [],
            "cancer_count": [],
            "virus_count": [],
            "immune_count": [],
            "infected_count": [],
            "cancer_types": [],
            "virus_tropisms": [],
            "virus_evasion": [],
        }
        CancerCell._id_counter = 0
        VirusParticle._id_counter = 0
        ImmuneCell._id_counter = 0

        self.frame_files = []
        if SAVE_VIDEO:
            if os.path.exists(FRAME_DIR):
                shutil.rmtree(FRAME_DIR)
            os.makedirs(FRAME_DIR)

        self._initialize_population()

    def _initialize_population(self):
        placed_cells = 0
        while placed_cells < INITIAL_CANCER_CELLS:
            r, c = random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)
            if self.grid[r, c] is None:
                receptor = random.choices(
                    list(INITIAL_RESISTANCE_DISTRIBUTION.keys()),
                    weights=list(INITIAL_RESISTANCE_DISTRIBUTION.values()),
                )[0]
                cell = CancerCell(
                    (r, c),
                    receptor,
                    self.effective_cancer_replication_prob,
                    self.effective_cancer_antiviral_resistance,
                    self.effective_cancer_mutation_rate_resistance,
                )
                self.grid[r, c] = cell
                self.cancer_cells[cell.id] = cell
                placed_cells += 1

        placed_viruses = 0
        if self.cancer_cells:
            cell_positions = [cell.pos for cell in self.cancer_cells.values()]
            while placed_viruses < INITIAL_VIRUS_PARTICLES:
                target_pos = random.choice(cell_positions)
                r_offset, c_offset = random.randint(-1, 1), random.randint(-1, 1)
                r = max(0, min(GRID_SIZE - 1, target_pos[0] + r_offset))
                c = max(0, min(GRID_SIZE - 1, target_pos[1] + c_offset))
                initial_genotype = {
                    "tropism": INITIAL_VIRUS_TROPISM,
                    "immune_evasion": INITIAL_VIRUS_EVASION,
                }
                virus = VirusParticle((r, c), initial_genotype)
                current_content = self.grid[r, c]
                if current_content is None:
                    self.grid[r, c] = [virus]
                elif isinstance(current_content, CancerCell):
                    self.grid[r, c] = [current_content, virus]
                elif isinstance(current_content, list):
                    current_content.append(virus)
                self.virus_particles[virus.id] = virus
                placed_viruses += 1
        else:
            print("Warning: No initial cancer cells.")

        placed_immune = 0
        while placed_immune < INITIAL_IMMUNE_CELLS:
            r, c = random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)
            immune_cell = ImmuneCell((r, c))
            self.immune_cells[immune_cell.id] = immune_cell
            placed_immune += 1

        print(
            f"Initialization: {len(self.cancer_cells)} cells, {len(self.virus_particles)} viruses, {len(self.immune_cells)} immune cells."
        )
        self._record_history()
        if SAVE_VIDEO:
            self._save_grid_frame()

    def _cleanup_and_reconcile_grid(self):
        new_grid = np.full((GRID_SIZE, GRID_SIZE), None, dtype=object)
        for cell_id, cell in self.cancer_cells.items():
            r, c = cell.pos
            if new_grid[r, c] is None:
                new_grid[r, c] = cell
            else:
                print(
                    f"GRID RECONCILE WARNING: Overlap for cell {cell_id} at {cell.pos}. Existing: {new_grid[r,c]}"
                )

        for virus_id, virus in self.virus_particles.items():
            r, c = virus.pos
            current_content = new_grid[r, c]
            if current_content is None:
                new_grid[r, c] = [virus]
            elif isinstance(current_content, CancerCell):
                new_grid[r, c] = [current_content, virus]
            elif isinstance(current_content, list):
                current_content.append(virus)  # Simplification: just append
            else:
                print(
                    f"GRID RECONCILE WARNING: Unexpected content {type(current_content)} at {virus.pos} for virus {virus.id}"
                )
        self.grid = new_grid

    def run_step(self):
        if not self.cancer_cells and not self.virus_particles:
            return False

        newly_created_cancer = []
        lysed_cells_ids = set()
        newly_created_viruses = []
        killed_by_immune_ids = {"cancer": set(), "virus": set()}
        viruses_infected_this_step = set()

        # Stage 1: Immune
        immune_cell_ids = list(self.immune_cells.keys())
        random.shuffle(immune_cell_ids)
        for agent_id in immune_cell_ids:
            if agent_id in self.immune_cells:
                immune_cell = self.immune_cells[agent_id]
                targets_killed = immune_cell.patrol_and_kill(self.grid)
                killed_by_immune_ids["cancer"].update(targets_killed["cancer"])
                killed_by_immune_ids["virus"].update(targets_killed["virus"])

        # Stage 2: Cancer
        cancer_cell_ids = list(self.cancer_cells.keys())
        random.shuffle(cancer_cell_ids)
        replication_claims = set()
        for agent_id in cancer_cell_ids:
            if (
                agent_id in self.cancer_cells
                and agent_id not in killed_by_immune_ids["cancer"]
            ):
                cell = self.cancer_cells[agent_id]
                if not cell.is_infected:
                    new_cell = cell.attempt_replication(self.grid, replication_claims)
                    if new_cell:
                        newly_created_cancer.append(new_cell)
                        replication_claims.add(new_cell.pos)
                if cell.is_infected:
                    if cell.progress_infection():
                        lysed_cells_ids.add(agent_id)

        # Stage 3: Virus
        virus_ids = list(self.virus_particles.keys())
        random.shuffle(virus_ids)
        virus_new_positions = {}
        for agent_id in virus_ids:
            if (
                agent_id in self.virus_particles
                and agent_id not in killed_by_immune_ids["virus"]
            ):
                virus = self.virus_particles[agent_id]
                virus.move_randomly(self.grid.shape)
                virus_new_positions[agent_id] = virus.pos

        viruses_at_location = {}
        for virus_id, new_pos in virus_new_positions.items():
            viruses_at_location.setdefault(new_pos, []).append(virus_id)

        for pos, resident_virus_ids in viruses_at_location.items():
            content = self.grid[pos]  # Use current grid state
            target_cell = None
            if isinstance(content, CancerCell):
                target_cell = content
            elif (
                isinstance(content, list)
                and len(content) > 0
                and isinstance(content[0], CancerCell)
            ):
                target_cell = content[0]

            if (
                target_cell
                and target_cell.id in self.cancer_cells
                and target_cell.id not in killed_by_immune_ids["cancer"]
                and not target_cell.is_infected
            ):
                random.shuffle(resident_virus_ids)
                for infecting_virus_id in resident_virus_ids:
                    if (
                        infecting_virus_id in self.virus_particles
                        and infecting_virus_id not in killed_by_immune_ids["virus"]
                        and infecting_virus_id not in viruses_infected_this_step
                    ):
                        virus = self.virus_particles[infecting_virus_id]
                        if target_cell.attempt_infection(virus):
                            viruses_infected_this_step.add(infecting_virus_id)
                            break

        # Stage 4: State Updates
        for cell_id in killed_by_immune_ids["cancer"]:
            if cell_id in self.cancer_cells:
                del self.cancer_cells[cell_id]
        all_viruses_to_remove = killed_by_immune_ids["virus"].union(
            viruses_infected_this_step
        )
        for virus_id in all_viruses_to_remove:
            if virus_id in self.virus_particles:
                del self.virus_particles[virus_id]

        lysed_cell_positions = []
        for cell_id in lysed_cells_ids:
            if cell_id in self.cancer_cells:
                cell = self.cancer_cells[cell_id]
                lysed_cell_positions.append(cell.pos)
                new_viruses_from_lysis = cell.lyse()
                newly_created_viruses.extend(new_viruses_from_lysis)
                del self.cancer_cells[cell_id]

        for cell in newly_created_cancer:
            self.cancer_cells[cell.id] = cell

        for virus in newly_created_viruses:
            self.virus_particles[virus.id] = virus

        num_recruits = sum(
            1
            for _ in range(len(lysed_cell_positions))
            if random.random() < IMMUNE_RECRUITMENT_PROB
        )
        if num_recruits > 0 and lysed_cell_positions:
            for _ in range(num_recruits):
                ref_pos = random.choice(lysed_cell_positions)
                r_offset, c_offset = random.randint(-2, 2), random.randint(-2, 2)
                r = max(0, min(GRID_SIZE - 1, ref_pos[0] + r_offset))
                c = max(0, min(GRID_SIZE - 1, ref_pos[1] + c_offset))
                immune_cell = ImmuneCell((r, c))
                self.immune_cells[immune_cell.id] = immune_cell

        self._cleanup_and_reconcile_grid()

        # Stage 5: Record History & Increment Step
        self.current_step += 1
        self._record_history()
        if SAVE_VIDEO and self.current_step % FRAME_SAVE_FREQ == 0:
            self._save_grid_frame()
        return True

    def _record_history(self):
        self.history["step"].append(self.current_step)
        self.history["cancer_count"].append(len(self.cancer_cells))
        self.history["virus_count"].append(len(self.virus_particles))
        self.history["immune_count"].append(len(self.immune_cells))
        self.history["infected_count"].append(
            sum(1 for c in self.cancer_cells.values() if c.is_infected)
        )
        self.history["cancer_types"].append(
            Counter(c.receptor_type for c in self.cancer_cells.values())
        )
        self.history["virus_tropisms"].append(
            Counter(v.genotype["tropism"] for v in self.virus_particles.values())
        )
        self.history["virus_evasion"].append(
            np.mean(
                [v.genotype["immune_evasion"] for v in self.virus_particles.values()]
            )
            if self.virus_particles
            else 0
        )

    def run_simulation(self):
        print(
            f"--- Starting Simulation (Aggressiveness: {self.cancer_aggressiveness:.2f}) ---"
        )
        for step in range(SIMULATION_STEPS):
            success = self.run_step()
            if not success:
                break
            if step % 25 == 0 or step == SIMULATION_STEPS - 1 or not self.cancer_cells:
                print(
                    f"Step: {self.current_step:>3}/{SIMULATION_STEPS} | "
                    f"Cancer: {len(self.cancer_cells):>4} ({self.history['infected_count'][-1]:>3} inf) | "
                    f"Viruses: {len(self.virus_particles):>5} | "
                    f"Immune: {len(self.immune_cells):>3} | "
                    f"Avg Evasion: {self.history['virus_evasion'][-1]:.3f}"
                )
            if not self.cancer_cells:
                print(f"\n--- Cancer Eliminated at Step {self.current_step}! ---")
                if SAVE_VIDEO and self.current_step % FRAME_SAVE_FREQ != 0:
                    self._save_grid_frame()
                break
            if len(self.cancer_cells) > GRID_SIZE * GRID_SIZE * 0.9:
                print(
                    f"\n--- Simulation stopped: Cancer overwhelmed grid ({len(self.cancer_cells)} cells) at step {self.current_step}. ---"
                )
                break
        if self.current_step >= SIMULATION_STEPS and self.cancer_cells:
            print(
                f"\n--- Simulation Ended at Step {SIMULATION_STEPS}. Cancer persists. ---"
            )
        elif (
            self.current_step < SIMULATION_STEPS
            and self.cancer_cells
            and not self.virus_particles
            and not any(c.is_infected for c in self.cancer_cells.values())
        ):
            print(
                f"\n--- Simulation ended after virus elimination. Cancer persists. ---"
            )
        if SAVE_VIDEO:
            self._create_video()

    def plot_results(self):
        if not self.history["step"]:
            print("No simulation history to plot.")
            return
        print("\n--- Plotting and Saving Results ---")
        fig, axs = plt.subplots(3, 1, figsize=(12, 15), sharex=True)
        plot_title = (
            f"DE-OV Sim Results (Aggressiveness: {self.cancer_aggressiveness:.2f})"
        )
        fig.suptitle(plot_title, fontsize=16)
        steps = self.history["step"]
        axs[0].plot(
            steps,
            self.history["cancer_count"],
            label="Total Cancer Cells",
            color="red",
            linewidth=2,
        )
        axs[0].plot(
            steps,
            self.history["infected_count"],
            label="Infected Cells",
            color="orange",
            linestyle="--",
            linewidth=2,
        )
        axs[0].plot(
            steps,
            self.history["virus_count"],
            label="Virus Particles",
            color="blue",
            linewidth=1.5,
        )
        axs[0].plot(
            steps,
            self.history["immune_count"],
            label="Immune Cells",
            color="green",
            linewidth=1.5,
        )
        axs[0].set_ylabel("Population Count")
        axs[0].set_title("Population Dynamics")
        axs[0].legend()
        axs[0].grid(True, linestyle=":", alpha=0.7)
        axs[0].set_yscale("symlog", linthresh=10)
        axs[0].set_ylim(bottom=0)
        tropism_types = sorted(list(INITIAL_RESISTANCE_TYPES))
        tropism_data = {t: [] for t in tropism_types}
        for step_data in self.history["virus_tropisms"]:
            total_viruses = sum(step_data.values())
            for t in tropism_types:
                freq = (step_data.get(t, 0) / total_viruses) if total_viruses > 0 else 0
                tropism_data[t].append(freq * 100)
        for trop_type in tropism_types:
            axs[1].plot(steps, tropism_data[trop_type], label=f"Tropism {trop_type}")
        axs[1].set_ylabel("Virus Tropism Frequency (%)")
        axs[1].set_title("Virus Tropism Evolution (Frequency)")
        axs[1].legend()
        axs[1].grid(True, linestyle=":", alpha=0.7)
        axs[1].set_ylim(0, 101)
        axs[2].plot(
            steps,
            self.history["virus_evasion"],
            label="Avg. Immune Evasion",
            color="purple",
            linewidth=2,
        )
        axs[2].set_xlabel("Time Steps")
        axs[2].set_ylabel("Average Evasion Level (0-1)")
        axs[2].set_title("Virus Immune Evasion Evolution")
        axs[2].legend()
        axs[2].grid(True, linestyle=":", alpha=0.7)
        axs[2].set_ylim(0, 1)
        plt.tight_layout(rect=[0, 0.03, 1, 0.97])
        plot_filename = f"simulation_plot_agg_{self.cancer_aggressiveness:.2f}.png"
        plt.savefig(plot_filename)
        print(f"Plot saved to {plot_filename}")
        plt.close(fig)

    def _save_grid_frame(self):
        cmap = mcolors.ListedColormap(
            ["black", "lightcoral", "darkorange", "mediumblue", "limegreen"]
        )
        bounds = [-0.5, 0.5, 1.5, 2.5, 3.5, 4.5]
        norm = mcolors.BoundaryNorm(bounds, cmap.N)
        grid_numeric = np.zeros((GRID_SIZE, GRID_SIZE))
        immune_positions = {i.pos for i in self.immune_cells.values()}
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                content = self.grid[r, c]
                val = 0
                if isinstance(content, CancerCell):
                    val = 2 if content.is_infected else 1
                elif isinstance(content, list):
                    if len(content) > 0 and isinstance(content[0], CancerCell):
                        val = 2 if content[0].is_infected else 1
                    elif any(isinstance(item, VirusParticle) for item in content):
                        val = 3
                if (r, c) in immune_positions:
                    val = 4
                grid_numeric[r, c] = val
        fig_frame, ax_frame = plt.subplots(figsize=(6, 6))
        im = ax_frame.imshow(
            grid_numeric, cmap=cmap, norm=norm, interpolation="nearest"
        )
        cbar_labels = ["Empty", "Cancer", "Infected", "Virus", "Immune"]
        patches = [
            plt.Rectangle((0, 0), 1, 1, fc=cmap(norm(i)))
            for i in range(len(cbar_labels))
        ]
        ax_frame.legend(
            patches,
            cbar_labels,
            bbox_to_anchor=(1.02, 1),
            loc="upper left",
            borderaxespad=0.0,
        )
        ax_frame.set_title(
            f"Step: {self.current_step} (Agg: {self.cancer_aggressiveness:.2f})"
        )
        ax_frame.set_xticks([])
        ax_frame.set_yticks([])
        frame_filename = os.path.join(FRAME_DIR, f"frame_{self.current_step:04d}.png")
        try:
            plt.savefig(frame_filename, bbox_inches="tight", dpi=100)
            self.frame_files.append(frame_filename)
        except Exception as e:
            print(f"Error saving frame {frame_filename}: {e}")
        finally:
            plt.close(fig_frame)  # Ensure figure is closed

    def _create_video(self):
        if not self.frame_files:
            print("No frames saved to create video.")
            return
        # Sort frames numerically, robustly
        self.frame_files.sort(
            key=lambda f: int(os.path.basename(f).split("_")[1].split(".")[0])
        )
        video_filename = f"simulation_video_agg_{self.cancer_aggressiveness:.2f}.mp4"
        print(f"\n--- Creating Video: {video_filename} ---")
        try:
            with imageio.get_writer(
                video_filename, fps=VIDEO_FPS, macro_block_size=8
            ) as writer:  # Added macro_block_size for compatibility
                for filename in self.frame_files:
                    try:
                        image = imageio.v2.imread(filename)
                        writer.append_data(image)  # Use imageio.v2.imread
                    except Exception as e:
                        print(f"Skipping frame {filename} due to read error: {e}")
            print("Video creation successful.")
        except Exception as e:
            print(
                f"Error creating video: {e}\nEnsure imageio and ffmpeg installed: pip install imageio imageio[ffmpeg]"
            )
        # finally: # Optional cleanup
        # if os.path.exists(FRAME_DIR): shutil.rmtree(FRAME_DIR); print(f"Removed frame directory: {FRAME_DIR}")


# --- Run Simulation ---
if __name__ == "__main__":
    # Run single simulation with default aggressiveness
    sim_single = Simulation(cancer_aggressiveness=CANCER_AGGRESSIVENESS_LEVEL)
    sim_single.run_simulation()
    sim_single.plot_results()

    # Run multiple simulations
    print("\n\n--- Running Multiple Aggressiveness Levels ---")
    aggressiveness_levels = [0.1, 0.4, 0.7, 0.9]
    results_summary = {}
    for level in aggressiveness_levels:
        print(f"\n===== Running Simulation for Aggressiveness: {level:.2f} =====")
        sim_multi = Simulation(cancer_aggressiveness=level)
        sim_multi.run_simulation()
        results_summary[level] = {
            "final_step": sim_multi.current_step,
            "final_cancer": len(sim_multi.cancer_cells),
            "final_virus": len(sim_multi.virus_particles),
            "max_infected": (
                max(sim_multi.history["infected_count"])
                if sim_multi.history["infected_count"]
                else 0
            ),
            "final_evasion": (
                sim_multi.history["virus_evasion"][-1]
                if sim_multi.history["virus_evasion"]
                else 0
            ),
        }
        sim_multi.plot_results()

    print("\n--- Results Summary ---")
    for level, data in results_summary.items():
        print(
            f"Aggressiveness {level:.2f}: Ended Step {data['final_step']:>3}, "
            f"Final Cancer={data['final_cancer']:>4}, Final Virus={data['final_virus']:>5}, "
            f"Max Infected={data['max_infected']:>4}, Final Evasion={data['final_evasion']:.3f}"
        )
