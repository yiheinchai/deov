import numpy as np
import random
import matplotlib.pyplot as plt
from collections import Counter
import copy  # For deep copying virus genotypes

# --- Simulation Parameters ---
GRID_SIZE = 50        # Size of the simulation grid (e.g., 50x50)
INITIAL_CANCER_CELLS = 200
INITIAL_VIRUS_PARTICLES = 50
SIMULATION_STEPS = 300

# Cancer Cell Parameters
CANCER_REPLICATION_PROB = 0.1  # Probability a healthy cell replicates per step
INITIAL_RESISTANCE_DISTRIBUTION = {'type1': 0.8, 'type2': 0.2} # Initial receptor types
CANCER_MUTATION_RATE_RESISTANCE = 0.005 # Chance cell changes receptor type spontaneously

# Virus Parameters
VIRUS_REPLICATION_BURST_SIZE = 50  # Viruses produced per infected cell lysis
INFECTION_LATENCY_PERIOD = 5    # Steps from infection to lysis
VIRAL_INFECTION_PROB_BASE = 0.7  # Base probability of infection if tropism matches
# --- Directed Evolution Parameters ---
VIRUS_GENOTYPE_KEYS = ['tropism', 'immune_evasion']
INITIAL_VIRUS_TROPISM = 'type1' # Initial virus targets this receptor
INITIAL_VIRUS_EVASION = 0.1     # Initial immune evasion level (0 to 1)
# *** KEY: Targeted Hypermutation Rates ***
MUTATION_RATE_TROPISM = 0.05     # Higher mutation rate for the tropism gene (e.g., 5%)
MUTATION_RATE_EVASION = 0.02     # Mutation rate for immune evasion gene (e.g., 2%)
OTHER_GENE_MUTATION_RATE = 0.001 # Background mutation rate for other hypothetical genes

# Immune System Parameters (Simplified)
INITIAL_IMMUNE_CELLS = 10
IMMUNE_CELL_PATROL_RADIUS = 3
IMMUNE_KILL_PROB_INFECTED = 0.6 # Base prob to kill infected cell
IMMUNE_KILL_PROB_FREE_VIRUS = 0.3 # Base prob to clear free virus
# How much evasion reduces kill probability (e.g., KillProb = Base * (1 - evasion_level))
EVASION_EFFECTIVENESS = 0.8

# --- Agent Classes ---

