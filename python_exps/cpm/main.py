from dataclasses import dataclass, field
from collections import deque


# ---------- Data ----------

@dataclass
class Activity:
    name: str
    duration: int
    predecessors: list[str] = field(default_factory=list)

@dataclass
class Event:
    id: int
    incoming: list = field(default_factory=list)
    outgoing: list = field(default_factory=list)


@dataclass
class Arrow:
    start: Event
    end: Event
    activity: Activity

#if activity is none, it is dummy


# ---------- Topological Sort ----------

def topological_sort(activities):
    activity_map = {a.name: a for a in activities}

    indegree = {a.name: len(a.predecessors) for a in activities}
    successors = {a.name: [] for a in activities}

    for a in activities:
        for pred in a.predecessors:
            successors[pred].append(a.name)

    queue = deque(
        activity_map[name]
        for name, deg in indegree.items()
        if deg == 0
    )

    order = []

    while queue:
        act = queue.popleft()
        order.append(act)

        for nxt in successors[act.name]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(activity_map[nxt])

    if len(order) != len(activities):
        raise ValueError("Cycle detected.")

    return order
    
def load_activities(filename):
    activities = []

    with open(filename) as f:
        for line in f:
            name, duration, preds = line.strip().split(":")

            predecessors = (
                [p.strip() for p in preds.split(",") if p.strip()]
                if preds else []
            )

            activities.append(
                Activity(name, int(duration), predecessors)
            )

    return activities

loaded = load_activities("example2.txt")

print("Activities:")
for a in loaded:
    print(a)

#super basic dummy unoptimized diagram on all
ordered = topological_sort(loaded)

start = Event(0)

events = [start]
arrows = []

next_event = 1

def new_event():
    global next_event
    event = Event(next_event)
    next_event += 1
    events.append(event)
    return event

def connect_arrow(start_event,end_event,activity):
    arrow = Arrow(
        start=start_event,
        end=end_event,
        activity=activity
    )
    arrows.append(arrow)
    start_event.outgoing.append(arrow)
    end_event.incoming.append(arrow)

for act in ordered:
    if len(act.predecessors) == 0:
        start_event = start
        end_event = new_event()
        connect_arrow(start_event,end_event,act)
        #print('starting', act)
    else:
        end_event = new_event()
        #print('for activity with precess', act)
        for prev_act in act.predecessors:
            #find end of previous act and dummy it here
            start_event = None
            for i in arrows:
                if i.activity:
                    if i.activity.name == prev_act:
                        start_event = i.end
                        break
            #print('connecting to', prev_act)
            connect_arrow(start_event,end_event,None)
        #actual activity
        #print('creating activity for', act.name)
        start_event = end_event
        end_event = new_event()
        connect_arrow(start_event,end_event,act)

#Connect to end
end = Event(-1)
starts_array = []
for a in arrows:
    starts_array.append(a.start.id)
#print(starts_array)
ends = []
for a in arrows:
    if not (a.end.id in starts_array):
        ends.append(a.end)
for i in ends:
    connect_arrow(i,end,None)

print("\nAOA dummy Network:(intermediate form, dont show)")
print(len(arrows))
for a in arrows:
    if not a.activity:
        print(f"{a.start.id} --Dummy--> {a.end.id}")
    else:
        print(
            f"{a.start.id} --{a.activity.name}({a.activity.duration})--> {a.end.id}"
        )
print()

#dummy collapse now
#strategy 1: same preceed collapse
#makes: makes later to 1st one, collapsing dummies
#for i in events:
def preceeded_by(event):
    #one hop only: the activity(ies) feeding directly into this event.
    #if an incoming arrow is a dummy, look exactly one step further back
    #through it (not recursively beyond that) to find the real activity.
    result = set()
    for arr in event.incoming:
        if arr.activity:
            result.add(arr.activity.name)
        else:
            for inner in arr.start.incoming:
                if inner.activity:
                    result.add(inner.activity.name)
    return result

print('test_1', preceeded_by(end))
#traverse left to right, need e1,e2,arrow between them
to_remove = []
for a in arrows:
    if not a.activity:#dummy this is what we want
        if preceeded_by(a.start)==preceeded_by(a.end):
            to_remove.append(a)
