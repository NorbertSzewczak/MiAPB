import bpmn_python.bpmn_diagram_rep as diagram
import bpmn_python.bpmn_diagram_layouter as layouter
import bpmn_python.bpmn_diagram_visualizer as visualizer
from config import log_list
output_directory = "./output/"
class footprint:
    def __init__(self, log, algorithm_name):
        self.algorithm_name = algorithm_name
        self.log = log
        self.unique_events = self.find_unique_events()
        self.direct_sucession = self.find_direct_sucession()
        self.start_events = self.find_start_events()
        self.end_events = self.find_end_events()
        self.succession = self.merge_sucessions()
        self.parallels = self.find_parallels()
        self.node_incomes = self.count_node_incomes(self.succession, self.parallels)
        self.node_outcomes = self.count_node_outcomes(self.succession, self.parallels)

    def find_unique_events(self):
        unique = []
        for trace in self.log:
            for event in trace:
                if event not in unique:
                    unique.append(event)
        return unique

    def find_direct_sucession(self):
        # ->
        temporal_dependencies = []
        for trace in self.log:
            for index, event in enumerate(trace):
                if index != len(trace) - 1:
                    if (event, trace[index + 1]) not in temporal_dependencies:
                        temporal_dependencies.append((event, trace[index + 1]))
        return temporal_dependencies


    def find_parallels(self):
        # ||
        parallels = []
        two_loops = self.find_two_loops()
        for event in self.unique_events:
            for event2 in self.unique_events:
                if (event, event2) in self.direct_sucession and (event2, event) in self.direct_sucession and [event, event2] not in parallels and [event2, event] not in parallels and event != event2:
                    parallels.append([event, event2])

        if self.algorithm_name == "alpha":
            return parallels

        for two_loop in two_loops:
            for parallel in parallels:
                for event in parallel:
                    for event2 in parallel:
                        if event in two_loop and event2 in two_loop:
                            if [event, event2] in parallels:
                                parallels.remove([event, event2])
                            if [event2, event] in parallels:
                                parallels.remove([event2, event])
        return parallels

    def max_parallels(self):
        parallels = self.find_parallels()
        for parallel in parallels:
            for parallel2 in parallels:
                if self.common_event(parallel, parallel2):
                    parallel.extend(parallel2)
                    parallels.remove(parallel2)

        for i in range(len(parallels)):
            parallels[i] = self.unique_list(parallels[i])
        return parallels

    def common_event(self, list1, list2):
        result = False

        for x in list1:
            for y in list2:
                if x == y:
                    result = True
                    return (result, x)
        return result

    def unique_list(self, list1):
        unique_list = []
        for x in list1:
            if x not in unique_list:
                unique_list.append(x)
        return unique_list


    def find_independences(self):
        # #
        independences = []
        for event in self.unique_events:
            for event2 in self.unique_events:
                if (event, event2) not in self.direct_sucession and (event2, event) not in self.direct_sucession and (event,event2) not in independences:
                    independences.append((event,event2))
        return independences

    def find_one_loops(self):
        one_loops = []
        for trace in self.log:
            for index, event in enumerate(trace):
                if index+1 != len(trace):
                    if event == trace[index+1]:
                        one_loops.append(event)
        return one_loops


    def find_two_loops(self):
        two_loops = []
        for trace in self.log:
            for index, event in enumerate(trace):
                if index+2 < len(trace):
                    if event == trace[index+2]:
                        two_loops.append([event, trace[index+1]])

        return two_loops


    def merge_sucessions(self):
        merged = {}
        i = 0
        used = []
        for dep in self.direct_sucession:
            wanted = dep[0]
            if wanted in used:
                continue
            for it in self.direct_sucession:
                if it[0] == wanted:
                    merged.setdefault(wanted,[])
                    merged[wanted].append(it[1])
            used.append(wanted)
            i += 1
        self.remove_parallels(self.find_parallels(), merged)
        return merged

    def remove_parallels(self, parallels, dict):
        for parallel in parallels:
            for event in parallel:
                for event2 in parallel:
                    if event != event2:
                        dict[event].remove(event2)



    def find_start_events(self):
        start_events = []
        for trace in self.log:
            if trace[0] not in start_events:
                start_events.append(trace[0])
        return start_events

    def find_end_events(self):
        end_events = []
        for trace in self.log:
            if trace[len(trace)-1] not in end_events:
                end_events.append(trace[len(trace)-1])
        return end_events

    def count_node_incomes(self, succession, parallels):
        incomes = {}
        for key in succession:
            for value in succession[key]:
                if value not in incomes.keys():
                    incomes[value] = 1
                else:
                    incomes[value] += 1
                for parallel in parallels:
                    if key in parallel and value in incomes:
                        incomes[value] -= (len(parallel)-1)


        return incomes


    def count_node_outcomes(self, succession, parallels):
        outcomes = {}
        for key in succession:
            if key in succession[key]:
                outcomes[key] = len(succession[key]) - 1
            else:
                outcomes[key] = len(succession[key])
            for parallel in parallels:
                for value in succession[key]:
                    if value in parallel:
                        outcomes[key] -= (len(parallel) - 1)
                    break

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


if __name__ == '__main__':
    bpmn_model = BPMN(log_list)
    bpmn_model.build_bpmn()
