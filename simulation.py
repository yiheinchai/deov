import numpy as np
import random
import matplotlib.pyplot as plt
from collections import Counter
import copy
import math # For distance calculation if needed

# --- Simulation Parameters ---
GRID_SIZE = 40        # Reduced for faster testing, increase later
INITIAL_CANCER_CELLS = 150
INITIAL_VIRUS_PARTICLES = 60
INITIAL_IMMUNE_CELLS = 15
SIMULATION_STEPS = 300

# Cancer Cell Parameters
CANCER_REPLICATION_PROB = 0.08  # Probability a healthy cell replicates per step
INITIAL_RESISTANCE_TYPES = ['ReceptorA', 'ReceptorB', 'ReceptorC'] # Possible receptor types
INITIAL_RESISTANCE_DISTRIBUTION = {'ReceptorA': 0.6, 'ReceptorB': 0.3, 'ReceptorC': 0.1}
CANCER_MUTATION_RATE_RESISTANCE = 0.003 # Chance cell changes receptor type spontaneously
CANCER_BASE_ANTIVIRAL_RESISTANCE = 0.05 # Base resistance to infection (0 to 1)

# Virus Parameters
VIRUS_REPLICATION_BURST_SIZE = 40  # Viruses produced per infected cell lysis
INFECTION_LATENCY_PERIOD = 6    # Steps from infection to lysis
VIRAL_INFECTION_PROB_BASE = 0.8  # Base probability of infection if tropism matches

# --- Directed Evolution Parameters ---
VIRUS_GENOTYPE_KEYS = ['tropism', 'immune_evasion']
INITIAL_VIRUS_TROPISM = 'ReceptorA' # Initial virus targets this receptor
INITIAL_VIRUS_EVASION = 0.1     # Initial immune evasion level (0 to 1)
# *** KEY: Targeted Hypermutation Rates ***
MUTATION_RATE_TROPISM = 0.06     # Higher mutation rate for the tropism gene (e.g., 6%)
MUTATION_RATE_EVASION = 0.03     # Mutation rate for immune evasion gene (e.g., 3%)
MUTATION_EVASION_STEP = 0.05     # How much evasion changes per mutation
# OTHER_GENE_MUTATION_RATE = 0.001 # Background mutation rate (not implemented further here)

# Immune System Parameters
IMMUNE_CELL_PATROL_RADIUS = 2    # Moore neighborhood radius
IMMUNE_KILL_PROB_INFECTED = 0.7  # Base prob to kill infected cell
IMMUNE_KILL_PROB_FREE_VIRUS = 0.4  # Base prob to clear free virus
EVASION_EFFECTIVENESS = 0.9      # How much evasion reduces kill probability (e.g., KillProb = Base * (1 - evasion_level * EVASION_EFFECTIVENESS))
IMMUNE_RECRUITMENT_PROB = 0.05   # Probability an immune cell is recruited near lysis/high virus count