for a in to_remove:
    arrows.remove(a)
    a.start.outgoing.remove(a)
    a.end.incoming.remove(a)

    # fully merge a.end into a.start
    for i in a.end.outgoing:
        i.start = a.start
    a.start.outgoing.extend(a.end.outgoing)

    for i in a.end.incoming:          # <-- this was missing
        i.end = a.start
    a.start.incoming.extend(a.end.incoming)

    a.end.outgoing = []               # <-- clear stale refs
    a.end.incoming = []

#strategy2: followed by
def followed_by(event):
    #one hop only: the activity(ies) fed directly by this event.
    #if an outgoing arrow is a dummy, look exactly one step further forward
    #through it (not recursively beyond that) to find the real activity.
    result = set()
    for arr in event.outgoing:
        if arr.activity:
            result.add(arr.activity.name)
        else:
            for inner in arr.end.outgoing:
                if inner.activity:
                    result.add(inner.activity.name)
    return result
    
print("test_2", followed_by(start))
#traverse left to right, need e1,e2,arrow between them
to_remove = []
for a in arrows:
    if not a.activity:#dummy this is what we want
        if followed_by(a.start)==followed_by(a.end):
            to_remove.append(a)
for a in to_remove:
    arrows.remove(a)
    a.start.outgoing.remove(a)
    a.end.incoming.remove(a)

    # fully merge a.end into a.start
    for i in a.end.outgoing:
        i.start = a.start
    a.start.outgoing.extend(a.end.outgoing)

    for i in a.end.incoming:          # <-- this was missing
        i.end = a.start
    a.start.incoming.extend(a.end.incoming)

    a.end.outgoing = []               # <-- clear stale refs
    a.end.incoming = []

print("\nAOA dummy Network:(Final)")
print(len(arrows))
for a in arrows:
    if not a.activity:
        print(f"{a.start.id} --Dummy--> {a.end.id}")
    else:
        print(
            f"{a.start.id} --{a.activity.name}({a.activity.duration})--> {a.end.id}"
        )


###

###


def export_aoa_html(arrows, filename="aoa_network.html"):
    dot = []
    dot.append("digraph AOA {")
    dot.append("rankdir=LR;")
    dot.append('node [shape=circle, fontsize=12, width=0.4, fixedsize=true];')
    dot.append('edge [fontsize=11];')

    # Collect nodes
    nodes = set()
    for a in arrows:
        nodes.add(a.start.id)
        nodes.add(a.end.id)

    for n in sorted(nodes):
        dot.append(f'{n} [label="{n}"];')

    # Add edges
    for a in arrows:
        if a.activity:
            label = f"{a.activity.name} ({a.activity.duration})"
            dot.append(
                f'{a.start.id} -> {a.end.id} [label="{label}", penwidth=2];'
            )
        else:
            dot.append(
                f'{a.start.id} -> {a.end.id} [label="Dummy", '
                'style=dashed, color=red];'
            )

    dot.append("}")

    dot_source = "\n".join(dot)

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>AOA Network</title>

<script src="https://cdn.jsdelivr.net/npm/viz.js@2.1.2/viz.js"></script>
<script src="https://cdn.jsdelivr.net/npm/viz.js@2.1.2/full.render.js"></script>

<style>
body {{
    font-family: Arial, sans-serif;
    margin: 20px;
}}

#graph {{
    border:1px solid #ccc;
    padding:20px;
    overflow:auto;
}}

svg {{
    width:100%;
    height:auto;
}}
</style>
</head>

<body>

<h2>AOA Network</h2>

<div id="graph"></div>

<script>
const dot = `{dot_source}`;

new Viz()
.renderSVGElement(dot)
.then(function(svg){{
    document.getElementById("graph").appendChild(svg);
}})
.catch(function(err){{
    document.getElementById("graph").innerHTML =
        "<pre>"+err+"</pre>";
}});
</script>

</body>
</html>
"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)

    print("Generated", filename)
    
export_aoa_html(arrows)
