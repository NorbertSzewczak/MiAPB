import bpmn_python.bpmn_diagram_rep as diagram
import bpmn_python.bpmn_diagram_layouter as layouter
import bpmn_python.bpmn_diagram_visualizer as visualizer

class footprint:
    def __init__(self, log, algorithm_name="alpha"):
        self.algorithm_name = algorithm_name
        self.log = log
        self.unique_events = self.find_unique_events()
        self.direct_succession = self.find_direct_succession()
        self.start_events = self.find_start_events()
        self.end_events = self.find_end_events()
        self.succession = self.merge_succession()
        self.parallels = self.find_parallels()
        self.node_incomes = self.count_node_incomes()
        self.node_outcomes = self.count_node_outcomes()

    def find_unique_events(self):
        return list(set(event for trace in self.log for event in trace))

    def find_direct_succession(self):
        return list(set((trace[i], trace[i+1]) for trace in self.log for i in range(len(trace) - 1)))

    def find_start_events(self):
        return list(set(trace[0] for trace in self.log))

    def find_end_events(self):
        return list(set(trace[-1] for trace in self.log))

    def merge_succession(self):
        merged = {}
        for prev, next_ in self.direct_succession:
            if prev not in merged:
                merged[prev] = []
            merged[prev].append(next_)
        return merged

    def find_parallels(self):
        return [[a, b] for a, b in self.direct_succession if (b, a) in self.direct_succession]

    def count_node_incomes(self):
        incomes = {event: 0 for event in self.unique_events}
        for key in self.succession:
            for value in self.succession[key]:
                incomes[value] += 1
        return incomes

    def count_node_outcomes(self):
        outcomes = {event: len(self.succession.get(event, [])) for event in self.unique_events}
        return outcomes

