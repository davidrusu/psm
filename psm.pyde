from collections import *
from math import *

num_percepts = 50
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

class MC:
    def __init__(self, states):
        self.mc = [[[random(1) for _ in range(states)] for _ in range(states)] for _ in range(num_percepts)]
        self.percept_visits = [[0] * num_percepts for _ in range(states)]
        self.nodes = [Node() for _ in range(states)]
        self.history = []
        self.state = 0
        [[self.normalize(p, s) for p in range(num_percepts)] for s in range(states)]
    
    def normalize(self, p, state):
        s = self.mc[p][state]
        total = sum(s)
        for i, p in enumerate(s):
            s[i] = p / total
                
    def positive(self, p, a, b, amount):
        self.mc[p][a][b] += amount
        self.normalize(p, a)
    
    def negative(self, p, a, b, amount):
        for i in range(len(self.mc[p][a])):
            self.mc[p][a][i] += amount 
        self.mc[p][a][b] -= amount
        self.normalize(p, a)
        
    def dominant_percept(self, a):
        return sorted(enumerate(self.percept_visits[a]), key=lambda x: x[1])[-1][0]
        
    def transition(self, percept):
        self.history.append(self.state)
        self.history = self.history[-100:]
        bump = 2
        if len(percept_history) > 1:
            if self.dominant_percept(self.state) == percept:
                for i, edge in enumerate(reversed(zip(self.history, self.history[1:]))):
                    p = percept_history[-(i + 2)]
                    a, b = edge
                    self.positive(p, a, b, bump / ((i + 1)**2))
            else:
                for i, edge in enumerate(reversed(zip(self.history, self.history[1:]))):
                    p = percept_history[-(i + 2)]
                    a, b = edge
                    self.negative(p, a, b, 0.1 * (bump / len(self.nodes)) / ((i + 1)**2))
        self.percept_visits[self.state][percept] += 1
        
        next_state = self.sample(percept, self.state)
        self.state = next_state
        
    def sample(self, percept, state):
        rv = random(1)
        cum_p = 0
        for next_state, p in sorted(enumerate(self.mc[percept][state]), key=lambda x: x[1], reverse=True):
            cum_p += p
            if rv < cum_p:
                break
        return next_state
    
    def update(self):
        for i, node in enumerate(self.nodes):
            if len(percept_history) < 1:
                continue
            node.update(self.nodes, self.mc[percept_history[-1]][i])
        
        for i in range(len(self.nodes)):
            a = self.nodes[i]
            for j in range(i + 1, len(self.nodes)):
                b = self.nodes[j]
                delta = b.pos - a.vel
                force = delta.norm() * (1000 / (delta.mag() ** 2))
                a.vel = a.vel - force
                b.vel = b.vel + force
                
    
    def draw(self):
        stroke(0, 0, 0, 50)
        for i, n1 in enumerate(self.nodes):
            for j, n2 in enumerate(self.nodes):
                avg_p = sum(self.mc[p][i][j] for p in range(num_percepts)) / num_percepts
                p = self.mc[self.dominant_percept(i)][i][j]
                if p < 0.1:
                    continue
                strokeWeight(p * 10)
                line(n1.pos.x, n1.pos.y, n2.pos.x, n2.pos.y)
        
        for i, node in enumerate(self.nodes):
            node.draw(i == self.state, self.dominant_percept(i))
    
class Node:
    def __init__(self):
        self.pos = Vec(random(width), random(height))
        self.vel = Vec(0, 0)

    def update(self, edges, ps):
        self.vel = self.vel + (Vec(width / 2, height / 2) - self.pos) * 0.001
        for p, node in zip(ps, edges):
            if p < 2.0 / num_percepts:
                continue 
            delta = node.pos - self.pos
            k = 0
            if p > 2.0 / num_percepts: #((len(ps) - 1) / len(ps)):
                k = 0.1 * (delta.mag(1) - 100)
            else:
                k = -100.0 / (delta.mag(1)**2)
            force = delta.norm() * k
            self.vel = self.vel + force
            node.vel = node.vel - force

        self.vel = self.vel * 0.1
        self.pos = self.pos + self.vel

    def draw(self, current_state, dom_percept):
        fill(255)
        if current_state:
            strokeWeight(5)
        else:
            strokeWeight(1)
        
        stroke(0)
        ellipse(self.pos.x, self.pos.y, 20, 20)
        
        fill(0);
        #text(str(dom_percept), self.pos.x - 2, self.pos.y + 5)

mc = None
active_states = []
percept_history = []
history_states = [] # [[(start_state, end_state, percept)]]
actual_history = [] # [percept]
percept_count = 0

def setup():
    global mc
    size(500, 500)
    mc = MC(int(num_percepts * 1.5))
    history_states.append([])

def transition(p):
    global percept_history, actual_history, percept_count
    percept_count += 1
    percept_history.append(p)
    actual_history.append(mc.dominant_percept(mc.state))
    percept_history = percept_history[-100:]
    actual_history = actual_history[-100:]
    mc.transition(p)
    
def update():
    t = 1 #int(10 * (millis() / 20000.0) * (sin(millis() / 10000.0) + 1)) + 1
    pattern = list(range(num_percepts))
    if frameCount % t == 0:
        for i in range(11):
            p = percept_count % num_percepts
            transition(p)
    if keyPressed:
        mc.update()


def draw():
    background(255)
    
    update()
    if keyPressed:
        mc.draw()
    
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
    recent_history = percept_history[-100:]
    hit_rate = float(len([ p1 for p1, p2 in zip(recent_history, actual_history[-len(recent_history):]) if p1 == p2 ])) / max(1, len(recent_history))
    text(str(hit_rate), 10, menu_height + 50)
    text(str(actual_history[-30:]), 10, menu_height + 75)        