class CancerCell:
    def __init__(self, id, pos, receptor_type, resistance_level=0.1):
        self.id = id
        self.pos = pos
        self.receptor_type = receptor_type
        self.resistance_level = resistance_level # General antiviral resistance
        self.is_infected = False
        self.infection_timer = 0
        self.virus_genotype_inside = None

    def attempt_replication(self, grid):
        if not self.is_infected and random.random() < CANCER_REPLICATION_PROB:
            # Find empty neighbor spots
            neighbors = self._get_neighbors(grid.shape)
            empty_neighbors = [(r, c) for r, c in neighbors if grid[r, c] is None]
            if empty_neighbors:
                new_pos = random.choice(empty_neighbors)
                # Potential spontaneous resistance mutation
                new_receptor = self.receptor_type
                if random.random() < CANCER_MUTATION_RATE_RESISTANCE:
                   new_receptor = random.choice(list(INITIAL_RESISTANCE_DISTRIBUTION.keys()))

                new_cell = CancerCell(f"C_{random.randint(10000, 99999)}", new_pos, new_receptor, self.resistance_level)
                return new_cell
        return None

    def attempt_infection(self, virus):
        # Tropism match check
        tropism_match = (virus.genotype['tropism'] == self.receptor_type)
        infection_prob = VIRAL_INFECTION_PROB_BASE if tropism_match else 0.0
        infection_prob *= (1 - self.resistance_level) # Factor in cell resistance

        if not self.is_infected and random.random() < infection_prob:
            self.is_infected = True
            self.infection_timer = INFECTION_LATENCY_PERIOD
            self.virus_genotype_inside = copy.deepcopy(virus.genotype) # Store genotype of infecting virus
            return True # Infection successful
        return False # Infection failed

    def progress_infection(self):
        if self.is_infected:
            self.infection_timer -= 1
            if self.infection_timer <= 0:
                return True # Ready to lyse
        return False # Not ready or not infected

    def lyse(self):
        """Produce new virus particles upon lysis."""
        new_viruses = []
        for _ in range(VIRUS_REPLICATION_BURST_SIZE):
            # --- Apply Directed Evolution (Mutation) ---
            new_genotype = copy.deepcopy(self.virus_genotype_inside)

            # Targeted Tropism Mutation
            if random.random() < MUTATION_RATE_TROPISM:
                # Simple random change for simulation - real biology is complex
                possible_tropisms = list(INITIAL_RESISTANCE_DISTRIBUTION.keys())
                current_tropism_index = possible_tropisms.index(new_genotype['tropism'])
                # Avoid mutating back immediately (can make more complex)
                possible_tropisms.pop(current_tropism_index)
                if possible_tropisms:
                   new_genotype['tropism'] = random.choice(possible_tropisms)

            # Targeted Immune Evasion Mutation
            if random.random() < MUTATION_RATE_EVASION:
                 # Simple random walk for evasion level
                 change = random.choice([-0.1, 0.1])
                 new_genotype['immune_evasion'] = max(0, min(1, new_genotype['immune_evasion'] + change)) # Clamp between 0 and 1

            # Background mutations (placeholder)
            # if random.random() < OTHER_GENE_MUTATION_RATE:
            #     pass # Mutate other hypothetical genes

            new_viruses.append(VirusParticle(f"V_{random.randint(10000, 99999)}", self.pos, new_genotype))
        return new_viruses

    def _get_neighbors(self, grid_shape):
        neighbors = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = self.pos[0] + dr, self.pos[1] + dc
                if 0 <= nr < grid_shape[0] and 0 <= nc < grid_shape[1]:
                    neighbors.append((nr, nc))
        return neighbors

class VirusParticle:
    def __init__(self, id, pos, genotype):
        self.id = id
        self.pos = pos
        self.genotype = genotype # e.g., {'tropism': 'type1', 'immune_evasion': 0.1}

    def move_randomly(self, grid_shape):
      # Simple random walk - can be diffusion based later
      dr, dc = random.choice([(-1,0), (1,0), (0,-1), (0,1), (0,0)])
      new_r = max(0, min(grid_shape[0]-1, self.pos[0] + dr))
      new_c = max(0, min(grid_shape[1]-1, self.pos[1] + dc))
      self.pos = (new_r, new_c)


