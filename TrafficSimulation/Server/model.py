from mesa import Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from agent import *
import json

class RandomModel(Model):
    """ 
    Creates a new model with random agents.
    Args:
        N: Number of agents in the simulation
        height, width: The size of the grid to model
    """
    def __init__(self, N):

        dataDictionary = json.load(open("mapDictionary.txt"))

        with open('base.txt') as baseFile:
            lines = baseFile.readlines()
            self.width = len(lines[0]) - 1
            self.height = len(lines)

            self.grid = MultiGrid(self.width, self.height,torus = False) 
            self.schedule = RandomActivation(self)

            for r, row in enumerate(lines):
                for c, col in enumerate(row):
                    if col in ["v", "^", ">", "<"]:
                        agent = Road_Agent(f"r{r*self.width+c}", self, dataDictionary[col])
                        self.grid.place_agent(agent, (c, self.height - r - 1))
                    elif col in ["S", "s"]:
                        agent = Traffic_Light_Agent(f"tl{r*self.width+c}", self, False if col == "S" else True, int(dataDictionary[col]))
                        self.grid.place_agent(agent, (c, self.height - r - 1))
                        self.schedule.add(agent)
                        # Additionally, add a road agent with same direction as road before traffic light

                    elif col == "#":
                        agent = Obstacle_Agent(f"ob{r*self.width+c}", self)
                        self.grid.place_agent(agent, (c, self.height - r - 1))
                    elif col == "D":
                        agent = Destination_Agent(f"d{r*self.width+c}", self)
                        self.grid.place_agent(agent, (c, self.height - r - 1))

        # Generate a graph of the streets
        self.graph = {}    # Generate graph dictionary
        for agents, x, y in self.grid.coord_iter():   # Iterate through all agents
            for agent in agents:
                if isinstance(agent, Road_Agent) or isinstance(agent, Traffic_Light_Agent):
                    # Check neighbors depending on the direction of the road
                    print(f"Road: {agent.unique_id} Direction: {agent.direction}")
                    
                    # Get the neighbors by their coordinates
                    n_ul = self.grid.get_cell_list_contents(agent.pos[0]-1, agent.pos[1]+1)
                    n_up = self.grid.get_cell_list_contents(agent.pos[0], agent.pos[1]+1)
                    n_ur = self.grid.get_cell_list_contents(agent.pos[0]+1, agent.pos[1]+1)
                    n_right = self.grid.get_cell_list_contents(agent.pos[0]+1, agent.pos[1])
                    n_dl = self.grid.get_cell_list_contents(agent.pos[0]-1, agent.pos[1]-1)
                    n_dr = self.grid.get_cell_list_contents(agent.pos[0]+1, agent.pos[1]-1)
                    n_down = self.grid.get_cell_list_contents(agent.pos[0], agent.pos[1]-1)
                    n_left = self.grid.get_cell_list_contents(agent.pos[0]-1, agent.pos[1])

                    # Check if coordinate contains a road or a traffic light, and generate their neighbors

                    if isinstance(agent, Road_Agent):
                        if(agent.direction == "Up"):
                            neighbors = [n_left, n_ul, n_up, n_ur, n_right]
                        elif(agent.direction == "Right"):
                            neighbors = [n_up, n_ur, n_right, n_dr, n_down]
                        elif(agent.direction == "Down"):
                            neighbors = [n_right, n_dr, n_down, n_dl, n_left]
                        elif(agent.direction == "Left"):
                            neighbors = [n_down, n_dl, n_left, n_ul, n_up]
                    elif isinstance(agent, Traffic_Light_Agent):
                        if n_down.direction == "Up":
                            neighbors = [n_left, n_ul, n_up, n_ur, n_right]
                        elif n_left.direction == "Right":
                            neighbors = [n_up, n_ur, n_right, n_dr, n_down]
                        elif n_up.direction == "Down":
                            neighbors = [n_right, n_dr, n_down, n_dl, n_left]
                        elif n_right.direction == "Left":
                            neighbors = [n_down, n_dl, n_left, n_ul, n_up]

                    # Filter out neighbors that are not roads, or if they are roads pointing towards the current road

                    # Check that neighbors are roads, and discard the ones that are not roads, discard roads pointing to this one
                    for neighbor in neighbors:
                        if isinstance(neighbor, Road_Agent):
                            # Filter invalid directions
                            if (neighbor == n_up and agent.direction == "Down") or (neighbor == n_down and agent.direction == "Up") or (neighbor == n_left and agent.direction == "Right") or (neighbor == n_right and agent.direction == "Left"):
                                neighbors.remove(neighbor)
                            elif (neighbor == n_ul and (agent.direction == "Down" or agent.direction == "Right")) or (neighbor == n_ur and (agent.direction == "Down" or agent.direction == "Left")) or (neighbor == n_dl and (agent.direction == "Up" or agent.direction == "Right")) or (neighbor == n_dr and (agent.direction == "Up" or agent.direction == "Left")):
                                neighbors.remove(neighbor)
                        else:
                            neighbors.remove(neighbor)

                    # Add the current agent to the dictionary with its id as the key and its neighbors as the value
                    self.graph[agent.unique_id] = neighbors

        print(self.graph)       

        self.num_agents = N
        self.running = True

    def step(self):
        '''Advance the model by one step.'''
        self.schedule.step()
        if self.schedule.steps % 10 == 0:
            for agents, x, y in self.grid.coord_iter():
                for agent in agents:
                    if isinstance(agent, Traffic_Light_Agent):
                        agent.state = not agent.state