class BPMN:
    def __init__(self, log):
        self.algorithm_name = "alpha"
        self.log = log
        self.footprint = footprint(self.log, self.algorithm_name)
        self.succession = self.footprint.succession
        self.bpmn_graph = diagram.BpmnDiagramGraph()
        self.bpmn_graph.create_new_diagram_graph(diagram_name="alpha_alogrithm_bpmn")
        self.process_id = self.bpmn_graph.add_process_to_diagram()
        self.node_ancestors = {}
        self.node_successors = {}
        self.event_incomes = []
        self.event_outcomes = []
        self.flows = []

    def build_bpmn(self):
        self.add_nodes()
        self.add_start_events()
        self.add_parallels()
        self.remove_parallel_incomes_outcomes()
        self.event_incomes = self.footprint.count_node_incomes(self.succession, self.footprint.parallels)
        self.event_outcomes = self.footprint.count_node_outcomes(self.succession, self.footprint.parallels)
        self.add_gates()
        self.add_flows()
        self.add_end_events()
        self.bpmn_graph.export_xml_file(output_directory, "alpha_algorithm.bpmn")

    def add_nodes(self):
        added_nodes = []
        for event in self.footprint.unique_events:
            if event not in added_nodes:
                self.bpmn_graph.add_task_to_diagram(self.process_id, task_name=event, node_id=event)

    def add_start_events(self):
        for start_event in self.footprint.start_events:
            [start_id, _] = self.bpmn_graph.add_start_event_to_diagram(self.process_id)
            start_event_id = start_event
            self.bpmn_graph.add_sequence_flow_to_diagram(self.process_id, start_id, start_event_id)
            self.flows.append((start_id, start_event_id))

    def add_end_events(self):
        for end_event in self.footprint.end_events:
            [end_id, _] = self.bpmn_graph.add_end_event_to_diagram(self.process_id)
            self.bpmn_graph.add_sequence_flow_to_diagram(self.process_id, end_event, end_id)
            self.flows.append((end_event, end_id))

    def add_parallels(self):
        parallels = self.footprint.parallels
        event_count = {}
        for parallel in parallels:
            [parallel_start, _] = self.bpmn_graph.add_parallel_gateway_to_diagram(self.process_id)
            [parallel_end, _] = self.bpmn_graph.add_parallel_gateway_to_diagram(self.process_id)

            for event in parallel:
                if event in event_count:
                    event_count[event] += 1
                else:
                    event_count[event] = 1

                self.bpmn_graph.add_sequence_flow_to_diagram(self.process_id, parallel_start, event)
                self.flows.append((parallel_start, event))
                self.node_ancestors.setdefault(event, []).append(parallel_start)

                self.bpmn_graph.add_sequence_flow_to_diagram(self.process_id, event, parallel_end)
                self.flows.append((event, parallel_end))
                self.node_successors.setdefault(event, []).append(parallel_end)

        for event in event_count:
            if event_count[event] > 1:
                [gate_anc, _] = self.bpmn_graph.add_exclusive_gateway_to_diagram(self.process_id)
                self.node_ancestors.setdefault(event, []).append(gate_anc)
                [gate_succ, _] = self.bpmn_graph.add_exclusive_gateway_to_diagram(self.process_id)
                self.node_successors.setdefault(event, []).append(gate_succ)

                for i in range(event_count[event]):
                    self.bpmn_graph.add_sequence_flow_to_diagram(self.process_id, gate_anc,
                                                                 self.node_ancestors[event][-(i + 2)])
                    self.flows.append((gate_anc, self.node_ancestors[event][-(i + 2)]))
                    self.bpmn_graph.add_sequence_flow_to_diagram(self.process_id,
                                                                 self.node_successors[event][-(i + 2)], gate_succ)
                    self.flows.append((self.node_successors[event][-(i + 2)], gate_succ))

    def remove_parallel_incomes_outcomes(self):
        parallels = self.footprint.parallels
        for key in self.succession:
            for value in self.succession[key]:
                for parallel in parallels:
                    if value in parallel:
                        for event in parallel:
                            for event2 in parallel:
                                if len(self.node_successors[event]) < len(self.node_successors[event2]) and event in \
                                        self.succession[key]:
                                    self.succession[key].remove(event)

    def add_gates(self):
        for event in self.event_incomes:
            if self.event_incomes[event] > 1:
                [exclusive_gate_id, _] = self.bpmn_graph.add_exclusive_gateway_to_diagram(self.process_id)
                self.node_ancestors.setdefault(event, []).append(exclusive_gate_id)

        for event in self.event_outcomes:
            if self.event_outcomes[event] > 1:
                [exclusive_gate_id, _] = self.bpmn_graph.add_exclusive_gateway_to_diagram(self.process_id)
                self.node_successors.setdefault(event, []).append(exclusive_gate_id)

    def add_flows(self):
        parallels = self.footprint.parallels
        for event in self.footprint.unique_events:
            used_parallels = []
            if not self.is_in_parallel(event, parallels):
                if event in self.node_ancestors:
                    if len(self.node_ancestors[event]) > 1:
                        for index, id in enumerate(self.node_ancestors[event]):
                            if index + 1 != len(self.node_ancestors[event]):
                                self.bpmn_graph.add_sequence_flow_to_diagram(self.process_id,
                                                                             self.node_ancestors[event][index + 1],
                                                                             id)
                                self.flows.append((self.node_ancestors[event][index + 1], id))
                    if not self.is_in_parallel(event, parallels):
                        self.bpmn_graph.add_sequence_flow_to_diagram(self.process_id, self.node_ancestors[event][0],
                                                                     event)
                        self.flows.append((self.node_ancestors[event][0], event))

                if event in self.node_successors:
                    if len(self.node_successors[event]) > 1:
                        for index, id in enumerate(self.node_successors[event]):
                            if index + 1 != len(self.node_successors[event]):
                                self.bpmn_graph.add_sequence_flow_to_diagram(self.process_id, id,
                                                                             self.node_successors[event][index + 1])
                                self.flows.append((id, self.node_successors[event][index + 1]))

                    if not self.is_in_parallel(event, parallels):
                        self.bpmn_graph.add_sequence_flow_to_diagram(self.process_id, event,
                                                                     self.node_successors[event][0])
                        self.flows.append((event, self.node_successors[event][0]))

            else:
                if len(self.node_successors[event]) > len(self.node_ancestors[event]):
                    self.bpmn_graph.add_sequence_flow_to_diagram(self.process_id, self.node_successors[event][-2],
                                                                 self.node_successors[event][-1])
                    self.flows.append((self.node_successors[event][-2], self.node_successors[event][-1]))
                elif len(self.node_successors[event]) < len(self.node_ancestors[event]):
                    self.bpmn_graph.add_sequence_flow_to_diagram(self.process_id, self.node_ancestors[event][-1],
                                                                 self.node_ancestors[event][-2])
                    self.flows.append((self.node_ancestors[event][-1], self.node_ancestors[event][-2]))

            if event in self.succession:
                for value in self.succession[event]:
                    if not self.is_connected(event, value):
                        if event in self.node_successors and value in self.node_ancestors and not self.is_in_parallel(
                                event, used_parallels):
                            self.add_flow_sucessor_to_ancestor(event, value)
                        elif event in self.node_successors and value not in self.node_ancestors:
                            self.add_flow_successor_to_node(event, value)
                        elif event not in self.node_successors and value in self.node_ancestors:
                            self.add_flow_node_to_ancestor(event, value)
                        elif event not in self.node_successors and value not in self.node_ancestors:
                            self.bpmn_graph.add_sequence_flow_to_diagram(self.process_id, event, value)
                            self.flows.append((event, value))

    def add_flow_sucessor_to_ancestor(self, event, value):
        parallels = self.footprint.parallels
        target = self.node_ancestors[value][-1]
        source = self.node_successors[event][-1]
        for parallel in parallels:
            if event in parallel:
                for event2 in parallel:
                    if len(self.node_successors[event2]) > len(self.node_successors[event]):
                        source = self.node_successors[event2][-1]
            if value in parallel:
                for event2 in parallel:
                    if len(self.node_ancestors[event2]) > len(self.node_ancestors[value]):
                        target = self.node_ancestors[event2][-1]

        self.bpmn_graph.add_sequence_flow_to_diagram(self.process_id, source, target)
        self.flows.append((source, target))

    def add_flow_node_to_ancestor(self, event, value):
        parallels = self.footprint.parallels
        target = self.node_ancestors[value][-1]
        for parallel in parallels:
            if event in parallel:
                for event2 in parallel:
                    if len(self.node_ancestors[event2]) > len(self.node_ancestors[value]):
                        target = self.node_ancestors[event2][-1]

        self.bpmn_graph.add_sequence_flow_to_diagram(self.process_id, event, target)
        self.flows.append((event, target))

    def add_flow_successor_to_node(self, event, value):
        parallels = self.footprint.parallels
        source = self.node_successors[event][-1]
        for parallel in parallels:
            if event in parallel:
                for event2 in parallel:
                    if len(self.node_successors[event2]) > len(self.node_successors[event]):
                        source = self.node_successors[event2][-1]

        self.bpmn_graph.add_sequence_flow_to_diagram(self.process_id, source, value)
        self.flows.append((source, value))

    def is_connected(self, source, target):
        availables = []
        availables.append(source)
        for ava in availables:
            for tuple in self.flows:
                if tuple[0] == ava and tuple[1] not in availables:
                    availables.append(tuple[1])

        if target in availables:
            return True
        return False

    def is_in_parallel(self, event, parallels):
        for parallel in parallels:
            if event in parallel:
                return True
        return False


# Przykładowe logi do testów
log_data = [["A", "B", "C"], ["A", "C", "B"], ["A", "B", "D"]]
bpmn_model = BPMN(log_data)
bpmn_model.build_bpmn()
