from dataclasses import dataclass
from typing import List, Set, Dict, Tuple

@dataclass
class DecisionTable:
    id: str
    name: str
    input_expressions: List[str]
    output_expressions: List[str]
    rules: List[Dict]

@dataclass
class DMNModel:
    """Represents a DMN decision requirement diagram"""
    
    def __init__(self):
        # Store tuples of (id, name) instead of just ids
        self.decisions: Set[Tuple[str, str]] = set()  # D - decision nodes with names
        self.input_data: Set[Tuple[str, str]] = set()  # I - input data nodes with names
        self.business_knowledge: Set[Tuple[str, str]] = set()  # B - business knowledge nodes with names
        self.knowledge_sources: Set[Tuple[str, str]] = set()  # K - knowledge source nodes with names
        
        # Relations
        self.information_requirements: Set[Tuple[str, str]] = set()  # RI ⊆ D∪I×D
        self.knowledge_requirements: Set[Tuple[str, str]] = set()  # RK ⊆ D∪I×D
        self.authority_requirements: Set[Tuple[str, str]] = set()  # RA ⊆ B×D∪B
        
        # Decision Tables
        self.decision_tables: Dict[str, DecisionTable] = {}  # TD - decision tables
        
    def add_decision(self, decision_id: str, name: str) -> None:
        self.decisions.add((decision_id, name or decision_id))
        
    def add_input_data(self, input_id: str, name: str) -> None:
        self.input_data.add((input_id, name or input_id))
        
    def add_business_knowledge(self, knowledge_id: str, name: str) -> None:
        self.business_knowledge.add((knowledge_id, name or knowledge_id))
        
    def add_knowledge_source(self, source_id: str, name: str) -> None:
        self.knowledge_sources.add((source_id, name or source_id))
        
    def add_information_requirement(self, source: str, target: str) -> None:
        self.information_requirements.add((source, target))
        
    def add_knowledge_requirement(self, source: str, target: str) -> None:
        self.knowledge_requirements.add((source, target))
        
    def add_authority_requirement(self, source: str, target: str) -> None:
        self.authority_requirements.add((source, target))
        
    def add_decision_table(self, decision_id: str, table: DecisionTable) -> None:
        self.decision_tables[decision_id] = table
        
    def get_start_decisions(self) -> Set[Tuple[str, str]]:
        """Returns decisions that don't have any incoming information requirements from other decisions"""
        decision_ids = {decision_id for decision_id, _ in self.decisions}
        decisions_with_incoming = set()
        
        for src, tgt in self.information_requirements:
            if src in decision_ids and tgt in decision_ids:
                decisions_with_incoming.add(tgt)
        
        return {(decision_id, name) for decision_id, name in self.decisions 
                if decision_id not in decisions_with_incoming}
        
    def get_start_inputs(self) -> Set[Tuple[str, str]]:
        """Returns input data used by start decisions"""
        start_decisions = {decision_id for decision_id, _ in self.get_start_decisions()}
        start_inputs = set()
        
        for src, tgt in self.information_requirements:
            if tgt in start_decisions:
                for input_id, input_name in self.input_data:
                    if src == input_id:
                        start_inputs.add((input_id, input_name))
                
        return start_inputs
        
    def find_redundant_requirements(self) -> Set[Tuple[str, str]]:
        """
        Finds redundant information requirements according to Definition 4 in the paper.
        
        Returns:
            Set[Tuple[str, str]]: Set of redundant information requirements
        """
        redundant = set()
        input_ids = {input_id for input_id, _ in self.input_data}
        
        # For each input data node
        for input_id in input_ids:
            # Find all decisions that use this input
            decisions_using_input = []
            for src, tgt in self.information_requirements:
                if src == input_id:
                    decisions_using_input.append(tgt)
            
            # If more than one decision uses this input
            if len(decisions_using_input) > 1:
                # Check for succession relations
                for i, d1 in enumerate(decisions_using_input):
                    for d2 in decisions_using_input[i+1:]:
                        # If there's a succession relation between d1 and d2
                        if self.has_succession_relation(d1, d2):
                            # The connection from input to d2 is redundant
                            redundant.add((input_id, d2))
                        elif self.has_succession_relation(d2, d1):
                            # The connection from input to d1 is redundant
                            redundant.add((input_id, d1))
        
        return redundant
    
    def has_succession_relation(self, decision1: str, decision2: str) -> bool:
        """
        Checks if there's a succession relation between two decisions.
        
        Args:
            decision1 (str): ID of the first decision
            decision2 (str): ID of the second decision
            
        Returns:
            bool: True if there's a succession relation, False otherwise
        """
        # Direct connection
        if (decision1, decision2) in self.information_requirements:
            return True
        
        # Indirect connection (recursively)
        for src, tgt in self.information_requirements:
            if src == decision1 and self.has_succession_relation(tgt, decision2):
                return True
        
        return False
