from collections import *
from math import *

num_percepts = 3
percept_colors = [color(255, 0, 0, 50),
                  color(0, 255, 0, 50),
                  color(0, 0, 255, 50),
                  color(255, 255, 0, 50),
                  color(0, 255, 255, 50)]

class Vec:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, v):
        return Vec(self.x + v.x, self.y + v.y)

    def __radd__(self, s):
        return Vec(self.x + s, self.y + s)

    def __sub__(self, v):
        return Vec(self.x - v.x, self.y - v.y)

    def __rsub__(self, s):
        return Vec(self.x - s, self.y - s)

    def __mul__(self, s):
        return Vec(self.x * s, self.y * s)

    def mag(self, min_val=0):
        return max(min_val, sqrt(self.x * self.x + self.y * self.y))

    def norm(self):
        return self * (1 / self.mag(0.0001))

class Node:
    def __init__(self):
        self.percept_visits = [0] * num_percepts
        self.edges = defaultdict(list)
        
        # for visualization
        self.pos = Vec(random(width), random(height))
        self.vel = Vec(0, 0)

    def update(self):
        self.vel = self.vel + (Vec(width / 2, height / 2) - self.pos) * 0.001
        
        for p in range(num_percepts):
            for node, _ in self.edges[p]:
                delta = node.pos - self.pos
                k = 0.001 * (delta.mag(1) - 20)
                force = delta.norm() * k
                self.vel = self.vel + force
                node.vel = node.vel - force
        
        for node in psm:
            delta = node.pos - self.pos
            k = -200  / (delta.mag(1) ** 2)
            force = delta.norm() * k
            self.vel = self.vel + force
            node.vel = node.vel - force

        self.vel = self.vel * 0.8
        self.pos = self.pos + self.vel

        
    def dominant_percept(self):
        return sorted(enumerate(self.percept_visits), key=lambda x: x[1])[-1][0]
    
    def visits(self):
        return sum(self.percept_visits)

    def draw(self):
        for p in range(num_percepts):
            c = percept_colors[p]
            stroke(c)
            for node, prob in self.edges[p]:
                strokeWeight(prob * 10)
                line(self.pos.x, self.pos.y, node.pos.x, node.pos.y)
        
        noFill()
        if self in active_states:
            strokeWeight(5)
        else:
            strokeWeight(1)
        
        stroke(0)
        ellipse(self.pos.x, self.pos.y, 20, 20)
        
        fill(0);
        text(str(self.dominant_percept()), self.pos.x - 2, self.pos.y + 5)

psm = []
active_states = []
percept_history = []
history_states = [] # [[(start_state, end_state, percept)]]
actual_histories = [] # [[percept]]

def normalize(dist):
    total = sum(dist)
    for i, p in enumerate(dist):
        dist[i] = p / total

def normalize_edges(edges):
    for i in range(len(edges)):
        s, p = edges[i]
        edges[i] = (s, max(0.001, p))
    total_p = sum([p for _, p in edges])
    for i in range(len(edges)):
        s, p = edges[i]
        edges[i] = (s, p / total_p)
        
        
def activation(x, a, b):
    return atan(x / a - b) / pi + 1/2

def sample(distribution):
    rv = random(1)

    cum_p = 0
    for node, p in sorted(distribution, key=lambda x: x[1], reverse=True):
        cum_p += p
        if rv < cum_p:
            return node
    raise Exception("dist doesn't sum to 1: {}".format(str(dist)))

def backpropagate(node, history_states):
    dom_percept = node.dominant_percept()
    actual_percept = percept_history[-1]
    bump = 1 if dom_percept == actual_percept else -0.1
    i = 1
    for start_state, end_state, percept in reversed(history_states):
        edges = start_state.edges[percept]
        for index, e in enumerate(edges):
            next_state, p = e
            if next_state == end_state:
                edges[index] = (next_state, p + bump / (i ** 2))
                break
        normalize_edges(edges)
        i += 1

def transition(node, p, actual_history, history_states):
    actual_history.append(node.dominant_percept())
    
    node.percept_visits[p] += 1
    backpropagate(node, history_states)
    edges = node.edges[p]
    
    if edges == []:
        random_node = psm[int(random(len(psm)))]
        edges.append((random_node, 1))
    next_node = sample(edges)

    confidence = activation(node.visits(), num_percepts, 5)
    mean = node.visits() / num_percepts
    sd = 0
    for p_v in node.percept_visits:
        sd += (p_v - mean) **2
    sd = sqrt(sd / num_percepts)
    
    rv = random(1)
    pvalue = sd / max(node.percept_visits)
    
    if rv * confidence > pvalue:
        if random(1) > activation(len(edges), 1, - 1) and len(edges) < len(psm):
            choices = [
                n for n in psm if all(e != n for e, _ in edges)
            ]
            next_node = choices[int(random(len(choices)))]
            edges.append((next_node, 0.5))
        else:
            next_node = Node()
            psm.append(next_node)
            edges.append((next_node, 0.5))
        
        normalize_edges(edges)
    return next_node


def setup():
    size(500, 500)
    psm.append(Node())
    active_states.append(psm[0])
    actual_histories.append([])
    history_states.append([])

def transition_all(p):
    global active_states
    percept_history.append(p)
    next_states = []
    for i, s in enumerate(active_states):
        next_state = transition(s, p, actual_histories[i], history_states[i])
        history_states[i].append((s, next_state, p))
        next_states.append(next_state)
    active_states = next_states
    
def update():
    t = 10
    if frameCount % t == 0:
        transition_all(int(frameCount / t) % num_percepts)
    
    for node in psm:
        node.update()


def draw():
    background(255)
    
    update()
    for node in psm:
        node.draw()
    
    menu()
    
def mousePressed():
    if mouseY < 50:
        percept = int(mouseX / (width / num_percepts))
        transition(percept)
        
def menu():
    strokeWeight(1)
    menu_height = 50
    button_size = width / num_percepts
    for i in range(num_percepts):
        fill(10,50,200);
        stroke(0) 
        rect(i * button_size, 0, button_size, menu_height)
        fill(255)
        noStroke()
        text(str(i), (i + 0.5) * button_size, menu_height * 0.5)
    
    fill(0)
    text(str(percept_history[-30:]), 10, menu_height + 25)
    hit_rate = sum(float(len([ p1 for p1, p2 in zip(percept_history, hist) if p1 == p2 ])) / max(1, len(percept_history)) for hist in actual_histories) / len(actual_histories)
    text(str(hit_rate), 10, menu_height + 50)
    
    for i, hist in enumerate(actual_histories):
        text(str(hist[-30:]), 10, menu_height + 75 + 25 * i)
    
    
        
    
    
    
        
        