# --- Helper Functions ---
def get_moore_neighbors(pos, grid_shape, radius=1):
    """Gets coordinates of Moore neighborhood within bounds."""
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
    def __init__(self, pos, receptor_type, resistance_level=CANCER_BASE_ANTIVIRAL_RESISTANCE):
        self.id = f"C_{CancerCell._id_counter}"
        CancerCell._id_counter += 1
        self.pos = pos
        self.receptor_type = receptor_type
        self.resistance_level = resistance_level # General antiviral resistance
        self.is_infected = False
        self.infection_timer = 0
        self.virus_genotype_inside = None

    def attempt_replication(self, grid):
        """Attempt to replicate into an adjacent empty square."""
        if not self.is_infected and random.random() < CANCER_REPLICATION_PROB:
            neighbors = get_moore_neighbors(self.pos, grid.shape)
            empty_neighbors = [(r, c) for r, c in neighbors if grid[r, c] is None]
            if empty_neighbors:
                new_pos = random.choice(empty_neighbors)
                # Potential spontaneous resistance mutation
                new_receptor = self.receptor_type
                if random.random() < CANCER_MUTATION_RATE_RESISTANCE:
                   available_receptors = [r for r in INITIAL_RESISTANCE_TYPES if r != self.receptor_type]
                   if available_receptors:
                       new_receptor = random.choice(available_receptors)

                new_cell = CancerCell(new_pos, new_receptor, self.resistance_level)
                return new_cell
        return None

    def attempt_infection(self, virus):
        """Attempt to get infected by a specific virus particle."""
        if self.is_infected:
            return False # Already infected

        # Tropism match check
        tropism_match = (virus.genotype['tropism'] == self.receptor_type)
        infection_prob = VIRAL_INFECTION_PROB_BASE if tropism_match else 0.0
        infection_prob *= (1 - self.resistance_level) # Factor in cell resistance
        infection_prob = max(0, infection_prob) # Ensure prob isn't negative

        if random.random() < infection_prob:
            self.is_infected = True
            self.infection_timer = INFECTION_LATENCY_PERIOD
            # IMPORTANT: Deep copy the genotype so mutations in the cell don't affect the original free virus
            self.virus_genotype_inside = copy.deepcopy(virus.genotype)
            return True # Infection successful
        return False # Infection failed

    def progress_infection(self):
        """Decrement infection timer. Return True if ready to lyse."""
        if self.is_infected:
            self.infection_timer -= 1
            if self.infection_timer <= 0:
                return True # Ready to lyse
        return False # Not ready or not infected

    def lyse(self):
        """Produce new virus particles upon lysis, applying directed evolution."""
        if not self.is_infected or not self.virus_genotype_inside:
            return [] # Should not happen if called correctly

        new_viruses = []
        parent_genotype = self.virus_genotype_inside
        for _ in range(VIRUS_REPLICATION_BURST_SIZE):
            # Start with parent genotype
            new_genotype = copy.deepcopy(parent_genotype)

            # --- Apply Directed Evolution (Mutation) ---
            # Targeted Tropism Mutation
            if random.random() < MUTATION_RATE_TROPISM:
                possible_tropisms = [r for r in INITIAL_RESISTANCE_TYPES if r != new_genotype['tropism']]
                if possible_tropisms:
                   new_genotype['tropism'] = random.choice(possible_tropisms)

            # Targeted Immune Evasion Mutation
            if random.random() < MUTATION_RATE_EVASION:
                 change = random.choice([-MUTATION_EVASION_STEP, MUTATION_EVASION_STEP])
                 new_genotype['immune_evasion'] = max(0, min(1, new_genotype['immune_evasion'] + change)) # Clamp between 0 and 1

            # Background mutations (placeholder - could affect replication rate, etc.)
            # if random.random() < OTHER_GENE_MUTATION_RATE: pass

            new_viruses.append(VirusParticle(self.pos, new_genotype)) # New viruses appear at lysis site
        return new_viruses

class VirusParticle:
    _id_counter = 0
    def __init__(self, pos, genotype):
        self.id = f"V_{VirusParticle._id_counter}"
        VirusParticle._id_counter += 1
        self.pos = pos
        self.genotype = genotype # e.g., {'tropism': 'ReceptorA', 'immune_evasion': 0.1}

    def move_randomly(self, grid_shape):
      """Move to one of the 8 neighboring cells or stay put."""
      dr = random.randint(-1, 1)
      dc = random.randint(-1, 1)
      new_r = max(0, min(grid_shape[0]-1, self.pos[0] + dr))
      new_c = max(0, min(grid_shape[1]-1, self.pos[1] + dc))
      self.pos = (new_r, new_c)