class ImmuneCell:
    def __init__(self, id, pos):
        self.id = id
        self.pos = pos

    def patrol_and_kill(self, grid, agents):
        """Move randomly and attempt to clear targets in radius."""
        # Simple random walk
        dr, dc = random.choice([(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (-1,1), (1,-1), (1,1)])
        new_r = max(0, min(GRID_SIZE-1, self.pos[0] + dr))
        new_c = max(0, min(GRID_SIZE-1, self.pos[1] + dc))
        self.pos = (new_r, new_c)

        targets_killed = {'cancer': [], 'virus': []}

        # Find nearby agents within radius
        min_r, max_r = max(0, self.pos[0]-IMMUNE_CELL_PATROL_RADIUS), min(GRID_SIZE, self.pos[0]+IMMUNE_CELL_PATROL_RADIUS+1)
        min_c, max_c = max(0, self.pos[1]-IMMUNE_CELL_PATROL_RADIUS), min(GRID_SIZE, self.pos[1]+IMMUNE_CELL_PATROL_RADIUS+1)

        potential_targets = []
        for r in range(min_r, max_r):
            for c in range(min_c, max_c):
                agent = grid[r, c]
                if agent: # Cancer cells or viruses at this location
                    if isinstance(agent, CancerCell) and agent.is_infected:
                         potential_targets.append(agent)
                    elif isinstance(agent, list): # Location holds viruses
                         potential_targets.extend(agent) # Add all viruses at location

        # Attempt to kill targets
        for target in potential_targets:
             kill_prob = 0
             if isinstance(target, CancerCell): # Target is infected cell
                 # Immune evasion of virus inside protects the cell
                 evasion_level = target.virus_genotype_inside['immune_evasion'] if target.virus_genotype_inside else 0
                 kill_prob = IMMUNE_KILL_PROB_INFECTED * (1 - evasion_level * EVASION_EFFECTIVENESS)

             elif isinstance(target, VirusParticle): # Target is free virus
                 evasion_level = target.genotype['immune_evasion']
                 kill_prob = IMMUNE_KILL_PROB_FREE_VIRUS * (1 - evasion_level * EVASION_EFFECTIVENESS)

             if random.random() < kill_prob:
                 if isinstance(target, CancerCell):
                     targets_killed['cancer'].append(target.id)
                 elif isinstance(target, VirusParticle):
                     targets_killed['virus'].append(target.id)

        return targets_killed


# --- Simulation Class ---
class Simulation:
    def __init__(self):
        self.grid = np.full((GRID_SIZE, GRID_SIZE), None, dtype=object)
        self.cancer_cells = {}
        self.virus_particles = {}
        self.immune_cells = {}
        self.current_step = 0
        self.history = {'step': [], 'cancer_count': [], 'virus_count': [], 'immune_count': [],
                        'infected_count': [], 'cancer_types': [], 'virus_tropisms': [], 'virus_evasion': []}
        self._initialize_population()

    def _initialize_population(self):
        # Place initial cancer cells
        for i in range(INITIAL_CANCER_CELLS):
            while True:
                r, c = random.randint(0, GRID_SIZE-1), random.randint(0, GRID_SIZE-1)
                if self.grid[r, c] is None:
                    receptor = random.choices(list(INITIAL_RESISTANCE_DISTRIBUTION.keys()),
                                               weights=list(INITIAL_RESISTANCE_DISTRIBUTION.values()))[0]
                    cell = CancerCell(f"C_{i}", (r, c), receptor)
                    self.grid[r, c] = cell
                    self.cancer_cells[cell.id] = cell
                    break

        # Place initial virus particles (can be at specific locations or random)
        for i in range(INITIAL_VIRUS_PARTICLES):
             # Place near existing cancer cells for better start
             cell_keys = list(self.cancer_cells.keys())
             if cell_keys:
                 target_cell = self.cancer_cells[random.choice(cell_keys)]
                 r,c = target_cell.pos
             else: # Fallback if no cancer cells somehow
                 r, c = random.randint(0, GRID_SIZE-1), random.randint(0, GRID_SIZE-1)

             initial_genotype = {'tropism': INITIAL_VIRUS_TROPISM, 'immune_evasion': INITIAL_VIRUS_EVASION}
             virus = VirusParticle(f"V_{i}", (r,c), initial_genotype)

             # Add virus to grid location (handle multiple viruses per spot)
             if self.grid[r,c] is None:
                 self.grid[r,c] = [virus]
             elif isinstance(self.grid[r,c], list):
                 self.grid[r,c].append(virus)
             else: # Location holds a cancer cell, place virus 'nearby' conceptually
                 if isinstance(self.grid[r,c], CancerCell): # Add virus list next to cell
                    self.grid[r,c] = [self.grid[r,c], virus] # Cell and virus list coexist temp
                 else:
                     pass # Should not happen if init correctly

             self.virus_particles[virus.id] = virus


        # Place initial immune cells
        for i in range(INITIAL_IMMUNE_CELLS):
             while True:
                r, c = random.randint(0, GRID_SIZE-1), random.randint(0, GRID_SIZE-1)
                # Avoid placing directly on cancer cell initially if desired
                if self.grid[r, c] is None or isinstance(self.grid[r,c], list): # Check empty or virus list
                    immune_cell = ImmuneCell(f"I_{i}", (r,c))
                    # Don't place immune cell directly onto the grid agent slot,
                    # they patrol over it. Store separately.
                    self.immune_cells[immune_cell.id] = immune_cell
                    break


    def run_step(self):
        # --- Agent Actions (in randomized order to avoid bias) ---
        agent_ids = list(self.cancer_cells.keys()) + list(self.virus_particles.keys()) + list(self.immune_cells.keys())
        random.shuffle(agent_ids)

        newly_created_cancer = []
        lysed_cells = []
        newly_created_viruses = []
        killed_by_immune = {'cancer': set(), 'virus': set()} # Use sets for efficiency

        # 1. Immune Cell Actions
        immune_actions = {} # Store results per immune cell
        for agent_id in agent_ids:
             if agent_id in self.immune_cells:
                 immune_cell = self.immune_cells[agent_id]
                 # Pass grid and *all* agents for context
                 targets_killed_this_step = immune_cell.patrol_and_kill(self.grid, {'cancer': self.cancer_cells, 'virus': self.virus_particles})
                 killed_by_immune['cancer'].update(targets_killed_this_step['cancer'])
                 killed_by_immune['virus'].update(targets_killed_this_step['virus'])


        # 2. Cancer Cell Actions (Replication & Infection Progression)
        # Need copy as dict changes size
        cancer_cell_ids_this_step = list(self.cancer_cells.keys())
        for agent_id in cancer_cell_ids_this_step:
            if agent_id in self.cancer_cells and agent_id not in killed_by_immune['cancer']:
                cell = self.cancer_cells[agent_id]
                # Replication
                new_cell = cell.attempt_replication(self.grid)
                if new_cell:
                    newly_created_cancer.append(new_cell)

                # Infection Progression
                if cell.progress_infection():
                    lysed_cells.append(cell) # Mark for lysis after all actions

        # 3. Virus Actions (Movement & Infection Attempts)
        # Need copy as dict changes size
        virus_ids_this_step = list(self.virus_particles.keys())
        infection_attempts = {} # Store attempts: {virus_id: cell_id}

        # Virus Movement - Update positions first
        viruses_at_location = {} # Track where viruses moved to
        for agent_id in virus_ids_this_step:
             if agent_id in self.virus_particles and agent_id not in killed_by_immune['virus']:
                 virus = self.virus_particles[agent_id]
                 old_pos = virus.pos
                 virus.move_randomly(self.grid.shape)
                 new_pos = virus.pos

                 # Update tracking for new positions
                 if new_pos not in viruses_at_location:
                    viruses_at_location[new_pos] = []
                 viruses_at_location[new_pos].append(virus)

                 # Clean up old grid position if necessary (carefully)
                 if self.grid[old_pos] is not None:
                     if isinstance(self.grid[old_pos], list):
                         try:
                             # Remove virus from list at old location
                             self.grid[old_pos].remove(virus)
                             if not self.grid[old_pos]: # If list is empty remove it
                                self.grid[old_pos] = None
                         except ValueError:
                            pass # Virus might have been killed/moved already

        # Infection attempts based on *new* locations
        for location, viruses in viruses_at_location.items():
             grid_content = self.grid[location]
             target_cell = None

             if isinstance(grid_content, CancerCell):
                 target_cell = grid_content
             elif isinstance(grid_content, list) and isinstance(grid_content[0], CancerCell):
                 # Handle cell + virus list case
                 target_cell = grid_content[0]

             if target_cell and not target_cell.is_infected and target_cell.id not in killed_by_immune['cancer']:
                 # Let one virus at the location attempt infection (simplification)
                 # Could be more complex (e.g. probability increases with virus count)
                 infecting_virus = random.choice(viruses)
                 if infecting_virus.id not in killed_by_immune['virus']:
                     if target_cell.attempt_infection(infecting_virus):
                         # Infection succeeded - virus is now 'inside' cell conceptually
                         # Remove infecting virus from free particles
                         killed_by_immune['virus'].add(infecting_virus.id)


        # --- Update State ---
        # Remove killed agents
        for cell_id in killed_by_immune['cancer']:
            if cell_id in self.cancer_cells:
                cell = self.cancer_cells.pop(cell_id)
                # Clear grid - handle complex cell+virus state if needed
                if isinstance(self.grid[cell.pos], list) and self.grid[cell.pos][0] == cell:
                    self.grid[cell.pos] = None # Assume immune kills cell + contained viruses
                elif self.grid[cell.pos] == cell:
                     self.grid[cell.pos] = None


        viruses_to_remove_final = set()
        viruses_to_remove_final.update(killed_by_immune['virus'])

        # Handle lysis
        for cell in lysed_cells:
            if cell.id in self.cancer_cells and cell.id not in killed_by_immune['cancer']: # Check if killed by immune mid-step
                new_viruses = cell.lyse()
                newly_created_viruses.extend(new_viruses)
                # Remove lysed cell
                pos = cell.pos
                self.cancer_cells.pop(cell.id)
                # Clear grid - handle complex state if needed
                if isinstance(self.grid[pos], list) and self.grid[pos][0] == cell:
                    self.grid[pos] = None # Lyse removes cell
                elif self.grid[pos] == cell:
                     self.grid[pos] = None


        # Add new cancer cells
        for cell in newly_created_cancer:
            if self.grid[cell.pos] is None: # Check if spot is free
                self.grid[cell.pos] = cell
                self.cancer_cells[cell.id] = cell

        # Remove killed/infected free viruses
        viruses_at_location_after_immune = {} # Track viruses surviving immune step
        for virus_id in list(self.virus_particles.keys()): # Iterate over copy
             if virus_id not in viruses_to_remove_final:
                 virus = self.virus_particles[virus_id]
                 pos = virus.pos
                 if pos not in viruses_at_location_after_immune:
                     viruses_at_location_after_immune[pos] = []
                 viruses_at_location_after_immune[pos].append(virus)
             else:
                 self.virus_particles.pop(virus_id) # Remove from master list


        # Add newly created viruses
        for virus in newly_created_viruses:
             pos = virus.pos
             if pos not in viruses_at_location_after_immune:
                 viruses_at_location_after_immune[pos] = []
             viruses_at_location_after_immune[pos].append(virus)
             self.virus_particles[virus.id] = virus # Add to master list


        # Update the grid based on final virus positions for this step
        occupied_by_virus = set(viruses_at_location_after_immune.keys())
        occupied_by_cells = {c.pos for c in self.cancer_cells.values()}

        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                pos = (r,c)
                viruses_here = viruses_at_location_after_immune.get(pos)
                cell_here = self.grid[pos] if isinstance(self.grid[pos], CancerCell) else (self.grid[pos][0] if isinstance(self.grid[pos], list) and isinstance(self.grid[pos][0], CancerCell) else None)


                if cell_here and cell_here.pos != pos: cell_here = None # Stale ref check
                if cell_here and cell_here.id not in self.cancer_cells: cell_here = None # Cell died

                if cell_here and viruses_here:
                    self.grid[pos] = [cell_here] + viruses_here # Cell is primary, list viruses
                elif cell_here:
                    if not isinstance(self.grid[pos], CancerCell): # Correct grid if needed
                       self.grid[pos] = cell_here
                    # else: pass # Already correct
                elif viruses_here:
                    self.grid[pos] = viruses_here # Only viruses here
                else:
                    if pos in occupied_by_cells or pos in occupied_by_virus:
                        pass # Should have been handled above
                    else:
                        self.grid[pos] = None # Empty


        # Record history
        self.current_step += 1
        self.history['step'].append(self.current_step)
        self.history['cancer_count'].append(len(self.cancer_cells))
        self.history['virus_count'].append(len(self.virus_particles))
        self.history['immune_count'].append(len(self.immune_cells))
        self.history['infected_count'].append(sum(1 for c in self.cancer_cells.values() if c.is_infected))
        self.history['cancer_types'].append(Counter(c.receptor_type for c in self.cancer_cells.values()))
        self.history['virus_tropisms'].append(Counter(v.genotype['tropism'] for v in self.virus_particles.values()))
        self.history['virus_evasion'].append(np.mean([v.genotype['immune_evasion'] for v in self.virus_particles.values()]) if self.virus_particles else 0)


    def run_simulation(self):
        print(f"Starting simulation: {len(self.cancer_cells)} cells, {len(self.virus_particles)} viruses, {len(self.immune_cells)} immune cells")
        for step in range(SIMULATION_STEPS):
            self.run_step()
            if step % 20 == 0 or step == SIMULATION_STEPS - 1:
                 print(f"Step: {self.current_step}, Cancer: {len(self.cancer_cells)}, Infected: {self.history['infected_count'][-1]}, Viruses: {len(self.virus_particles)}, Immune: {len(self.immune_cells)}, Avg Evasion: {self.history['virus_evasion'][-1]:.3f}")
            if not self.cancer_cells:
                print(f"Cancer eliminated at step {self.current_step}!")
                break
            if not self.virus_particles and not any(c.is_infected for c in self.cancer_cells.values()):
                 print(f"Virus eliminated at step {self.current_step}. Cancer persists.")
                 break
        print("Simulation finished.")


    def plot_results(self):
        fig, axs = plt.subplots(3, 1, figsize=(10, 12), sharex=True)

        # Plot population dynamics
        axs[0].plot(self.history['step'], self.history['cancer_count'], label='Cancer Cells', color='red')
        axs[0].plot(self.history['step'], self.history['infected_count'], label='Infected Cells', color='orange', linestyle='--')
        axs[0].plot(self.history['step'], self.history['virus_count'], label='Virus Particles', color='blue')
        axs[0].plot(self.history['step'], self.history['immune_count'], label='Immune Cells', color='green')
        axs[0].set_ylabel("Population Count")
        axs[0].set_title("Population Dynamics")
        axs[0].legend()
        axs[0].grid(True)
        axs[0].set_yscale('log') # Often useful for large population changes
        axs[0].set_ylim(bottom=1) # Avoid log(0) issues

        # Plot Virus Genotype Frequencies (Tropism)
        tropism_types = sorted(list(INITIAL_RESISTANCE_DISTRIBUTION.keys()))
        for trop_type in tropism_types:
            counts = [step_data.get(trop_type, 0) for step_data in self.history['virus_tropisms']]
            axs[1].plot(self.history['step'], counts, label=f'Tropism {trop_type}')
        axs[1].set_ylabel("Virus Count")
        axs[1].set_title("Virus Tropism Evolution")
        axs[1].legend()
        axs[1].grid(True)

         # Plot Average Immune Evasion
        axs[2].plot(self.history['step'], self.history['virus_evasion'], label='Avg. Immune Evasion', color='purple')
        axs[2].set_xlabel("Time Steps")
        axs[2].set_ylabel("Average Evasion Level (0-1)")
        axs[2].set_title("Virus Immune Evasion Evolution")
        axs[2].legend()
        axs[2].grid(True)
        axs[2].set_ylim(0, 1)


        plt.tight_layout()
        plt.show()

    def visualize_grid(self, step_number):
        """Crude text-based visualization."""
        vis = np.full((GRID_SIZE, GRID_SIZE), '.', dtype=str)
        for r in range(GRID_SIZE):
             for c in range(GRID_SIZE):
                 agent = self.grid[r,c]
                 if isinstance(agent, CancerCell):
                     vis[r,c] = 'I' if agent.is_infected else 'C'
                 elif isinstance(agent, list):
                     if isinstance(agent[0], CancerCell):
                         vis[r,c] = 'X' # Cell + Virus
                     else:
                         vis[r,c] = 'v' # Viruses only
        # Overlay immune cells (approximate)
        for immune in self.immune_cells.values():
            r,c = immune.pos
            if vis[r,c] == '.': vis[r,c] = 'M'
            elif vis[r,c] == 'v': vis[r,c] = 'W' # Immune + Virus
            else : vis[r,c] = 'K' # Immune on/near cell

        print(f"\n--- Grid State at Step {step_number} ---")
        for row in vis:
            print(" ".join(row))
        print("Legend: . Empty, C Cancer, I Infected, v Virus(es), M Immune")
        print("        X Cell+Virus, W Immune+Virus, K Immune+Cell")
        print("-"*(GRID_SIZE*2))


# --- Run Simulation ---
sim = Simulation()
# sim.visualize_grid(0) # Show initial state
sim.run_simulation()
# sim.visualize_grid(sim.current_step) # Show final state
sim.plot_results()