class ImmuneCell:
    _id_counter = 0
    def __init__(self, pos):
        self.id = f"I_{ImmuneCell._id_counter}"
        ImmuneCell._id_counter += 1
        self.pos = pos

    def move_randomly(self, grid_shape):
      """Move to one of the 8 neighboring cells or stay put."""
      dr = random.randint(-1, 1)
      dc = random.randint(-1, 1)
      new_r = max(0, min(grid_shape[0]-1, self.pos[0] + dr))
      new_c = max(0, min(grid_shape[1]-1, self.pos[1] + dc))
      self.pos = (new_r, new_c)

    def patrol_and_kill(self, grid):
        """Move and attempt to clear targets in Moore neighborhood."""
        self.move_randomly(grid.shape)

        targets_killed_ids = {'cancer': [], 'virus': []}
        neighbor_coords = get_moore_neighbors(self.pos, grid.shape, radius=IMMUNE_CELL_PATROL_RADIUS)
        neighbor_coords.append(self.pos) # Check own location too

        potential_targets_at_coord = {} # {coord: [target1, target2...]}

        for r, c in neighbor_coords:
            content = grid[r, c]
            if content is not None:
                 potential_targets_at_coord[(r,c)] = []
                 if isinstance(content, CancerCell) and content.is_infected:
                     potential_targets_at_coord[(r,c)].append(content)
                 elif isinstance(content, list): # Can be [Virus...] or [Cell, Virus...]
                     for item in content:
                         if isinstance(item, CancerCell) and item.is_infected:
                              potential_targets_at_coord[(r,c)].append(item)
                         elif isinstance(item, VirusParticle):
                              potential_targets_at_coord[(r,c)].append(item)

        # Attempt to kill targets found
        for coord, targets in potential_targets_at_coord.items():
            for target in targets:
                 # Check if target hasn't already been marked for killing by another immune cell this step
                 # (Requires passing killed sets - simplified here: assumes first immune cell gets the kill)
                 kill_prob = 0
                 if isinstance(target, CancerCell): # Target is infected cell
                     evasion_level = target.virus_genotype_inside['immune_evasion'] if target.virus_genotype_inside else 0
                     kill_prob = IMMUNE_KILL_PROB_INFECTED * (1 - evasion_level * EVASION_EFFECTIVENESS)
                 elif isinstance(target, VirusParticle): # Target is free virus
                     evasion_level = target.genotype['immune_evasion']
                     kill_prob = IMMUNE_KILL_PROB_FREE_VIRUS * (1 - evasion_level * EVASION_EFFECTIVENESS)

                 kill_prob = max(0, kill_prob) # Ensure non-negative

                 if random.random() < kill_prob:
                     if isinstance(target, CancerCell):
                         targets_killed_ids['cancer'].append(target.id)
                     elif isinstance(target, VirusParticle):
                         targets_killed_ids['virus'].append(target.id)
                     # Prevent trying to kill the same agent multiple times by this immune cell
                     # A more robust implementation would handle this globally across immune cells
                     # For simplicity here, we just record the kill ID.
        return targets_killed_ids


# --- Simulation Class ---
class Simulation:
    def __init__(self):
        # Grid stores None, CancerCell object, or a list of VirusParticle objects
        # Or potentially [CancerCell, Virus1, Virus2...]
        self.grid = np.full((GRID_SIZE, GRID_SIZE), None, dtype=object)
        self.cancer_cells = {} # {id: CancerCell_object}
        self.virus_particles = {} # {id: VirusParticle_object}
        self.immune_cells = {} # {id: ImmuneCell_object}
        self.current_step = 0
        self.history = {'step': [], 'cancer_count': [], 'virus_count': [], 'immune_count': [],
                        'infected_count': [], 'cancer_types': [], 'virus_tropisms': [], 'virus_evasion': []}
        self._initialize_population()

    def _initialize_population(self):
        """Place initial agents onto the grid and into dictionaries."""
        # Place initial cancer cells
        placed_cells = 0
        while placed_cells < INITIAL_CANCER_CELLS:
            r, c = random.randint(0, GRID_SIZE-1), random.randint(0, GRID_SIZE-1)
            if self.grid[r, c] is None:
                receptor = random.choices(list(INITIAL_RESISTANCE_DISTRIBUTION.keys()),
                                           weights=list(INITIAL_RESISTANCE_DISTRIBUTION.values()))[0]
                cell = CancerCell((r, c), receptor)
                self.grid[r, c] = cell
                self.cancer_cells[cell.id] = cell
                placed_cells += 1

        # Place initial virus particles near cancer cells for faster start
        placed_viruses = 0
        if self.cancer_cells: # Check if there are cells to place near
            cell_positions = [cell.pos for cell in self.cancer_cells.values()]
            while placed_viruses < INITIAL_VIRUS_PARTICLES:
                 target_pos = random.choice(cell_positions)
                 # Place in neighborhood of target cell
                 r_offset, c_offset = random.randint(-1, 1), random.randint(-1, 1)
                 r = max(0, min(GRID_SIZE-1, target_pos[0] + r_offset))
                 c = max(0, min(GRID_SIZE-1, target_pos[1] + c_offset))

                 initial_genotype = {'tropism': INITIAL_VIRUS_TROPISM, 'immune_evasion': INITIAL_VIRUS_EVASION}
                 virus = VirusParticle((r,c), initial_genotype)

                 # Add virus to grid location (handle existing content)
                 current_content = self.grid[r,c]
                 if current_content is None:
                     self.grid[r,c] = [virus] # Start a list if empty
                 elif isinstance(current_content, CancerCell):
                     self.grid[r,c] = [current_content, virus] # Convert cell to list [cell, virus]
                 elif isinstance(current_content, list):
                     current_content.append(virus) # Add to existing list

                 self.virus_particles[virus.id] = virus
                 placed_viruses += 1
        else:
            print("Warning: No initial cancer cells to place viruses near.")


        # Place initial immune cells randomly
        placed_immune = 0
        while placed_immune < INITIAL_IMMUNE_CELLS:
            r, c = random.randint(0, GRID_SIZE-1), random.randint(0, GRID_SIZE-1)
            # Can place anywhere, they patrol
            immune_cell = ImmuneCell((r,c))
            self.immune_cells[immune_cell.id] = immune_cell
            placed_immune += 1

        print(f"Initialization: {len(self.cancer_cells)} cells, {len(self.virus_particles)} viruses, {len(self.immune_cells)} immune cells.")
        self._record_history() # Record initial state

    def _update_grid_location(self, pos, new_content):
        """Helper to update grid, ensuring lists are handled correctly."""
        self.grid[pos] = new_content

    def _cleanup_and_reconcile_grid(self):
        """Ensure grid accurately reflects agent dictionaries after all actions."""
        new_grid = np.full((GRID_SIZE, GRID_SIZE), None, dtype=object)
        # Place cancer cells
        for cell_id, cell in self.cancer_cells.items():
            r, c = cell.pos
            if new_grid[r, c] is None:
                new_grid[r, c] = cell
            else:
                 # This shouldn't happen if replication/movement logic is correct
                 print(f"Warning: Overlap detected for cell {cell_id} at {cell.pos}")


        # Place virus particles (potentially adding to lists or creating lists)
        for virus_id, virus in self.virus_particles.items():
            r, c = virus.pos
            current_content = new_grid[r, c]
            if current_content is None:
                new_grid[r, c] = [virus]
            elif isinstance(current_content, CancerCell):
                # Cell exists, create list [Cell, Virus]
                new_grid[r, c] = [current_content, virus]
            elif isinstance(current_content, list):
                # List exists (either [Virus..] or [Cell, Virus..]), append
                current_content.append(virus)
            else:
                 print(f"Warning: Unexpected grid content type {type(current_content)} at {virus.pos} for virus {virus.id}")

        self.grid = new_grid


    def run_step(self):
        """Execute one time step of the simulation."""
        if not self.cancer_cells and not self.virus_particles:
            print("Extinction event. Simulation ending early.")
            return False # Signal to stop simulation

        # --- Stage 0: Initialization for the step ---
        newly_created_cancer = []
        lysed_cells_ids = set()
        newly_created_viruses = []
        killed_by_immune_ids = {'cancer': set(), 'virus': set()} # Collect IDs killed this step
        viruses_infected_this_step = set() # Track viruses that successfully infected

        # --- Stage 1: Immune Cell Actions ---
        # Shuffle order to avoid bias
        immune_cell_ids = list(self.immune_cells.keys())
        random.shuffle(immune_cell_ids)
        for agent_id in immune_cell_ids:
            if agent_id in self.immune_cells: # Check if not removed mid-step (unlikely here)
                immune_cell = self.immune_cells[agent_id]
                # Pass grid for context
                targets_killed = immune_cell.patrol_and_kill(self.grid)
                # Use update to add multiple items from the returned list/set
                killed_by_immune_ids['cancer'].update(targets_killed['cancer'])
                killed_by_immune_ids['virus'].update(targets_killed['virus'])

        # --- Stage 2: Cancer Cell Actions ---
        cancer_cell_ids = list(self.cancer_cells.keys())
        random.shuffle(cancer_cell_ids)
        for agent_id in cancer_cell_ids:
            # Check if cell exists and wasn't killed by immune system this step
            if agent_id in self.cancer_cells and agent_id not in killed_by_immune_ids['cancer']:
                cell = self.cancer_cells[agent_id]

                # Replication attempt (only if not infected)
                if not cell.is_infected:
                    new_cell = cell.attempt_replication(self.grid)
                    if new_cell:
                        newly_created_cancer.append(new_cell) # Add to temporary list

                # Infection Progression & Lysis Check
                if cell.is_infected:
                    if cell.progress_infection():
                        lysed_cells_ids.add(agent_id) # Mark for lysis later

        # --- Stage 3: Virus Actions (Movement & Infection Attempts) ---
        virus_ids = list(self.virus_particles.keys())
        random.shuffle(virus_ids)
        virus_new_positions = {} # Store where each virus moved to {virus_id: new_pos}

        # 3a. Virus Movement
        for agent_id in virus_ids:
             # Check if virus exists and wasn't killed by immune system this step
             if agent_id in self.virus_particles and agent_id not in killed_by_immune_ids['virus']:
                 virus = self.virus_particles[agent_id]
                 virus.move_randomly(self.grid.shape)
                 virus_new_positions[agent_id] = virus.pos

        # 3b. Infection Attempts at *new* locations
        # Group viruses by their destination coordinates
        viruses_at_location = {} # {pos: [virus_id1, virus_id2...]}
        for virus_id, new_pos in virus_new_positions.items():
            if new_pos not in viruses_at_location:
                viruses_at_location[new_pos] = []
            viruses_at_location[new_pos].append(virus_id)

        # Iterate through locations where viruses landed
        for pos, resident_virus_ids in viruses_at_location.items():
            content = self.grid[pos]
            target_cell = None
            if isinstance(content, CancerCell):
                target_cell = content
            elif isinstance(content, list) and isinstance(content[0], CancerCell):
                target_cell = content[0]

            # If a potential target cell exists at this location
            if target_cell and target_cell.id in self.cancer_cells \
               and target_cell.id not in killed_by_immune_ids['cancer'] \
               and not target_cell.is_infected:
                 # Simplification: Let one random virus at location attempt infection
                 infecting_virus_id = random.choice(resident_virus_ids)
                 # Ensure this chosen virus wasn't killed by immune system
                 if infecting_virus_id in self.virus_particles and infecting_virus_id not in killed_by_immune_ids['virus']:
                     virus = self.virus_particles[infecting_virus_id]
                     if target_cell.attempt_infection(virus):
                         # Infection successful! Virus is now 'used up' (inside cell)
                         viruses_infected_this_step.add(infecting_virus_id)


        # --- Stage 4: State Updates ---
        # 4a. Remove killed agents
        for cell_id in killed_by_immune_ids['cancer']:
            if cell_id in self.cancer_cells:
                del self.cancer_cells[cell_id]
        # Combine viruses killed by immune and those that successfully infected
        all_viruses_to_remove = killed_by_immune_ids['virus'].union(viruses_infected_this_step)
        for virus_id in all_viruses_to_remove:
            if virus_id in self.virus_particles:
                 del self.virus_particles[virus_id]


        # 4b. Process Lysis - MUST happen after kills, before adding new viruses
        for cell_id in lysed_cells_ids:
             # Check if cell still exists (wasn't killed by immune system)
             if cell_id in self.cancer_cells:
                 cell = self.cancer_cells[cell_id]
                 new_viruses_from_lysis = cell.lyse()
                 newly_created_viruses.extend(new_viruses_from_lysis)
                 # Remove the lysed cell itself
                 del self.cancer_cells[cell_id]

        # 4c. Add newly replicated cancer cells
        for cell in newly_created_cancer:
            # Check grid spot again in case another cell replicated there in the same step
            if self.grid[cell.pos] is None:
                self.cancer_cells[cell.id] = cell
            # else: Replication failed due to space limitation

        # 4d. Add newly created viruses from lysis
        for virus in newly_created_viruses:
             self.virus_particles[virus.id] = virus

        # 4e. Immune Recruitment (Optional) - Add new immune cells near lysis sites
        if random.random() < IMMUNE_RECRUITMENT_PROB * len(lysed_cells_ids):
             # Find a random spot near a lysis event (simplistic)
             try:
                lysed_cell_pos = self.cancer_cells[random.choice(list(lysed_cells_ids))].pos # Get pos before deleting
                r_offset, c_offset = random.randint(-2, 2), random.randint(-2, 2)
                r = max(0, min(GRID_SIZE-1, lysed_cell_pos[0] + r_offset))
                c = max(0, min(GRID_SIZE-1, lysed_cell_pos[1] + c_offset))
                immune_cell = ImmuneCell((r,c))
                self.immune_cells[immune_cell.id] = immune_cell
             except (KeyError, IndexError):
                pass # Ignore if lysed cell was already gone or no lysis happened

        # 4f. Update Grid - Crucial step to reflect all changes
        self._cleanup_and_reconcile_grid()

        # --- Stage 5: Record History & Increment Step ---
        self.current_step += 1
        self._record_history()

        return True # Simulation step completed successfully

    def _record_history(self):
        """Record the current state of the simulation."""
        self.history['step'].append(self.current_step)
        self.history['cancer_count'].append(len(self.cancer_cells))
        self.history['virus_count'].append(len(self.virus_particles))
        self.history['immune_count'].append(len(self.immune_cells))
        self.history['infected_count'].append(sum(1 for c in self.cancer_cells.values() if c.is_infected))
        self.history['cancer_types'].append(Counter(c.receptor_type for c in self.cancer_cells.values()))
        self.history['virus_tropisms'].append(Counter(v.genotype['tropism'] for v in self.virus_particles.values()))
        self.history['virus_evasion'].append(np.mean([v.genotype['immune_evasion'] for v in self.virus_particles.values()]) if self.virus_particles else 0)

    def run_simulation(self):
        """Run the simulation for the defined number of steps."""
        print(f"--- Starting Simulation ---")
        for step in range(SIMULATION_STEPS):
            success = self.run_step()
            if not success: # Check if simulation ended early
                break

            # Print progress periodically
            if step % 25 == 0 or step == SIMULATION_STEPS - 1:
                 print(f"Step: {self.current_step:>3}/{SIMULATION_STEPS} | "
                       f"Cancer: {len(self.cancer_cells):>4} ({self.history['infected_count'][-1]:>3} inf) | "
                       f"Viruses: {len(self.virus_particles):>5} | "
                       f"Immune: {len(self.immune_cells):>3} | "
                       f"Avg Evasion: {self.history['virus_evasion'][-1]:.3f}")
                 # Optional: Display grid snapshot periodically
                 # if step % 100 == 0: self.visualize_grid(self.current_step)


            # Termination Conditions
            if not self.cancer_cells:
                print(f"\n--- Cancer Eliminated at Step {self.current_step}! ---")
                break
            if len(self.cancer_cells) > GRID_SIZE * GRID_SIZE * 0.8: # Prevent grid overflow
                print(f"\n--- Simulation stopped: Cancer overwhelmed grid at step {self.current_step}. ---")
                break
            if not self.virus_particles and not any(c.is_infected for c in self.cancer_cells.values()):
                 print(f"\n--- Virus Eliminated at Step {self.current_step}. Cancer may persist. ---")
                 # Optionally continue simulation to see if cancer regrows
                 # break

        if self.current_step == SIMULATION_STEPS and self.cancer_cells:
             print(f"\n--- Simulation Ended at Step {SIMULATION_STEPS}. Cancer persists. ---")
        elif self.current_step < SIMULATION_STEPS and self.cancer_cells:
             # Handle other stop conditions if any added
             pass

    def plot_results(self):
        """Plot the simulation results."""
        print("\n--- Plotting Results ---")
        fig, axs = plt.subplots(3, 1, figsize=(12, 15), sharex=True)
        steps = self.history['step']

        # Plot population dynamics
        axs[0].plot(steps, self.history['cancer_count'], label='Total Cancer Cells', color='red', linewidth=2)
        axs[0].plot(steps, self.history['infected_count'], label='Infected Cells', color='orange', linestyle='--', linewidth=2)
        axs[0].plot(steps, self.history['virus_count'], label='Virus Particles', color='blue', linewidth=1.5)
        axs[0].plot(steps, self.history['immune_count'], label='Immune Cells', color='green', linewidth=1.5)
        axs[0].set_ylabel("Population Count")
        axs[0].set_title("Population Dynamics")
        axs[0].legend()
        axs[0].grid(True, linestyle=':', alpha=0.7)
        # Use symlog if counts vary wildly, otherwise linear or log
        axs[0].set_yscale('symlog', linthresh=10) # Handles zero, good for large ranges
        axs[0].set_ylim(bottom=0)

        # Plot Virus Genotype Frequencies (Tropism)
        tropism_types = sorted(list(INITIAL_RESISTANCE_TYPES))
        tropism_data = {t: [] for t in tropism_types}
        for step_data in self.history['virus_tropisms']:
             total_viruses = sum(step_data.values())
             for t in tropism_types:
                 # Calculate frequency, handle division by zero
                 freq = (step_data.get(t, 0) / total_viruses) if total_viruses > 0 else 0
                 tropism_data[t].append(freq * 100) # Plot as percentage

        for trop_type in tropism_types:
            axs[1].plot(steps, tropism_data[trop_type], label=f'Tropism {trop_type}')
        axs[1].set_ylabel("Virus Tropism Frequency (%)")
        axs[1].set_title("Virus Tropism Evolution (Frequency)")
        axs[1].legend()
        axs[1].grid(True, linestyle=':', alpha=0.7)
        axs[1].set_ylim(0, 100)


        # Plot Average Immune Evasion
        axs[2].plot(steps, self.history['virus_evasion'], label='Avg. Immune Evasion', color='purple', linewidth=2)
        axs[2].set_xlabel("Time Steps")
        axs[2].set_ylabel("Average Evasion Level (0-1)")
        axs[2].set_title("Virus Immune Evasion Evolution")
        axs[2].legend()
        axs[2].grid(True, linestyle=':', alpha=0.7)
        axs[2].set_ylim(0, 1)

        plt.tight_layout()
        plt.show()

    def visualize_grid(self, step_number):
        """Crude text-based visualization of the grid state."""
        vis = np.full((GRID_SIZE, GRID_SIZE), '.', dtype=str)
        immune_pos = {i.pos for i in self.immune_cells.values()}

        for r in range(GRID_SIZE):
             for c in range(GRID_SIZE):
                 content = self.grid[r,c]
                 immune_here = (r,c) in immune_pos

                 char = '.'
                 if isinstance(content, CancerCell):
                     char = 'I' if content.is_infected else 'C'
                 elif isinstance(content, list):
                     has_cell = isinstance(content[0], CancerCell)
                     has_virus = any(isinstance(item, VirusParticle) for item in content)

                     if has_cell and has_virus:
                         char = 'X' # Infected Cell + Viruses (likely)
                     elif has_cell: # Should not happen if grid cleaned correctly, but handle
                         char = 'I' if content[0].is_infected else 'C'
                     elif has_virus:
                         char = 'v' # Only viruses
                     else: # Empty list? Cleanup error?
                         char = '?'

                 if immune_here:
                     if char == '.': char = 'M'
                     elif char == 'v': char = 'W' # Immune fighting viruses
                     else: char = 'K' # Immune fighting cell/infected cell
                 vis[r,c] = char

        print(f"\n--- Grid State at Step {step_number} ---")
        # Print column headers
        print("   " + "".join([f"{i:<2}" for i in range(GRID_SIZE)]))
        print("  +" + "--"*GRID_SIZE + "+")
        for i, row in enumerate(vis):
            print(f"{i:<2}|" + " ".join(row) + " |")
        print("  +" + "--"*GRID_SIZE + "+")
        print("Legend: . Empty, C Cancer, I Infected, v Virus(es), M Immune")
        print("        X Cell+Virus, W Immune+Virus, K Immune+Cell")
        print("-"*(GRID_SIZE*2 + 4))


# --- Run Simulation ---
if __name__ == "__main__":
    # Set random seeds for reproducibility if needed
    # random.seed(42)
    # np.random.seed(42)

    sim = Simulation()
    # sim.visualize_grid(0) # Show initial state
    sim.run_simulation()
    # sim.visualize_grid(sim.current_step) # Show final state (or last step if stopped early)
    sim.plot_results()
